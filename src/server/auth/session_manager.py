"""
This module defines a SessionManager class that handles session management, including generating, validating, and destroying sessions.

Imports:
    - os: Provides a way of using operating system-dependent functionality.
    - base64: Provides methods for encoding and decoding Base64 data.
    - time: Provides time-related functions.
    - src.server.db.sessions_db_manager.SessionsDbManager: Custom module to manage session data in the database.
"""

import os
import base64
import time
from src.server.db.sessions_db_manager import SessionsDbManager

class SessionManager:
    """
    A class to manage user sessions, including generating, validating, and destroying sessions.
    """
    # Check for session validity includes expiration check
    SESSION_EXPIRATION = 3600  # 1 hour

    def __init__(self):
        """
        Initializes the SessionManager with a SessionsDbManager.
        """
        self.db_manager = SessionsDbManager()

    def generate_session_id(self, username=None):
        """
        Generates a new session ID for the specified user.

        Args:
            username (str, optional): The username for which to generate a session ID. Defaults to None.

        Returns:
            str: The generated session ID.
        """
        session_id = base64.urlsafe_b64encode(os.urandom(16)).decode()
        self.db_manager.insert_session(session_id=session_id, username=username, timestamp=time.time())
        return session_id

    def is_session_valid(self, session_id):
        """
        Checks if the session ID is valid, including an expiration check.

        Args:
            session_id (str): The session ID to check.

        Returns:
            bool: True if the session is valid, False otherwise.
        """
        session_info = self.db_manager.get_session_data(session_id=session_id)
        if session_info and (time.time() - session_info[1]) < SessionManager.SESSION_EXPIRATION:
            return True
        
        self.destroy_session(session_id)
        return False

    def destroy_session(self, session_id):
        """
        Destroys the session with the given session ID.

        Args:
            session_id (str): The session ID to destroy.
        """
        self.db_manager.delete_session(session_id=session_id)
    
    def find_user(self, session_id):
        """
        Finds the username associated with the given session ID.

        Args:
            session_id (str): The session ID to search for.

        Returns:
            str: The username associated with the session ID, or None if not found.
        """
        if record := self.db_manager.get_session_data(session_id=session_id):
            return record[0]
