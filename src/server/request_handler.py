import os
import mimetypes
import urllib.parse
from .functions import Functions, ROUTING_DICT

EXTENSION_CONTENT_DICT = {
    'text/html': 'r', 'image/jpeg': 'rb',
    'text/javascript': 'r', 'text/css': 'r',
    'image/png': 'rb', 'application/json': 'r'
}

PRIVATE_PATH = '/private'
PUBLIC_PATH = '/public'

class RequestHandler:
    """
    A class to handle HTTP requests and responses.
    """

    def __init__(self, request_data, server_root):
        """
        Initialize the RequestHandler with request data and server root.

        Parameters:
        request_data (str): The raw HTTP request data.
        server_root (str): The root directory of the server.
        """
        self.request_data = request_data
        self.server_root = server_root
        self.method, self.path, self.protocol = self.parse_request_line()
        self.path, self.parameters = self.parse_path_parameters()

        if self.path == '/':
            self.path = '/index.html'
        
        self.headers, self.body = self.parse_headers_and_body()

    def parse_request_line(self):
        """
        Parse the request line to get the method, path, and protocol.

        Returns:
        tuple: (method, path, protocol)
        """
        request_line = self.request_data.split('\r\n')[0]
        method, path, protocol = request_line.split(' ')
        return method, urllib.parse.unquote(path), protocol

    def parse_path_parameters(self):
        """
        Parse the path to get the path and parameters.

        Returns:
        tuple: (path, parameters)
        """
        try: 
            path, parameters = self.path.split('?')
            parameters = {arg: val for arg, val in [param.split('=') for param in parameters.split('&')]}
            return path, parameters
        except Exception as e:
            return self.path, {}

    def parse_headers_and_body(self):
        """
        Parse the headers and body from the request data.

        Returns:
        tuple: (headers, body)
        """
        parts = self.request_data.split('\r\n\r\n', 1)
        headers_part = parts[0]
        body = parts[1] if len(parts) > 1 else ''
        headers = self.parse_headers(headers_part)
        return headers, body

    def parse_headers(self, headers_part):
        """
        Parse the headers part to get a dictionary of headers.

        Returns:
        dict: headers
        """
        headers = {}
        for line in headers_part.split('\r\n')[1:]:  # Skip the request line
            key, value = line.split(': ', 1)
            headers[key] = value
        return headers

    def handle_request(self):
        """
        Handle the HTTP request and generate a response.

        Returns:
        bytes: The HTTP response.
        """
        if self.method == 'GET':
            return self.handle_get_request()
        elif self.method == 'POST':
            return self.handle_post_request()
        else:
            return self.method_not_allowed()
        
    def get_resource_access_parameter(self):
        private_path = self.server_root + PRIVATE_PATH + self.path
        public_path = self.server_root + PUBLIC_PATH + self.path

        if os.path.isfile(private_path):
            return PRIVATE_PATH, private_path
        elif os.path.isfile(public_path):
            return PUBLIC_PATH, public_path
        
        return None, ''

    def handle_get_request(self):
        """
        Handle a GET request.

        Returns:
        bytes: The HTTP response.
        """
        
        access_parameter, file_path = self.get_resource_access_parameter()

        response_dict = {}

        if access_parameter == PRIVATE_PATH:
            response_dict = self.handle_private_resource_request(file_path, headers=self.headers)
        elif access_parameter == PUBLIC_PATH:
            response_dict = self.serve_file(file_path)
        else:
            if self.path in ROUTING_DICT:
                response_dict = ROUTING_DICT[self.path](headers=self.headers, parameters=self.parameters)

        if response_dict:
            return self.generate_response(**response_dict)
            
        return self.not_found()
    @Functions.role(1)
    def handle_private_resource_request(self, file_path, *args, **kwargs):
        """
        Handle a request for a private resource.

        Parameters:
        file_path (str): The path to the requested file.

        Returns:
        bytes: The HTTP response.
        """
        return self.serve_file(file_path)

    def handle_post_request(self):
        """
        Handle a POST request.

        Returns:
        bytes: The HTTP response.
        """
        if self.path in ROUTING_DICT:
            return self.generate_response(**ROUTING_DICT[self.path](headers=self.headers, body=self.body, parameters=self.parameters))
        else:
            return self.not_found()
            

    def serve_file(self, file_path):
        """
        Serve a file as the HTTP response.

        Parameters:
        file_path (str): The path to the file.

        Returns:
        dict: The HTTP response details.
        """
        response = {}
        mime_type, _ = mimetypes.guess_type(file_path)

        try:
            with open(file_path, 'rb') as file:
                file_content = file.read()

                response = {
                    'code': 200,
                    'content_type': mime_type,
                    'data': file_content,
                }
                return response
        except Exception as e:
            print(f"Error serving file: {e}")
            return self.internal_server_error()

    def not_found(self):
        """
        Generate a 404 Not Found response.

        Returns:
        bytes: The HTTP response.
        """
        return f'{self.protocol} 404 Not Found\r\nConnection: close\r\n\r\n'.encode('utf-8')

    def method_not_allowed(self):
        """
        Generate a 405 Method Not Allowed response.

        Returns:
        bytes: The HTTP response.
        """
        return f'{self.protocol} 405 Method Not Allowed\r\nConnection: close\r\n\r\n'.encode('utf-8')

    def internal_server_error(self):
        """
        Generate a 500 Internal Server Error response.

        Returns:
        bytes: The HTTP response.
        """
        return f'{self.protocol} 500 Internal Server Error\r\nConnection: close\r\n\r\n'.encode('utf-8')

    def generate_response(self, code, content_type, data, additional_headers=None):
        """
        Generate an HTTP response.

        Parameters:
        code (int): The HTTP status code.
        content_type (str): The content type of the response.
        data (str or bytes): The response body.
        additional_headers (dict, optional): Additional headers for the response.

        Returns:
        bytes: The HTTP response.
        """
        if not isinstance(data, bytes):
            data = data.encode('utf-8')  # Ensure the data is bytes

        headers = {
            **{'Content-Type': content_type, 'Content-Length': str(len(data))},
            **(additional_headers if additional_headers else {})
        }
        header = f"{self.protocol} {code} OK\r\n" + "\r\n".join([f"{key}: {value}" for key, value in headers.items()]) + "\r\n\r\n"

        return header.encode('utf-8') + data
