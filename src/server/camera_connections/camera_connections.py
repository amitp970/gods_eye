import socket
import ssl
from uuid import uuid4
from typing import List
import threading
# from src.server.models.camera import Camera
import time
import json
import cv2
import numpy as np

import protocol
# Server settings
IP = '127.0.0.1'
PORT = 54321
CERT_FILE = './src/server/auth/cert/server_cert.pem'
KEY_FILE = './src/server/auth/cert/server_key.pem'

class CameraConnection:
    def __init__(self, client_socket, client_address):
        self.camera_id = uuid4()
        self.client_socket = client_socket
        self.client_address = client_address
        self.frame_rate = 1

        self.handle_client()

    def handle_client(self):
        try:
            while True:
                # message = self.client_socket.recv(5096).decode('utf-8')
                message_dict = protocol.receive_data(self.client_socket)
                if message_dict:
                    response = self.process_message(message_dict)
                    protocol.send_data(self.client_socket, response)
                    # self.client_socket.sendall(json.dumps(response).encode('utf-8'))
                else:
                    break
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.client_socket.close()

    def process_message(self, message):
        if message['type'] == 'auth':
            return self.authenticate(message['token'])
        elif message['type'] == 'data':
            # Process data here (e.g., save frames)
            frame = np.array(message['frame_data'])
            frame = frame.astype(np.uint8)

            cv2.imwrite(f'myphoto{uuid4()}.jpg', frame)

            return {"type": "ack", "status": "received"}
        elif message['type'] == 'disconnect':
            return {"type": "disconnect_ack"}

    def authenticate(self, token):
        valid_token = "SECRET_TOKEN"  # This should be securely stored/configured
        if token == valid_token:
            return {"type": "auth_response", "status": "success"}
        else:
            return {"type": "auth_response", "status": "failure"}

class CameraConnections:
    def __init__(self):
        self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((IP, PORT))
        self.ssl_sock = self.ssl_context.wrap_socket(self.sock, server_side=True)

    def start(self):
        self.ssl_sock.listen(5)
        print(f"Listening to camera connections on {self.ssl_sock.getsockname()}")
        
        try:
            while True:
                client_socket, client_address = self.ssl_sock.accept()
                threading.Thread(target=CameraConnection, args=(client_socket, client_address)).start()
        except Exception as e:
            print(e)
        finally:
            self.ssl_sock.close()

# NOTE: Uncomment the below lines to start the server
if __name__ == "__main__":
    server = CameraConnections()
    server.start()
