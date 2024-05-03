import cv2
import threading
import socket
import time
import numpy as np
import base64
import json
from datetime import datetime

from src.core.protocol import send_data, receive_data
from .config import settings

def create_udp_socket():
    """Create a UDP socket for broadcasting."""
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    return udp_socket

class CameraServer:
    def __init__(self, host=socket.gethostbyname(socket.gethostname()), port=12345, location=None, frame_rate=1):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.udp_socket = create_udp_socket()
        self.client_connected = False
        self.broadcast_thread = threading.Thread(target=self.__broadcast_ip, daemon=True)
        self.capture = None

        self.location = location
        self.frame_rate = frame_rate

    def __broadcast_ip(self):
        """Broadcast the IP address and port every 10 seconds when no clients are connected."""
        while True:

            if not self.client_connected:
                message = {
                    'type' : 'cameraConn',
                    'host' : self.host,
                    'port' : self.port,
                    'location' : self.location
                }
                # message = f"{self.host}:{self.port}"
                self.udp_socket.sendto(json.dumps(message).encode(), (settings.HTTP_SERVER_IP, settings.HTTP_SERVER_CAMERA_LISTEN_PORT))
                print(f"Broadcasting {message} on port 37020")
                time.sleep(10)

    def __client_communication(self, client_scoket):
        while self.client_connected:
            message = receive_data(client_scoket)
            # NOTE: implement support for recieving instructions form the client, ie: changing the frame rate 


    def __start_capture(self):
        """Start capturing video frames from the camera."""
        self.capture = cv2.VideoCapture(0)  # Index 0 to use the default webcam.
        if not self.capture.isOpened():
            print("Error: Camera could not be opened.")
            return False
        return True

    def __handle_client(self, client_socket, addr):
        """Handle client communications and send video frames."""
        print(f"Connected to {addr}")
        self.client_connected = True
        if self.__start_capture():
            try:
                while self.client_connected:
                    ret, frame = self.capture.read()
                    if not ret:
                        print("Error: Could not read frame from camera.")
                        break

                    # Process and send the frame (here you would typically serialize the frame)
                    _, buffer = cv2.imencode('.jpg', frame)
                    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                    # serialized_frame = buffer.tobytes()
                    
                    if not send_data(client_socket, {'frame': jpg_as_text, 'time': datetime.now().strftime('%Y%m%d_%H%M%S')}):
                        print("Couldn't send message: disconnecting client.")
                        break
            finally:
                self.client_connected = False
                client_socket.close()
                self.capture.release()
                print(f"Disconnected from {addr}")

    def start_server(self):
        """Start the server to accept connections."""
        self.server_socket.listen(1)
        self.broadcast_thread.start()
        print("Server is listening for connections...")
        
        while True:
            client_socket, addr = self.server_socket.accept()
            client_handler = threading.Thread(target=self.__handle_client, args=(client_socket, addr))
            client_handler.start()

# Uncomment to run:
if __name__=='__main__':
    camera_server = CameraServer(location={'lat': 32.1241975, 'lng' : 34.825830})
    camera_server.start_server()
