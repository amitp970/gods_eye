import socket
import hashlib
import base64
import cv2
import pickle
import struct

def create_websocket_handshake_response(key):
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    hash = hashlib.sha1(key.encode('utf-8') + GUID.encode('utf-8')).digest()
    response_key = base64.b64encode(hash).decode('utf-8')
    return (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Accept: {}\r\n\r\n".format(response_key)
    )

def handle_client(connection):
    data = connection.recv(1024).decode('utf-8')
    lines = data.split("\r\n")
    key = ""
    for line in lines:
        if "Sec-WebSocket-Key" in line:
            key = line.split(": ")[1]
    response = create_websocket_handshake_response(key)
    connection.send(response.encode('utf-8'))
    
    # Simple echo message handling (not following WebSocket frame structure)
    while True:
        if connection:
            try:
                vid = cv2.VideoCapture(0)
                
                while(vid.isOpened()):
                    img, frame = vid.read()
                    a = pickle.dumps(frame)
                    message = struct.pack("Q",len(a))+a
                    connection.sendall(message)
                    
                    cv2.imshow('TRANSMITTING VIDEO', frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        connection.close()
            except Exception as e:
                print(e)

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 8765))
    server_socket.listen(1)
    print("WebSocket server listening on port 8765")
    
    while True:
        connection, _ = server_socket.accept()
        handle_client(connection)
        connection.close()

# Uncomment to start the server
start_server()