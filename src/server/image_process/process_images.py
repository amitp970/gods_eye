import cv2
import os
import threading
from datetime import datetime
import numpy as np
import traceback
import time

from .config import settings

from .face_recognition import FaceRecognition
from .face_process.data_manager import DataManager
from .face_process.deepface_encapsulator import FeatureExtractor

from src.core.thread_safe_set import ThreadSafeSet
from collections import deque
from queue import Queue, Empty

class FilePathManager:
    def __init__(self) -> None:
        self.dq = deque()
        self.set = ThreadSafeSet()
        self.lock = threading.Lock()

    def __contains__(self, file_path):
        return file_path in self.set

    def add(self, location, file_path):
        with self.lock:
            self.dq.append((location, file_path))
            self.set.add(file_path)

    def remove(self, location, file_path):
        os.remove(file_path)
        with self.lock:
            self.dq.remove((location, file_path))
            self.set.remove(file_path)


    def get(self):
        if not self.set.is_empty():
            return self.dq[0]
        
        return None
    
    def pop(self):
        with self.lock:
            loc, file_path = self.dq.pop()
            self.set.remove(file_path)

        return (loc, file_path)
    
    @staticmethod
    def extract_datetime_from_filename(filename):
        """
        Extracts the datetime object from a filename formatted with a trailing datetime stamp
        after the last dash '-' and before the '.jpg' extension.

        :param filename: A string representing the filename with format 'uuid-datetime.jpg'
        :return: A datetime object representing the datetime extracted from the filename
        """
        # Split the filename to isolate the datetime part
        parts = filename.split('-')
        datetime_part = parts[-1]  # The datetime part is after the last dash
        
        # Remove the file extension '.jpg'
        datetime_without_extension = datetime_part.split('.')[0]
        
        # Parse the datetime string into a datetime object
        datetime_object = datetime.strptime(datetime_without_extension, '%Y%m%d_%H%M%S')
        
        return datetime_object


class ImageProcessor:
    def __init__(self):
        self.face_model = FaceRecognition()
        self.data_manager = DataManager(mongodb_url=settings.MONGODB_URL, index_path=settings.FAISS_PATH)
        self.feature_extractor = FeatureExtractor('Facenet')
        self.folder_path = settings.ROOT_PATH_IMAGES

        self.file_paths = FilePathManager()
        self.faces_queue = Queue()

        self.images_finder_thread = threading.Thread(target=self.find_images, daemon=True)
        self.process_images_thread = threading.Thread(target=self.process_images)
        self.process_faces_thread = threading.Thread(target=self.process_faces)

        self.conf_threshold = 0.4

        self.is_running = True
    

    def find_images(self):
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
        """Extracts prediction data from the YOLO model's output boxes."""
        pred_data = []
        for xyxy, conf in zip(boxes.xyxy.tolist(), boxes.conf.tolist()):
            if conf >= self.conf_threshold:
                top_left = tuple(map(int, xyxy[:2]))
                bottom_right = tuple(map(int, xyxy[2:]))
                pred_data.append((top_left, bottom_right, conf))
        return pred_data

    def process_image_path(self, location, file_path):
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
                    traceback.print_exc
            except Empty as e:
                print(e)

    def get_embeddings(self, images):
        for image in images:
            results = self.face_model.predict(image)
            pred_data = self.get_prediction_data(results[0].boxes)
            
            for top_left, bottom_right, _ in pred_data:
                cropped_face = image[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
                embedding = self.feature_extractor.get_embedding(cropped_face)

                yield embedding

    def match_embedding_to_person(self, embedding, suspect_name):
        distances, ids = self.data_manager.index.search(np.expand_dims(embedding, axis=0), 1)

        if distances.size > 0 and distances[0][0] <= FeatureExtractor.FACENET_THRESHOLD_EUCLIDEAN:
            person = self.data_manager.search_person_by_id(ids[0][0])

            if person:
                self.data_manager.insert_name(_id=person['_id'], name=suspect_name)

                return person
        return None

    def match_suspect_to_person(self, suspect_name, images):
        for embedding in self.get_embeddings(images):
                
                person = self.match_embedding_to_person(embedding, suspect_name)

                if person:
                    return person
        return None
    
    def get_face_from_image(self, image):
        results = self.face_model.predict(image)
        pred_data = self.get_prediction_data(results[0].boxes)

        for top_left, bottom_right, _ in pred_data:
                cropped_face = image[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]

                return cropped_face
        
        return image




    def start(self):
        self.images_finder_thread.start()
        self.process_images_thread.start()
        self.process_faces_thread.start()
    
    def stop(self):
        self.is_running = False
        self.data_manager.index.save_faiss()