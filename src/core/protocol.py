import socket
import ssl
import json
import struct

def send_data(sock: socket.socket, message):
    """
    Send a JSON message through an SSL socket with a header indicating the message length.
    
    Args:
        sock (ssl.SSLSocket): The SSL socket through which the message will be sent.
        message (dict): A dictionary containing the message to send.
    """
    try:
        json_data = json.dumps(message)
        encoded_data = json_data.encode('utf-8')
        header = struct.pack('!I', len(encoded_data))  # '!I' denotes network byte order unsigned int
        sock.sendall(header + encoded_data)
        return True
    except Exception as e:
        print(f"Error sending data: {e}")
        return False

def receive_data(sock: socket.socket):
    """
    Receive a JSON message from an SSL socket, reading the message length from the header first.
    
    Args:
        sock (ssl.SSLSocket): The SSL socket from which the message will be received.
        
    Returns:
        dict: The received JSON message as a dictionary, or None if an error occurs.
    """
    try:
        # First, read the length of the data
        header = sock.recv(4)  # Assuming header is always 4 bytes long
        if not header:
            return None
        data_length = struct.unpack('!I', header)[0]
        
        # Now read the exact amount of data
        received_data = b''
        while len(received_data) < data_length:
            part = sock.recv(data_length - len(received_data))
            if not part:
                raise ConnectionError("Connection lost while receiving data")
            received_data += part

        resp = json.loads(received_data.decode('utf-8'))
        return resp
    except json.JSONDecodeError:
        print("Error decoding JSON data.")
    except Exception as e:
        print(f"Error receiving data: {e}")
        return None
