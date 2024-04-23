import cv2
import os
import threading

from .config import settings

from face_recognition import FaceRecognition
from .face_process.data_manager import DataManager
from .face_process.deepface_encapsulator import FeatureExtractor

from collections import deque

class ImageProcessor:
    def __init__(self):
        self.face_model = FaceRecognition()
        self.data_manager = DataManager(index_path=settings.FAISS_PATH, db_path=settings.DATABASE_URL)
        self.feature_extractor = FeatureExtractor('Facenet')
        self.folder_path = settings.ROOT_PATH_IMAGES

        self.file_paths_deque = deque()
        self.file_paths_set = set()

        self.image_finder_thread = threading.Thread(target=self.find_images)
    

    def find_images(self):
        for location in os.listdir(self.folder_path):
            path = os.path.join(self.folder_path, location)
            if os.path.isdir(path):
                for file_name in os.listdir(path):
                    file_path = os.path.join(path, file_name)
                    if os.path.isfile(file_path):
                        if not file_path in self.file_paths_set:
                            self.file_paths_deque.append((location, file_path))
                            self.file_paths_set.add(file_path)
                        
                
    

    def process_image_path(self, file_path):
        pass