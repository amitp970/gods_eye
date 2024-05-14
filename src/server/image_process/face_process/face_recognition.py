from ultralytics import YOLO
import threading
# import torch

class FaceRecognition:
    def __init__(self):
        self.model = self.load_yolo_model()
        self.lock = threading.Lock()

    def load_yolo_model(self):
        """Loads the YOLO model for object detection from a predefined path."""
        model = YOLO(r".\data\models\yolov8n-face.pt", task='detect')
        # model = torch.load(r".\data\models\yolov8n-face.pt")
        return model
    
    def predict(self, frame):
        with self.lock:
            return self.model(frame)

