import os
import base64
import time
from db.sessions_db_manager import SessionsDbManager

class SessionManager:
    
    def __init__(self):
        # self.sessions = {}  # Stores session data
        self.db_manager = SessionsDbManager()
            # Check for session validity includes expiration check
        SESSION_EXPIRATION = 3600  # 1 hour

    def generate_session_id(self, username=None):
        session_id = base64.urlsafe_b64encode(os.urandom(16)).decode()

        self.db_manager.insert_session(session_id=session_id, username=username, timestamp=time.time())
        return session_id


    # Check for session validity includes expiration check
    SESSION_EXPIRATION = 3600  # 1 hour

    def is_session_valid(self, session_id):
        session_info = self.db_manager.get_session_data(session_id=session_id)
        if session_info and (time.time() - session_info[1]) < SessionManager.SESSION_EXPIRATION:
            return True
        
        self.destroy_session(session_id)
        
        return False

    def destroy_session(self, session_id):
        self.db_manager.delete_session(session_id=session_id)
    
    def find_user(self, session_id):
        if record := self.db_manager.get_session_data(session_id=session_id):
            return record[0]