import socket
import threading
import time
import json

class CameraRadar:
    def __init__(self, listen_port=37020):
        self.listen_port = listen_port
        self.available_cameras = {}
        self.running = True
        self.listen_thread = threading.Thread(target=self.listen_for_cameras, daemon=True)
        self.cleanup_thread = threading.Thread(target=self.cleanup_cameras, daemon=True)
        # self.video_clients = {}
        self.timeout = 10

    def get_available_cameras(self):
        return self.available_cameras

    def listen_for_cameras(self):
        """Listen for broadcast messages from cameras on the designated port."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(('', self.listen_port))  # Listen on all interfaces

            while self.running:
                try:
                    message, addr = sock.recvfrom(1024)  # Receive broadcast
                    ip = addr[0]
                    if message:
                        try:
                            camera_info = json.loads(message.decode('utf-8'))
                        except Exception as e:
                            print(e)
                            continue

                        if 'type' in camera_info and camera_info['type'] == 'cameraConn':
                            camera_info['last_seen'] = time.time()
                            self.available_cameras[ip] = camera_info
                            print(f"Discovered camera: {camera_info}")
                except socket.error as e:
                    print(f"Socket error: {e}")
                except Exception as e:
                    print(f"Error: {e}")

    def cleanup_cameras(self):
        """Remove cameras that haven't broadcasted in the last timeout seconds."""
        while self.running:
            current_time = time.time()
            cameras_to_remove = [ip for ip, info in self.available_cameras.items() if current_time - info['last_seen'] > self.timeout]
            for ip in cameras_to_remove:
                del self.available_cameras[ip]
                print(f"Removed camera: {ip} due to timeout.")
            time.sleep(2)  # Check every 2 seconds

    def display_available_cameras(self):
        """Print the list of discovered cameras."""
        if not self.available_cameras:
            print("No cameras available.")
        else:
            print("Available cameras:")
            for ip, details in self.available_cameras.items():
                print(f"{ip}: {details}")

    # def select_and_connect_camera(self):
    #     """Allow user to select a camera and connect to it."""
    #     self.display_available_cameras()
    #     camera_ip = input("Enter the IP of the camera to connect: ")
    #     if camera_ip in self.cameras:
    #         details = self.cameras[camera_ip]
    #         port = details['port']  # Assuming the port is part of the details
    #         client = VideoClient(camera_ip, port, None)
    #         client.connect_to_server()
    #         self.video_clients[camera_ip] = client
    #         print(f"Connected to camera at {camera_ip}")
    #     else:
    #         print("Camera not found.")

    def start(self):
        """Start listening for cameras."""
        self.listen_thread.start()
        self.cleanup_thread.start()
        print("Started listening for camera broadcasts...")

    def stop(self):
        """Stop listening for cameras."""
        self.running = False
        print("Stopped listening for camera broadcasts.")

def main():
    camera_connections = CameraRadar()
    camera_connections.start()

    try:
        # Allow user to interact and choose a camera to connect
        while True:
            time.sleep(10)
            print("Press Control + C to exit")
            # input("Press Enter to disconnect and exit...")  # Hold the connection until user decides to exit
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        camera_connections.stop()

if __name__ == "__main__":
    main()
