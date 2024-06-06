"""
This module sets up and runs a basic HTTP server.

Imports:
    - socket: Provides low-level networking interface.
    - threading: Allows for the creation and management of threads.
    - traceback: Provides methods for extracting, formatting, and printing stack traces.
    - .request_handler.RequestHandler: Custom module to handle HTTP requests.
    - .functions.services: List of services that need to be stopped when the server shuts down.
"""

import socket
import threading
import traceback
import ssl

from .request_handler import RequestHandler
from .functions import services

class Server:
    """
    A simple HTTP server class that handles incoming client connections and processes HTTP requests.
    """

    def __init__(self, ip=socket.gethostbyname(socket.gethostname()), port=443, root='./src/server/files'):
        """
        Initializes the server with the given IP address, port, and root directory.

        Args:
            ip (str): The IP address to bind the server to. Defaults to the local machine's IP.
            port (int): The port to bind the server to. Defaults to 443 for HTTPS.
            root (str): The root directory for the server files. Defaults to './src/server/files'.
        """
        self.ip = ip
        self.port = port
        self.root = root
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Create an SSL context
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # self.context.
        self.context.load_cert_chain(certfile="./data/https/server.crt", keyfile="./data/https/server.key")
        self.socket = self.context.wrap_socket(self.socket, server_side=True)
    
    def start(self):
        """
        Starts the server, binds it to the specified IP and port, and begins listening for incoming connections.
        """
        try:
            self.socket.bind((self.ip, self.port))
            self.socket.listen(5)
            print(f"Server running on {self.ip}:{self.port}")

            while True:
                try:
                    client_socket, addr = self.socket.accept()
                    print(f"Connection from {addr}")
                    threading.Thread(target=self.handle_client, args=(client_socket,)).start()
                except ssl.SSLError as e:
                    print(f"SSL error: {e}")
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
        """
        Extracts the Content-Length from a raw HTTP request string.

        Args:
            http_request (str): The raw HTTP request string.

        Returns:
            str: The content length if found, otherwise None.
        """
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
        """
        Handles an incoming client connection, processes the HTTP request, and sends back the response.

        Args:
            client_socket (socket.socket): The socket connected to the client.
        """
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

if __name__ == '__main__':
    server = Server()
    server.start()
