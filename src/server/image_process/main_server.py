
import asyncio
import cv2
from ultralytics import YOLO
from concurrent.futures import ThreadPoolExecutor
import aiofiles
import os
from datetime import datetime
from ultralytics.engine.results import Boxes

class MainServer:
    def __init__(self):
        """Initializes the MainServer with a YOLO model and a thread pool executor."""
        self.model = self.load_yolo_model()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.conf_threshold = 0.6
    
    def load_yolo_model(self) -> YOLO:
        """Loads the YOLO model for object detection from a predefined path."""
        model = YOLO(r".\data\models\yolov8n-face.pt", task='detect')
        return model
    
    async def write_files_async(self, frame, pred_data, camera_location):
        """
        Asynchronously writes cropped images from detected objects to files.
        
        Args:
            frame: The video frame from which objects are detected.
            pred_data: The prediction data containing bounding boxes.
            camera_id: Identifier for the camera source.
        """
        imgs_path = f'./data/faces/{camera_location}/'
        os.makedirs(imgs_path, exist_ok=True)

        for top_left, bottom_right, _ in pred_data:
            cropped_face = frame[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
            file_path = imgs_path + datetime.now().strftime('%Y%m%d_%H%M%S') + '.jpg'
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(cv2.imencode('.jpg', cropped_face)[1].tobytes())
    
    def get_prediction_data(self, boxes : Boxes) -> list:
        """Extracts prediction data from the YOLO model's output boxes."""
        pred_data = []
        for xyxy, conf in zip(boxes.xyxy.tolist(), boxes.conf.tolist()):
            if conf >= self.conf_threshold:
                top_left = tuple(map(int, xyxy[:2]))
                bottom_right = tuple(map(int, xyxy[2:]))
                pred_data.append((top_left, bottom_right, conf))
        return pred_data
    
    def draw(self, frame : cv2.UMat, pred_data : list) -> cv2.UMat:
        """Draws bounding boxes and confidence scores on the video frame."""
        for top_left, bottom_right, conf in pred_data:
            color = (0, 255, 0)  # Green
            thickness = 2
            cv2.rectangle(frame, top_left, bottom_right, color, thickness)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(frame, str(conf), top_left, font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        return frame
    
    async def process_frame(self, frame, camera_location):
        """Processes each video frame to detect objects and write them to files asynchronously."""
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(self.executor, self.model, frame)
        pred_data = self.get_prediction_data(results[0].boxes)
        await self.write_files_async(frame, pred_data, camera_location)
    
    async def capture_and_process_video(self):
        """Captures video frames and processes them for object detection."""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open video stream.")
            return
        
        frame_count = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Can't receive frame. Exiting ...")
                    break
                
                frame_count += 1
                if frame_count == 10:
                    frame_count = 0
                    await asyncio.create_task(self.process_frame(frame, 'web'))
                
                cv2.imshow('Frame', frame)
                if cv2.waitKey(1) == ord('q'):
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()
    
    async def run(self):
        """Starts the video capture and processing loop."""
        await self.capture_and_process_video()

if __name__ == "__main__":
    server = MainServer()
    asyncio.run(server.run())
