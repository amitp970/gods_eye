"""
This module defines a SessionsDbManager class that handles session-related database operations using the DatabaseManager.

Imports:
    - .database_manager.db_manager: Instance of DatabaseManager for executing database operations.
"""

from .database_manager import db_manager

class SessionsDbManager:
    """
    A class to manage session-related database operations.
    """

    def __init__(self):
        """
        Initializes the SessionsDbManager and ensures the sessions table exists.
        """
        self.db_manager = db_manager
        self.initialize_sessions_table()

    def initialize_sessions_table(self):
        """
        Creates the sessions table if it doesn't exist.
        """
        self.db_manager.execute_update('''CREATE TABLE IF NOT EXISTS sessions (
                            session_id TEXT PRIMARY KEY, username TEXT NOT NULL,
                            timestamp REAL NOT NULL)''')

    def get_session_data(self, session_id):
        """
        Retrieves session data (username and timestamp) for the given session ID.

        Args:
            session_id (str): The session ID to look up.

        Returns:
            tuple: The username and timestamp associated with the session ID, or None if not found.
        """
        return self.db_manager.execute_query_one("SELECT username, timestamp FROM sessions WHERE session_id = ?", (session_id,))
    
    def insert_session(self, session_id, username, timestamp):
        """
        Inserts a new session into the sessions table.

        Args:
            session_id (str): The session ID.
            username (str): The username associated with the session.
            timestamp (float): The timestamp when the session was created.
        """
        self.db_manager.execute_update("INSERT INTO sessions (session_id, username, timestamp) VALUES (?, ?, ?)",
                                        (session_id, username, timestamp))
    
    def delete_session(self, session_id):
        """
        Deletes a session from the sessions table.

        Args:
            session_id (str): The session ID to delete.
        """
        self.db_manager.execute_update("DELETE FROM sessions WHERE session_id = ?", (session_id,))
