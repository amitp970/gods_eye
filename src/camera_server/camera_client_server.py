import cv2
import socket
import time
import base64
from datetime import datetime
from queue import Queue, Full, Empty
import os
from collections import deque
import traceback
import threading

from src.core.protocol import send_data, receive_data
from .config import settings

class CameraClient:
    def __init__(self, location, server_host=settings.HTTP_SERVER_PUBLIC_IP, server_port=settings.HTTP_SERVER_CAMERA_LISTEN_PORT):
        self.server_host = server_host
        self.server_port = server_port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.live = False
        self.running = True

        self.location = location

        self.frame_queue = Queue(maxsize=5)
        self.frame_buffer = deque()

        self.id = None

    

    def capture_frames(self):
        try:
            cap = cv2.VideoCapture(0)

            if not cap.isOpened():
                print("Error: Camera could not be opened.")
                return
            
            while self.running:
                ret, frame = cap.read()

                if not ret:
                    print("Error: Could not read frame from camera.")
                    break
            
                try:
                    self.frame_queue.put({'frame': frame, 'time': datetime.now().strftime(r'%Y%m%d_%H%M%S')}, timeout=0.1)
                except Full:
                    time.sleep(0.01)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def connect_to_server(self):
        self.sock.connect((self.server_host, self.server_port))
        print("Attempting to connect to Server.")

        message = {
            'type' : 'cameraConn',
            'location' : self.location
        }

        if not send_data(self.sock, message):
            return False, "Connection Failed."
        
        response = receive_data(self.sock)

        if response['success']:
            self.id = response['id']
            return True, "Connected to Server."
        
        return False, 'Connection Failed'
        
    
    def send_frame(self, sock, frame, time=datetime.now().strftime('%Y%m%d_%H%M%S')):
        # Process and send the frame (here you would typically serialize the frame)

        _, buffer = cv2.imencode('.jpg', frame)

        frame_data = base64.b64encode(buffer).decode('utf-8')
    
        if not send_data(sock, {'frame': frame_data, 'time': time}):
            print("Couldn't send message: disconnecting client.")
            self.running = False
            return False
        
        return True
                        

    def send_frames_for_analysis(self):
        while self.running:
            try:
                frame_data = self.frame_queue.get(timeout=0.1) 
            except Empty:
                time.sleep(0.1)
                continue
                
            if self.send_frame(sock=self.sock, frame=frame_data['frame'], time=frame_data['time']):
                time.sleep(1)


    def server_communication(self):
        while self.running:
            server_msg = receive_data(self.sock)

            if server_msg:
                try:
                    command = server_msg['command']

                    if command == 'startLive':
                        print("starting live")
                        self.live = True
                    elif command == 'stopLive':
                        print("stoping live")
                        self.live = False
                    elif command == 'closeConn':
                        self.running = False

                except Exception as e:
                    print(e)
                    traceback.print_exc()
    
    def live_video(self):
        while self.running:
            if self.live:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as live_socket:
                    live_socket.connect((settings.HTTP_SERVER_PUBLIC_IP, settings.HTTP_SERVER_CAMERA_LIVE_PORT))

                    if not send_data(live_socket, {'id': self.id}):
                        print("Couldn't send ID.")
                        

                    while self.running and self.live:
                        try:
                            frame_data = self.frame_queue.get(timeout=1)
                            if not self.send_frame(live_socket, frame=frame_data['frame'], time=frame_data['time']):
                                print("couldn't send live stream")
                                break
                            else:
                                time.sleep(0.01)
                        except Empty:
                            pass
                        except Exception as e:
                            print(e)
                            traceback.print_exc()

                    print("finished live")
            else:
                time.sleep(5)

    def start(self):
        try:
            result, msg = self.connect_to_server()

            if result:
                self.running = True

                threading.Thread(target=self.capture_frames).start()
                threading.Thread(target=self.send_frames_for_analysis).start()
                threading.Thread(target=self.server_communication).start()
                threading.Thread(target=self.live_video).start()
            else:
                print(msg)
        except Exception as e:
            print(e)
            traceback.print_exc()
            self.running = False

        
if __name__=='__main__':
    client = CameraClient(location={'lat': 32.1241975, 'lng' : 34.825830})
    client.start()






            
            

    
    
