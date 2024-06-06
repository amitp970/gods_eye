"""
This module defines a LiveServer class that handles live streaming of camera feeds using Flask and SocketIO.

Imports:
    - Flask: The Flask web application class.
    - Flask_SocketIO: Flask extension for creating web applications with Socket.IO.
    - socket: Provides low-level networking interface.
    - traceback: Provides methods for extracting, formatting, and printing stack traces.
    - threading: Allows for the creation and management of threads.
    - .config.settings: Custom module to access configuration settings.
    - src.core.protocol.receive_data: Custom module to handle receiving data.
"""

from flask import Flask
from flask_socketio import SocketIO, emit
import socket
import traceback
import threading
import ssl

from .config import settings
from src.core.protocol import receive_data

app = Flask(__name__)
socketio = SocketIO(app, async_mode=None, cors_allowed_origins="*")

class LiveServer:
    """
    A class to handle live streaming of camera feeds using Flask and SocketIO.
    """

    def __init__(self, host=settings.HTTP_SERVER_IP, port=settings.HTTP_SERVER_CAMERA_LIVE_PORT):
        """
        Initializes the LiveServer with the given host and port.

        Args:
            host (str): The IP address to bind the server to. Defaults to settings.HTTP_SERVER_IP.
            port (int): The port to bind the server to. Defaults to settings.HTTP_SERVER_CAMERA_LIVE_PORT.
        """
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.bind((host, port))
        self.server_sock.listen()
        self.running = False

    def handle_client(self, client_socket, addr):
        """
        Handles a new client connection, receiving live feed data and emitting it via SocketIO.

        Args:
            client_socket (socket.socket): The socket connected to the client.
            addr (tuple): The address of the client.
        """
        try:
            client_socket.settimeout(5)
            camera_id = receive_data(client_socket)

            if camera_id:
                camera_id = camera_id['id']

                while self.running:
                    data = receive_data(client_socket)
                    if not data:
                        print("Exiting live feed")
                        break
                    socketio.emit(f'live-{camera_id}', data)
                    
        except Exception as e:
            print(e)
            traceback.print_exc()
        
        client_socket.close()

    def start_server(self):
        """
        Starts the server to accept new client connections.
        """
        while self.running:
            try:
                client_socket, addr = self.server_sock.accept()
                threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()
            except socket.timeout:
                pass

    def start(self):
        """
        Starts the live server and the Flask-SocketIO server.
        """
        self.running = True
        self.server_sock.settimeout(5)

        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certfile=settings.SSL_CERT_FILE, keyfile=settings.SSL_KEY_FILE)

        threading.Thread(target=socketio.run, args=(app, settings.HTTP_SERVER_IP, 5000), kwargs={'ssl_context': ssl_context}).start()
        threading.Thread(target=self.start_server).start()

    def stop(self):
        """
        Stops the live server.
        """
        self.running = False
