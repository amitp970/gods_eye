from flask import Flask
from flask_socketio import SocketIO, emit
import socket
import traceback
import threading

from .config import settings
from src.core.protocol import receive_data


app = Flask(__name__)
socketio = SocketIO(app, async_mode=None, cors_allowed_origins="*")

class LiveServer:
    def __init__(self, host=settings.HTTP_SERVER_IP, port=settings.HTTP_SERVER_CAMERA_LIVE_PORT):
        
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.bind((host, port))
        self.server_sock.listen()

        self.running = False

    def handle_client(self, client_socket):

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
        while self.running:
            try:
                client_socket, addr = self.server_sock.accept()

                threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()
            except socket.timeout:
                pass

    def start(self):
        self.running = True
        self.server_sock.settimeout(5)

        threading.Thread(target=socketio.run, args=(app, settings.HTTP_SERVER_IP, 5000)).start()
        threading.Thread(target=self.start_server).start()


    
    def stop(self):
        self.running = False
        