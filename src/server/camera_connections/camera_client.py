import socket
import base64
import cv2
import numpy as np
import uuid
from datetime import datetime
import os

from src.core.protocol import receive_data, send_data

class CameraClient:
    def __init__(self, host, port, camera_location):
        self.host = host
        self.port = port
        self.sock = None
        self.camera_location = camera_location
        self.is_running = False

    def connect_to_server(self):
        """Create a TCP/IP socket and connect to the server."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        print("Connected to server.")

    def decode_frame(self, base64_string):
        """Decode a base64 string to an OpenCV image."""
        img_bytes = base64.b64decode(base64_string)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return frame
    
    def write_file(self, frame, time=datetime.now().strftime('%Y%m%d_%H%M%S')):
        """
        Asynchronously writes cropped images from detected objects to files.
        
        Args:
            frame: The video frame from which objects are detected.
        """
        try:
            lat = self.camera_location['lat']
            lng = self.camera_location['lng']
        except Exception as e:
            print(e)
            lat = 0
            lng = 0
        
        imgs_path = f'./data/cameras/{lat}_{lng}/'

        os.makedirs(imgs_path, exist_ok=True)

        file_path = f"{imgs_path}/{uuid.uuid4()}-{time}.jpg"
        with open(file_path, 'wb') as f:
            f.write(cv2.imencode('.jpg', frame)[1].tobytes())

    def receive_frames(self):
        """Receive frames from the server and write them to the file system using OpenCV."""
        try:
            while self.is_running:
                # Receive data from the server
                frame_info = receive_data(self.sock)
                if not frame_info:
                    print("Connection closed by server.")
                    break

                frame = self.decode_frame(frame_info['frame'])
                time = frame_info['time']

                # NOTE: write the frame to the correct folder data/cameras/{location}/{uuid4()}.jpg()
                self.write_file(frame, time)

                # # Display the frame
                # cv2.imshow('Live Video', frame)
                # if cv2.waitKey(1) & 0xFF == ord('q'):
                #     break
        finally:
            # cv2.destroyAllWindows()
            self.disconnect_from_server()

    def disconnect_from_server(self):
        """Close the socket and disconnect from the server."""
        self.sock.close()
        print("Disconnected from server.")
    
    def stop(self):
        self.is_running = False
        
    def start(self):
        self.connect_to_server()
        self.is_running=True
        self.receive_frames()

def main():
    server_host = '192.168.68.123'  # Change to your server's IP address
    server_port = 12345        # Change to your server's port
    client = CameraClient(server_host, server_port, "tel aviv")
    client.start()

if __name__ == "__main__":
    main()
