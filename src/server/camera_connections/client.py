import socket
import ssl
import json
import cv2
import time
import src.server.camera_connections.protocol as protocol

class Client:
    def __init__(self, server_host='127.0.0.1', server_port=54321):
        self.server_host = server_host
        self.server_port = server_port
        self.ssl_context = ssl.create_default_context()
        
        # For self-signed certificates, you might need to specify the server's certificate.
        self.ssl_context.load_verify_locations('./src/server/auth/cert/server_cert.pem')
        self.ssl_socket = self.ssl_context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_hostname=server_host)

    def authenticate(self):
        token = {"type": "auth", "token": "SECRET_TOKEN"}
        self.send_message(token)
        response = self.receive_message()
        if response["status"] == "success":
            print("Authentication Successful")
            return True
        else:
            print("Authentication Failed")
            return False

    def send_message(self, message):
        protocol.send_data(self.ssl_socket, message)

    def receive_message(self):
        return protocol.receive_data(self.ssl_socket)

    def send_camera_data(self, frame):
        data = {"type": "data", "frame_data": frame.tolist()}  # Example, adjust according to actual data handling
        self.send_message(data)
        print("Data sent, waiting for acknowledgment...")
        ack = self.receive_message()
        print(f"Acknowledgment received: {ack}")

    def start(self):
        self.ssl_socket.connect((self.server_host, self.server_port))
        if self.authenticate():
            cap = cv2.VideoCapture(0)
            try:
                while True:
                    ret, frame = cap.read()
                    if ret:
                        self.send_camera_data(frame)
                        time.sleep(1)  # Adjust based on needed frame rate
                    else:
                        print("Failed to capture frame")
                        break
            finally:
                cap.release()
                self.ssl_socket.close()
                print("Connection closed")

# To run the client
if __name__ == "__main__":
    client = Client()
    client.start()
