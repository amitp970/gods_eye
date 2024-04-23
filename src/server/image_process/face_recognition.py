from ultralytics import YOLO


class FaceRecognition:
    def __init__(self):
        self.model = self.load_model()
        self.conf_threshold = 0.6

    def load_yolo_model(self):
        """Loads the YOLO model for object detection from a predefined path."""
        model = YOLO(r".\data\models\yolov8n-face.pt", task='detect')
        return model
    
    def predict(self, frame):
        return self.model(frame)

    