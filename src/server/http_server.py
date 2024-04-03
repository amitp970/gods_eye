import socket
import re
import sqlite3
import bcrypt
import json  # Assuming JSON data for POST requests
import mysql.connector
from mysql.connector import Error

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'amit',  # Replace with your MySQL username
    'password': 'ilanaviv12',  # Replace with your MySQL password
    'database': 'god_client'  # Replace with your database name
}

# Server Configuration
IP = '0.0.0.0'
PORT = 80  # Default HTTP port
SOCKET_TIMEOUT = 1
ROOT = r'C:\Users\amitp\cs-project\gods_eye\src\server'  # Update this path to your files location
DEFAULT_URL = '/login.html'
PROTOCOL = 'HTTP/1.1'

def create_connection():
    """Create a database connection and return the connection object."""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Error: '{e}'")
    return connection

def initialize_db():
    """Create users table if it doesn't exist."""
    try:
        conn = create_connection()
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                              username VARCHAR(255) PRIMARY KEY,
                              password VARCHAR(255) NOT NULL)''')
            conn.commit()
    except Error as e:
        print(e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def add_user(username, password):
    """Add a new user to the database."""
    try:
        conn = create_connection()
        if conn.is_connected():
            cursor = conn.cursor()
            query = "INSERT INTO users (username, password) VALUES (%s, %s)"
            cursor.execute(query, (username, password))
            conn.commit()
    except Error as e:
        print(e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def verify_user(username, password):
    """Verify user's login credentials."""
    user_exists = False
    try:
        conn = create_connection()
        if conn.is_connected():
            cursor = conn.cursor()
            query = "SELECT password FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            record = cursor.fetchone()
            user_exists = password == record[0] if record else False
    except Error as e:
        print(e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return user_exists

def handle_get_request(resource, client_socket):
    if resource == '/':
        resource = DEFAULT_URL
    try:
        with open(ROOT + resource, 'rb') as file:
            content = file.read()
            send_response(200, 'text/html', content, client_socket)
    except FileNotFoundError:
        send_response(404, 'text/html', b'Not Found', client_socket)

def handle_post_request(resource, data, client_socket):
    if resource == '/login':
        credentials = json.loads(data)
        username = credentials['username']
        password = credentials['password']
        if verify_user(username, password):
            send_response(200, 'application/json', json.dumps({'message': 'Login successful'}).encode(), client_socket)
        else:
            send_response(401, 'application/json', json.dumps({'message': 'Unauthorized'}).encode(), client_socket)
    else:
        send_response(404, 'text/html', b'Not Found', client_socket)

def validate_http_request(request):
    try:
        lines = request.split('\r\n')
        method, resource, _ = lines[0].split(' ')
        data = ''
        if method == 'POST':
            headers_and_body = request.split('\r\n\r\n')
            if len(headers_and_body) > 1:
                data = headers_and_body[1]
        return True, method, resource, data
    except Exception as e:
        print(e)
        return False, '', '', ''

def handle_client(client_socket):
    client_request = client_socket.recv(1024).decode()
    valid_request, method, resource, data = validate_http_request(client_request)
    
    if valid_request:
        if method == 'POST':
            handle_post_request(resource, data, client_socket)
        else:  # Defaults to GET for simplicity
            handle_get_request(resource, client_socket)
    else:
        send_response(400, 'text/html', b'Bad Request', client_socket)
    
    client_socket.close()

def send_response(code, content_type, data, client_socket):
    header = f"{PROTOCOL} {code} OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(data)}\r\n\r\n"
    client_socket.sendall(header.encode() + data)

def main():
    initialize_db()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((IP, PORT))
    server_socket.listen()
    print(f"HTTP server listening on port {PORT}")
    
    while True:
        try:
            client_socket, _ = server_socket.accept()
            client_socket.settimeout(SOCKET_TIMEOUT)
            handle_client(client_socket)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    main()
