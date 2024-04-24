import cv2
import os
import threading

from .config import settings

from face_recognition import FaceRecognition
from .face_process.data_manager import DataManager
from .face_process.deepface_encapsulator import FeatureExtractor

from src.core.thread_safe_set import ThreadSafeSet
from collections import deque

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
        with self.lock:
            self.dq.remove((location, file_path))
            self.set.remove(file_path)
    
    def get(self):
        return self.dq[0]
    
    def pop(self):
        with self.lock:
            loc, file_path = self.dq.pop()
            self.set.remove(file_path)

        return (loc, file_path)

class ImageProcessor:
    def __init__(self):
        self.face_model = FaceRecognition()
        self.data_manager = DataManager(index_path=settings.FAISS_PATH, db_path=settings.DATABASE_URL)
        self.feature_extractor = FeatureExtractor('Facenet')
        self.folder_path = settings.ROOT_PATH_IMAGES

        self.file_paths = FilePathManager()

        self.images_finder_thread = threading.Thread(target=self.find_images, daemon=True)
        self.process_images_thread = threading.Thread(target=self.process_images)

        self.is_running = True

    def find_images(self):
        while self.is_running:
            for location in os.listdir(self.folder_path):
                path = os.path.join(self.folder_path, location)
                if os.path.isdir(path):
                    for file_name in os.listdir(path):
                        file_path = os.path.join(path, file_name)
                        if os.path.isfile(file_path):
                            if not file_path in self.file_paths_set:
                                self.file_paths.add(location=location, file_path=file_path)

    def process_image_path(self, file_path):
        pass

    def process_images(self):
        while self.is_running:
            location, file_path = self.file_paths.get()
            self.process_image_path(file_path=file_path)
            self.file_paths.remove(location=location, file_path=file_path)

    def start(self):
        self.images_finder_thread.start()
        self.images_finder_thread.start()
    
    def stop(self):
        self.is_running = False