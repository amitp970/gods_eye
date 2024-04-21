import socket
import threading

from .request_handler import RequestHandler

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
        finally:
            self.socket.close()
    
    def handle_client(self, client_socket):
        try:
            request_data = client_socket.recv(1024).decode('utf-8')
            print(request_data)
            response = RequestHandler(request_data, self.root).handle_request()
            client_socket.sendall(response)
        except Exception as e:
            print(f"Error handling request: {e}")
        finally:
            client_socket.close()


if __name__=='__main__':
    server = Server()
    server.start()
