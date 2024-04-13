import os
import base64
import time

class SessionManager:
    
    def __init__(self):
        self.sessions = {}  # Stores session data
            # Check for session validity includes expiration check
        SESSION_EXPIRATION = 3600  # 1 hour

    def generate_session_id(self, username=None):
        session_id = base64.urlsafe_b64encode(os.urandom(16)).decode()
        self.sessions[session_id] = {'username': username, 'timestamp': time.time()}
        return session_id


    # Check for session validity includes expiration check
    SESSION_EXPIRATION = 3600  # 1 hour

    def is_session_valid(self, session_id):
        session_info = self.sessions.get(session_id, None)
        if session_info and (time.time() - session_info['timestamp']) < SessionManager.SESSION_EXPIRATION:
            return True
        
        self.destroy_session(session_id)
        
        return False

    def destroy_session(self, session_id):
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def find_user(self, session_id):
        if session_id in self.sessions:
            return self.sessions[session_id]['username']
