"""
This module defines classes and functions for image processing, including face detection and feature extraction.

Imports:
    - cv2: OpenCV library for computer vision tasks.
    - os: Provides a way of using operating system-dependent functionality.
    - threading: Allows for the creation and management of threads.
    - datetime: Supplies classes for manipulating dates and times.
    - numpy as np: Provides support for large, multi-dimensional arrays and matrices.
    - traceback: Provides methods for extracting, formatting, and printing stack traces.
    - time: Provides time-related functions.
    - .config.settings: Custom module to access configuration settings.
    - .face_process.face_recognition.FaceRecognition: Custom module for face recognition.
    - .face_process.data_manager.DataManager: Custom module to manage face data.
    - .face_process.deepface_encapsulator.FeatureExtractor: Custom module to extract features from faces.
    - src.core.thread_safe_set.ThreadSafeSet: Custom thread-safe set implementation.
    - collections.deque: Provides a double-ended queue implementation.
    - queue.Queue, queue.Empty: Queue module provides a FIFO implementation.
"""

import cv2
import os
import threading
from datetime import datetime
import numpy as np
import traceback
import time

from .config import settings
from .face_process.face_recognition import FaceRecognition
from .face_process.data_manager import DataManager
from .face_process.deepface_encapsulator import FeatureExtractor
from src.core.thread_safe_set import ThreadSafeSet
from collections import deque
from queue import Queue, Empty

class FilePathManager:
    """
    A class to manage file paths, including adding, removing, and retrieving file paths in a thread-safe manner.
    """
    
    def __init__(self) -> None:
        """
        Initializes the FilePathManager with a deque and a thread-safe set.
        """
        self.dq = deque()
        self.set = ThreadSafeSet()
        self.lock = threading.Lock()

    def __contains__(self, file_path):
        """
        Checks if the file path is in the set.

        Args:
            file_path (str): The file path to check.

        Returns:
            bool: True if the file path is in the set, False otherwise.
        """
        return file_path in self.set

    def add(self, location, file_path):
        """
        Adds a file path to the deque and set.

        Args:
            location (str): The location of the file.
            file_path (str): The file path to add.
        """
        with self.lock:
            self.dq.append((location, file_path))
            self.set.add(file_path)

    def remove(self, location, file_path):
        """
        Removes a file path from the deque and set.

        Args:
            location (str): The location of the file.
            file_path (str): The file path to remove.
        """
        os.remove(file_path)
        with self.lock:
            self.dq.remove((location, file_path))
            self.set.remove(file_path)

    def get(self):
        """
        Retrieves the first file path from the deque.

        Returns:
            tuple: The first file path in the deque, or None if the deque is empty.
        """
        if not self.set.is_empty():
            return self.dq[0]
        return None
    
    def pop(self):
        """
        Removes and returns the last file path from the deque.

        Returns:
            tuple: The last file path in the deque.
        """
        with self.lock:
            loc, file_path = self.dq.pop()
            self.set.remove(file_path)
        return (loc, file_path)
    
    @staticmethod
    def extract_datetime_from_filename(filename):
        """
        Extracts the datetime object from a filename formatted with a trailing datetime stamp
        after the last dash '-' and before the '.jpg' extension.

        Args:
            filename (str): A string representing the filename with format 'uuid-datetime.jpg'

        Returns:
            datetime: A datetime object representing the datetime extracted from the filename
        """
        parts = filename.split('-')
        datetime_part = parts[-1]
        datetime_without_extension = datetime_part.split('.')[0]
        datetime_object = datetime.strptime(datetime_without_extension, '%Y%m%d_%H%M%S')
        return datetime_object

