import socket
import threading
import traceback

from .request_handler import RequestHandler
from .functions import services

class Server:
    def __init__(self, ip=socket.gethostbyname(socket.gethostname()), port=80, root='./src/server/files'):
        self.ip = ip
        self.port = port
        self.root = root
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    def start(self):
        try:
            self.socket.bind((self.ip, self.port))
            self.socket.listen(5)
            print(f"Server running on {self.ip}:{self.port}")

            while True:
                client_socket, _ = self.socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
        except KeyboardInterrupt:
            print("Server shutting down...")
        except Exception as e:
            print(e)
            traceback.print_exc()
        finally:
            for service in services:
                service.stop()

            self.socket.close()

    def extract_content_length(self, http_request):
        """Extract the Content-Length from a raw HTTP request string."""
        # Split the request into lines
        lines = http_request.split('\n')
        # Iterate through each line
        for line in lines:
            # Check if the line contains the Content-Length header
            if "Content-Length:" in line:
                # Extract the value after the colon and strip any extraneous spaces
                content_length = line.split(":")[1].strip()
                return content_length
        return None
    
    def handle_client(self, client_socket):
        try:
            bytes_read = 0
            header = 1024

            data_bytes = client_socket.recv(header)
            
            request_data = data_bytes.decode('utf-8')

            try:
                content_length = self.extract_content_length(request_data)

                if content_length and len(data_bytes) == header:
                    content_length = int(content_length)

                    try:
                        client_socket.settimeout(0.1)
                        while True:
                            request_data += client_socket.recv(header).decode('utf-8')
                    except socket.timeout as e:
                        print(e)
                                    
            except Exception as e:
                print(e)
                traceback.print_exc()
            
            response = RequestHandler(request_data, self.root).handle_request()

            client_socket.sendall(response)

        except Exception as e:
            print(f"Error handling request: {e}")
            traceback.print_exc()
        finally:
            client_socket.close()


if __name__=='__main__':
    server = Server()
    server.start()
