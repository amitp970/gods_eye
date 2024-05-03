from .database_manager import db_manager

class UsersDbManager:
    def __init__(self):
        self.db_manager = db_manager
        self.initialize_users_table()

    def initialize_users_table(self):
        """Create users table if it doesn't exist."""
        self.db_manager.execute_update('''CREATE TABLE IF NOT EXISTS users (
                            username TEXT PRIMARY KEY,
                            password TEXT NOT NULL, role INTEGER NOT NULL)''')
    
    def get_user_password(self, username):
        return self.db_manager.execute_query_one("SELECT password FROM users WHERE username = ?", (username,))
    
    def insert_user(self, username, password, role):
        self.db_manager.execute_update("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                                        (username, password, role))
        
    def get_user_role(self, username):
        return self.db_manager.execute_query_one("SELECT role FROM users WHERE username = ?", (username,))
    
    def delete_user(self, username):
        self.db_manager.execute_update("DELETE FROM users WHERE username = ?", (username,))

    def get_users(self):
        return self.db_manager.execute_query_all("SELECT username, role FROM users")