class ImageProcessor:
    """
    A class to process images, including face detection, feature extraction, and matching suspects to known individuals.
    """

    def __init__(self):
        """
        Initializes the ImageProcessor with the necessary components for face recognition, data management, 
        and feature extraction.
        """
        self.face_model = FaceRecognition()
        self.data_manager = DataManager(mongodb_url=settings.MONGODB_URL, index_path=settings.FAISS_PATH)
        self.feature_extractor = FeatureExtractor('Facenet')
        self.folder_path = settings.ROOT_PATH_IMAGES

        self.file_paths = FilePathManager()
        self.faces_queue = Queue()

        self.images_finder_thread = threading.Thread(target=self.find_images, daemon=True)
        self.process_images_thread = threading.Thread(target=self.process_images)
        self.process_faces_thread = threading.Thread(target=self.process_faces)

        self.conf_threshold = 0.25
        self.is_running = True

    def find_images(self):
        """
        Continuously searches for new images in the specified folder path.
        """
        os.makedirs(self.folder_path, exist_ok=True)

        while self.is_running:
            for location in os.listdir(self.folder_path):
                path = os.path.join(self.folder_path, location)
                if os.path.isdir(path):
                    for file_name in os.listdir(path):
                        file_path = os.path.join(path, file_name)
                        if os.path.isfile(file_path):
                            if not file_path in self.file_paths:
                                self.file_paths.add(location=location, file_path=file_path)
            time.sleep(5)

    def get_prediction_data(self, boxes):
        """
        Extracts prediction data from the YOLO model's output boxes.

        Args:
            boxes: The bounding boxes output from the YOLO model.

        Returns:
            list: A list of tuples containing the top-left and bottom-right coordinates of the bounding box and the confidence score.
        """
        pred_data = []
        for xyxy, conf in zip(boxes.xyxy.tolist(), boxes.conf.tolist()):
            if conf >= self.conf_threshold:
                top_left = tuple(map(int, xyxy[:2]))
                bottom_right = tuple(map(int, xyxy[2:]))
                pred_data.append((top_left, bottom_right, conf))
        return pred_data

    def process_image_path(self, location, file_path):
        """
        Processes an image from the specified file path, detects faces, and puts them in the faces queue.

        Args:
            location (str): The location of the image.
            file_path (str): The file path of the image.
        """
        with open(file_path, 'rb') as f:
            content = f.read()
            image_data = np.frombuffer(content, dtype=np.uint8)

            try:
                image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
            except Exception as e:
                print(e)
                return
                
        results = self.face_model.predict(image)
        pred_data = self.get_prediction_data(results[0].boxes)
        image_datetime = FilePathManager.extract_datetime_from_filename(file_path)
        
        for top_left, bottom_right, _ in pred_data:
            cropped_face = image[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
            self.faces_queue.put((location, image_datetime, cropped_face))

    def process_images(self):
        """
        Continuously processes images from the file paths manager.
        """
        while self.is_running:
            try:
                data = self.file_paths.get()

                if data:
                    location, file_path = data
                    self.process_image_path(location=location, file_path=file_path)
                    self.file_paths.remove(location=location, file_path=file_path)
                else:
                    time.sleep(2)
            except Exception as e:
                print(e)
                traceback.print_exc()

    def process_faces(self):
        """
        Continuously processes faces from the faces queue, extracting embeddings and storing them.
        """
        while self.is_running:
            try:
                location, image_datetime, face_frame = self.faces_queue.get(timeout=5)

                lat, lng = location.split('_')
                location = {'lat': lat, 'lng': lng}

                embedding = self.feature_extractor.get_embedding(face_frame)
                try:
                    self.data_manager.insert(embedding=embedding, location=location, time=image_datetime)
                except Exception as e:
                    print(e)
                    traceback.print_exc()
            except Empty as e:
                print(e)

    def get_embeddings(self, images):
        """
        Generates embeddings for the given images.

        Args:
            images (list): A list of images to process.

        Yields:
            numpy.ndarray: The embeddings for each image.
        """
        for image in images:
            results = self.face_model.predict(image)
            pred_data = self.get_prediction_data(results[0].boxes)
            
            for top_left, bottom_right, _ in pred_data:
                cropped_face = image[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
                embedding = self.feature_extractor.get_embedding(cropped_face)
                yield embedding

    def match_embedding_to_person(self, embedding, suspect_name):
        """
        Matches an embedding to a known person, and if found, updates the person's name in the database.

        Args:
            embedding (numpy.ndarray): The embedding to match.
            suspect_name (str): The suspect's name to update if a match is found.

        Returns:
            dict: The matched person's data, or None if no match is found.
        """
        distances, ids = self.data_manager.index.search(np.expand_dims(embedding, axis=0), 1)

        if distances.size > 0 and distances[0][0] <= FeatureExtractor.FACENET_THRESHOLD_EUCLIDEAN:
            person = self.data_manager.search_person_by_id(ids[0][0])

            if person:
                self.data_manager.insert_name(_id=person['_id'], name=suspect_name)
                return person
        return None

    def match_suspect_to_person(self, suspect_name, images):
        """
        Matches a suspect to a known person using the provided images.

        Args:
            suspect_name (str): The suspect's name.
            images (list): A list of images of the suspect.

        Returns:
            dict: The matched person's data, or None if no match is found.
        """
        for embedding in self.get_embeddings(images):
            person = self.match_embedding_to_person(embedding, suspect_name)
            if person:
                return person
        return None
    
    def get_face_from_image(self, image):
        """
        Extracts the face from the given image.

        Args:
            image (numpy.ndarray): The image to process.

        Returns:
            numpy.ndarray: The cropped face image.
        """
        results = self.face_model.predict(image)
        pred_data = self.get_prediction_data(results[0].boxes)

        for top_left, bottom_right, _ in pred_data:
            cropped_face = image[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
            return cropped_face
        
        return image

    def start(self):
        """
        Starts the image processing threads.
        """
        self.images_finder_thread.start()
        self.process_images_thread.start()
        self.process_faces_thread.start()
    
    def stop(self):
        """
        Stops the image processing and saves the FAISS index.
        """
        self.is_running = False
        self.data_manager.index.save_faiss()
