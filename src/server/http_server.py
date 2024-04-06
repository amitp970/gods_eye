import socket
import re
import sqlite3
import bcrypt
import json  # Assuming JSON data for POST requests
from mysql.connector import Error
import threading
import time
from hashlib import sha256
import os
import base64
import mimetypes

# Server Configuration
IP = '0.0.0.0'
PORT = 80  # Default HTTP port
SOCKET_TIMEOUT = 1
ROOT = r'./src/server/files/pages'  # Update this path to your files location
DEFAULT_URL = '/login.html'
PROTOCOL = 'HTTP/1.1'

DB_FILE = r"./src/server/server_db.db"

EXTENSION_CONTENT_DICT = {'text/html' : 'r', 'image/jpeg' : 'rb',
                          'text/javascript' : 'r', 'text/css' : 'r', 'image/png' : 'rb', 'application/json' : 'r'}

active_sessions = {}  # This will store active sessions: {session_id: username}

def handle_logout(session_id):
    if session_id in active_sessions:
        del active_sessions[session_id]

def generate_session_id():
    session_id = base64.urlsafe_b64encode(os.urandom(16)).decode()
    active_sessions[session_id] = {'username': None, 'timestamp': time.time()}
    return session_id

# Check for session validity includes expiration check
SESSION_EXPIRATION = 3600  # 1 hour

def is_session_valid(session_id):
    session_info = active_sessions.get(session_id, None)
    if session_info and (time.time() - session_info['timestamp']) < SESSION_EXPIRATION:
        return True
    if session_info:
        del active_sessions[session_id]  # Cleanup expired session
    return False

def create_connection():
    """Create a database connection to the SQLite database specified by DB_FILE."""
    try:
        conn = sqlite3.connect(DB_FILE)
        return conn
    except Error as e:
        print(e)
    return None

def initialize_db():
    """Create users table if it doesn't exist."""
    conn = create_connection()
    if conn is not None:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                          username TEXT PRIMARY KEY,
                          password TEXT NOT NULL)''')
        conn.commit()
        cursor.close()


def add_user(username, password):
    """Add a new user to the database."""
    try:
        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            query = "INSERT INTO users (username, password) VALUES (%s, %s)"
            cursor.execute(query, (username, password))
            conn.commit()
    except Error as e:
        print(e)
    finally:
        conn.close()

def verify_user(username, password):
    user_exists = False
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        record = cursor.fetchone()
        
        # user_exists = password == record[0] if record else False
        if record:
            stored_password = record[0]
            user_exists = bcrypt.checkpw(password=password.encode(), hashed_password=stored_password)

    except Error as e:
        print(e)
    finally:
        conn.close()
    return user_exists

def handle_get_request(resource, client_socket):
    file_path = f'./src/server/files/{resource}' if resource != '/' else './src/server/files/login.html'

    # Determine the content type
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = 'application/octet-stream'  # Default content type for unknown files

    try:
        # For binary files like images, open the file in binary mode
        mode = 'rb' if 'image' in content_type else 'r'
        with open(file_path, mode) as file:
            file_content = file.read()

        # Send the file content in the response
        send_response(200, content_type, file_content, client_socket)
    except FileNotFoundError:
        # File not found, send a 404 response
        send_response(404, 'text/html', 'File not found', client_socket)
    except Exception as e:
        print(f'Error serving {resource}: {e}')
        send_response(500, 'text/html', 'Internal server error', client_socket)


def handle_signup(data):
    data_dict = json.loads(data)
    username = data_dict['username']
    password = data_dict['password']  # Password should be hashed on the client-side

    # Check if the user already exists
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        return False, "User already exists"

    # Hash the password (even though it's already hashed client-side, double hashing for demonstration)
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    # Insert the new user
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    cursor.close()
    conn.close()
    return True, "Signup successful"

# Modify the handle_post_request function
def handle_post_request(resource, data, client_socket):
    if resource == '/login':
        data_dict = json.loads(data)
        username = data_dict['username']
        password = data_dict['password']  # Assuming password is sent in plaintext for verification
        if verify_user(username, password):
            session_id = generate_session_id()
            # Set cookie in the response
            send_response(302, 'text/html', '<html><body>Login successful. Redirecting...</body></html>', client_socket, additional_headers={'Set-Cookie': f'session_id={session_id}; Path=/', 'Location': '/home.html'})
        else:
            send_response(401, 'application/json', json.dumps({'message': 'Unauthorized'}), client_socket)
    elif resource == '/signup':
        success, message = handle_signup(data)
        if success:
            send_response(200, 'application/json', json.dumps({'message': message}), client_socket)
        else:
            send_response(400, 'application/json', json.dumps({'message': message}), client_socket)
    else:
        # Handle other POST requests or extend for more functionalities
        pass

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

def send_response(code, content_type, data, client_socket, additional_headers=None):
    mode = EXTENSION_CONTENT_DICT[content_type]
    print(f"{content_type} : {mode}")
    if 'b' not in mode:
        data = data.encode()  # Ensure the data is bytes
    headers = {**{'Content-Type': content_type, 'Content-Length': str(len(data))}, **(additional_headers if additional_headers else {})}
    header = f"{PROTOCOL} {code} OK\r\n" + "\r\n".join([f"{key}: {value}" for key, value in headers.items()]) + "\r\n\r\n"
    client_socket.sendall(header.encode() + data)

# def send_response(code, content_type, data, client_socket, mode='r', additional_headers=None):
#     if 'b' not in mode:
#         data = data.encode()  # Ensure the data is bytes
#     header = f"HTTP/1.1 {code} OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(data)}\r\n\r\n"
#     client_socket.sendall(header.encode() + data)

def main():
    initialize_db()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((IP, PORT))
    server_socket.listen()
    print(f"HTTP server listening on port {PORT}")
    
    while True:
        try:
            client_socket, _ = server_socket.accept()
            
            thread = threading.Thread(target=handle_client, args=(client_socket, ))
            thread.start()


        except Exception as e:
            print(e)

if __name__ == "__main__":
    main()
