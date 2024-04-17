import socket
from uuid import uuid4

from models.camera import Camera
import time

class CameraConnection:
    def __init__(self, location, sock):
        self.camera: Camera = Camera(location=location, id=uuid4)
        self.sock: socket.socket = sock


    def start(self):
        try:
            while(True):
                print(f"Listening to camera connection on {self.sock.getsockname()}")
                time.sleep(10)
                break
        except Exception as e:
            print(e)
        finally:
            self.sock.close()
    
