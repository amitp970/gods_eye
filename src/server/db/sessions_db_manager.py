from .database_manager import db_manager


class SessionsDbManager:
    def __init__(self):
        self.db_manager = db_manager
        self.initialize_sessions_table()

    def initialize_sessions_table(self):
        """Create sessions table if it doesn't exist."""
        self.db_manager.execute_update('''CREATE TABLE IF NOT EXISTS sessions (
                            session_id TEXT PRIMARY KEY, username TEXT NOT NULL,
                            timestamp REAL NOT NULL)''')
    
    def get_session_data(self, session_id):
        return self.db_manager.execute_query_one("SELECT username, timestamp FROM sessions WHERE session_id = ?", (session_id,))
    
    def insert_session(self, session_id, username, timestamp):
        self.db_manager.execute_update("INSERT INTO sessions (session_id, username, timestamp) VALUES (?, ?, ?)",
                                        (session_id, username, timestamp))
    
    def delete_session(self, session_id):
        self.db_manager.execute_update("DELETE FROM sessions WHERE session_id = ?", (session_id,))