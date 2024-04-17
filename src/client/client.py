import socket
import threading
import os
import requests
import cv2
import time

class Client:
    
    def __init__(self, server_host='127.0.0.1', server_port=80, frame_rate=1):
        self.server_host = server_host
        self.frame_rate = frame_rate
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def send_data(self, data):
        try:
            self.sock.connect((self.server_host, self.server_port))
            
            self.sock.sendall(data)

            response = self.sock.recv(1024).decoee('utf-8')
        except Exception as e:
            print(e)
        finally:
            self.sock.close()


    def start(self):

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open video stream.")
            return
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Can't receive frame. Exiting ...")
                    break
                
                requests.get('http://localhost')
                
                cv2.imshow('Frame', frame)
                if cv2.waitKey(1) == ord('q'):
                    break

                time.sleep((1.0/self.frame_rate))
        finally:
            cap.release()
            cv2.destroyAllWindows()
    
        