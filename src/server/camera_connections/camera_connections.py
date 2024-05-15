"""
This module defines classes for managing camera connections, including handling connections, receiving frames, 
and managing multiple camera connections.

Imports:
    - socket: Provides low-level networking interface.
    - base64: Provides methods for encoding and decoding Base64 data.
    - cv2: OpenCV library for computer vision tasks.
    - numpy as np: Provides support for large, multi-dimensional arrays and matrices.
    - uuid4: Provides methods for generating universally unique identifiers.
    - datetime: Supplies classes for manipulating dates and times.
    - os: Provides a way of using operating system-dependent functionality.
    - threading: Allows for the creation and management of threads.
    - traceback: Provides methods for extracting, formatting, and printing stack traces.
    - src.core.protocol.receive_data, src.core.protocol.send_data: Custom modules to handle sending and receiving data.
    - .config.settings: Custom module to access configuration settings.
"""

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
    """
    A class to represent a connection with a single camera, handling data reception and frame processing.
    """

    def __init__(self, client_socket, ip, port, location, camera_id):
        """
        Initializes the CameraConnection with the given socket, IP address, port, location, and camera ID.

        Args:
            client_socket (socket.socket): The socket connected to the client.
            ip (str): The IP address of the camera.
            port (int): The port number of the camera.
            location (dict): The location of the camera (latitude and longitude).
            camera_id (str): The unique identifier for the camera.
        """
        self.sock = client_socket
        self.camera_ip = ip
        self.camera_port = port
        self.camera_id = camera_id
        self.camera_location = location
        self.running = False

    @staticmethod
    def decode_frame(base64_string):
        """
        Decodes a base64 string to an OpenCV image.

        Args:
            base64_string (str): The base64 encoded string of the image.

        Returns:
            numpy.ndarray: The decoded image.
        """
        img_bytes = base64.b64decode(base64_string)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return frame
    
    def write_file(self, frame, time=datetime.now().strftime('%Y%m%d_%H%M%S')):
        """
        Writes images to files.

        Args:
            frame (numpy.ndarray): The video frame to write.
            time (str): The timestamp of the frame.
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
        """
        Handles the initial connection with the camera and starts receiving frames.
        """
        if send_data(self.sock, {'success': True, 'id': self.camera_id}):
            print(f'{self.camera_ip}:{self.camera_port} connected.')
            self.running = True
            self.receive_frames()
        
    def start_live(self):
        """
        Sends a command to the camera to start live streaming.
        """
        send_data(self.sock, {'command': 'startLive'})

    def stop_live(self):
        """
        Sends a command to the camera to stop live streaming.
        """
        send_data(self.sock, {'command': 'stopLive'})

    def close_connection(self):
        """
        Sends a command to the camera to close the connection.
        """
        send_data(self.sock, {'command': 'closeConn'})

    def close(self):
        """
        Closes the camera connection and stops running.
        """
        self.close_connection()
        self.running = False
        self.sock.close()

    def receive_frames(self):
        """
        Receives frames from the camera and writes them to the file system.
        """
        try:
            while self.running:
                frame_info = receive_data(self.sock)
                if not frame_info:
                    print("Connection closed by server.")
                    break

                frame = CameraConnection.decode_frame(frame_info['frame'])
                time = frame_info['time']
                self.write_file(frame, time)
    
        except Exception as e:
            print(e)
            traceback.print_exc()

class CameraConnections:
    """
    A class to manage multiple camera connections, including handling new connections, disconnecting cameras, 
    and starting the camera server.
    """

    def __init__(self, host=settings.HTTP_SERVER_IP, port=settings.HTTP_SERVER_CAMERA_LISTEN_PORT):
        """
        Initializes the CameraConnections with the given host and port.

        Args:
            host (str): The IP address to bind the server to. Defaults to settings.HTTP_SERVER_IP.
            port (int): The port to bind the server to. Defaults to settings.HTTP_SERVER_CAMERA_LISTEN_PORT.
        """
        self.host = host
        self.port = port
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False
        self.camera_connections = {}

    def handle_client(self, client_sock, address):
        """
        Handles a new client connection, initializing a CameraConnection and starting its handling thread.

        Args:
            client_sock (socket.socket): The socket connected to the client.
            address (tuple): The address of the client.
        """
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
        """
        Disconnects the camera with the given camera ID.

        Args:
            camera_id (str): The unique identifier for the camera.

        Returns:
            bool: True if the camera was disconnected, False otherwise.
        """
        if conn := self.get_camera_connection(camera_id):
            print("Closing conn")
            conn.close()
            del self.camera_connections[camera_id]
            return True

        print("couldn't find camera")
        return False
    
    def get_camera_connection(self, camera_id):
        """
        Retrieves the CameraConnection with the given camera ID.

        Args:
            camera_id (str): The unique identifier for the camera.

        Returns:
            CameraConnection: The CameraConnection object if found, otherwise None.
        """
        return self.camera_connections.get(camera_id, None)
    
    def get_cameras(self):
        """
        Retrieves all current camera connections.

        Returns:
            dict: A dictionary of all current camera connections.
        """
        return self.camera_connections
    
    def start(self):
        """
        Starts the camera server.
        """
        self.running = True
        threading.Thread(target=self.start_server).start()
    
    def stop(self):
        """
        Stops the camera server.
        """
        self.running = False

    def start_server(self):
        """
        Binds the server to the host and port, and starts accepting client connections.
        """
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
