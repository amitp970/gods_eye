import socket
import base64
import cv2
import numpy as np
from uuid import uuid4
from datetime import datetime
import os
import threading
import traceback

from src.core.protocol import receive_data, send_data
from .config import settings

class CameraConnection:
    def __init__(self, client_socket, ip, port, location, camera_id):

        self.sock = client_socket
        self.camera_ip = ip
        self.camera_port = port
        self.camera_id = camera_id

        self.camera_location = location

        self.running = False

    @staticmethod
    def decode_frame(base64_string):
        """Decode a base64 string to an OpenCV image."""
        img_bytes = base64.b64decode(base64_string)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return frame
    
    def write_file(self, frame, time=datetime.now().strftime('%Y%m%d_%H%M%S')):
        """
        Writes images to files.
        
        Args:
            frame: The video frame.
        """
        try:
            lat = self.camera_location['lat']
            lng = self.camera_location['lng']
        except Exception as e:
            print(e)
            traceback.print_exc()

            lat = 0
            lng = 0
        
        imgs_path = f'./data/cameras/{lat}_{lng}/'

        os.makedirs(imgs_path, exist_ok=True)

        file_path = f"{imgs_path}/{uuid4()}-{time}.jpg"
        with open(file_path, 'wb') as f:
            f.write(cv2.imencode('.jpg', frame)[1].tobytes())

    def handle_connection(self):
        if send_data(self.sock, {'success': True, 'id': self.camera_id}):
            print(f'{self.camera_ip}:{self.camera_port} connected.')
            self.running = True

            self.receive_frames()
        
    def start_live(self):
        send_data(self.sock, {'command': 'startLive'})

    def stop_live(self):
        send_data(self.sock, {'command': 'stopLive'})

    def close_connection(self):
        send_data(self.sock, {'command': 'closeConn'})

    def close(self):
        self.close_connection()
        self.running = False
        self.sock.close()

    def receive_frames(self):
        """Receive frames from the server and write them to the file system using OpenCV."""
        try:
            while self.running:
                # Receive data from the server
                frame_info = receive_data(self.sock)
                if not frame_info:
                    print("Connection closed by server.")
                    break

                frame = CameraConnection.decode_frame(frame_info['frame'])
                time = frame_info['time']

                # write the frame to the correct folder data/cameras/{location}/{uuid4()}.jpg()
                self.write_file(frame, time)
    
        except Exception as e:
            print(e)
            traceback.print_exc()




class CameraConnections:
    def __init__(self, host=settings.HTTP_SERVER_IP, port=settings.HTTP_SERVER_CAMERA_LISTEN_PORT):
        self.host = host
        self.port = port
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.running = False

        self.camera_connections = {}

    
    def handle_client(self, client_sock, address):
        try:
            msg = receive_data(client_sock)

            if msg['type'] == 'cameraConn':
                ip = address[0]
                port = address[1]

                print("Connection From: ", address)
                camera_id = str(uuid4())
                camera_connection = CameraConnection(client_sock, ip, port, msg['location'], camera_id)

                self.camera_connections[camera_id] = camera_connection

                threading.Thread(target=camera_connection.handle_connection).start()


        except Exception as e:
            print(e)
            traceback.print_exc()

            send_data(client_sock, {'success': False})

    def disconnect_camera(self, camera_id):
        if conn := self.get_camera_connection(camera_id):
            print("Closing conn")
            conn.close()
            del self.camera_connections[camera_id]
            return True

        print("couldn't find camera")
        return False
    
    def get_camera_connection(self, id):
        return self.camera_connections.get(id , None)
    
    def get_cameras(self):
        return self.camera_connections
    
    def start(self):
        self.running = True

        threading.Thread(target=self.start_server).start()
    
    def stop(self):
        self.running = False


    def start_server(self):
        try:
            self.server_sock.bind((self.host, self.port))

            self.server_sock.listen()
            print(f"Camera Server running on {self.host}:{self.port}")
            self.server_sock.settimeout(2)
            while self.running:
                try:
                    client_socket, address = self.server_sock.accept()
                
                    print(f'camera client: {address}')
                    threading.Thread(target=self.handle_client, args=(client_socket, address)).start()
                except socket.timeout:
                    pass
        except Exception as e:
            print(e)
            traceback.print_exc()