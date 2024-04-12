import os
import mimetypes
import urllib.parse
from functions import Functions

EXTENSION_CONTENT_DICT = {'text/html' : 'r', 'image/jpeg' : 'rb',
                          'text/javascript' : 'r', 'text/css' : 'r', 
                          'image/png' : 'rb', 'application/json' : 'r'}

ROUTING_DICT = {
    # 'URL' : FUNC,...
    '/login' : Functions.login
}

class RequestHandler:
    
    def __init__(self, request_data, server_root):
        self.request_data = request_data
        self.server_root = server_root
        self.method, self.path, self.protocol = self.parse_request_line()
        
        if self.method == 'POST':
            self.headers, self.body = self.parse_headers_and_body()

    def parse_request_line(self):
        request_line = self.request_data.split('\r\n')[0]
        method, path, protocol = request_line.split(' ')
        return method, urllib.parse.unquote(path), protocol
    
    def parse_headers_and_body(self):
        parts = self.request_data.split('\r\n\r\n', 1)
        headers_part = parts[0]
        body = parts[1] if len(parts) > 1 else ''
        headers = self.parse_headers(headers_part)
        return headers, body

    def parse_headers(self, headers_part):
        headers = {}
        for line in headers_part.split('\r\n')[1:]:  # Skip the request line
            key, value = line.split(': ', 1)
            headers[key] = value
        return headers

    def handle_request(self):
        if self.method == 'GET':
            return self.handle_get_request()
        elif self.method == 'POST':
            return self.handle_post_request()
        else:
            return self.method_not_allowed()

    def handle_get_request(self):
        # NOTE: figure out whether the resource is a file or a function

        if self.path == '/' or os.path.isfile(self.server_root + self.path):
            # Serving files from the server root directory
            file_path = self.server_root + self.path
            if os.path.isdir(file_path):
                file_path += 'login.html'  # Serve the login file if the path is a directory
            if not os.path.exists(file_path):
                return self.not_found()
            return self.serve_file(file_path)
        else:
            if self.path in ROUTING_DICT:
                return self.generate_response(**ROUTING_DICT[self.path]())
            else:
                return self.method_not_allowed()
            
    def handle_post_request(self):
        if self.path in ROUTING_DICT:
            return self.generate_response(**ROUTING_DICT[self.path](headers=self.headers, body=self.body))
        else:
            return self.method_not_allowed()

    def serve_file(self, file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        try:
            with open(file_path, 'rb') as file:
                file_content = file.read()
                response = f'{self.protocol} 200 OK\r\n'
                response += f'Content-Type: {mime_type}\r\n'
                response += 'Connection: close\r\n\r\n'
                response = response.encode('utf-8') + file_content
                return response
        except Exception as e:
            print(f"Error serving file: {e}")
            return self.internal_server_error()

    def not_found(self):
        return f'{self.protocol} 404 Not Found\r\nConnection: close\r\n\r\n'.encode('utf-8')

    def method_not_allowed(self):
        return f'{self.protocol} 405 Method Not Allowed\r\nConnection: close\r\n\r\n'.encode('utf-8')

    def internal_server_error(self):
        return f'{self.protocol} 500 Internal Server Error\r\nConnection: close\r\n\r\n'.encode('utf-8')
    

    def generate_response(self, code, content_type, data, additional_headers=None):
        mode = EXTENSION_CONTENT_DICT[content_type]
        print(f"{content_type} : {mode}")
        if 'b' not in mode:
            data = data.encode('utf-8')  # Ensure the data is bytes
        headers = {**{'Content-Type': content_type, 'Content-Length': str(len(data))}, **(additional_headers if additional_headers else {})}
        header = f"{self.protocol} {code} OK\r\n" + "\r\n".join([f"{key}: {value}" for key, value in headers.items()]) + "\r\n\r\n"

        return header.encode('utf-8') + data