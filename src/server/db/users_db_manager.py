from database_manager import DatabaseManager

class UsersDbManager:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.initialize_db()

    def initialize_db(self):
        """Create users table if it doesn't exist."""
        self.db_manager.execute_update('''CREATE TABLE IF NOT EXISTS users (
                            username TEXT PRIMARY KEY,
                            password TEXT NOT NULL)''')
    
    def get_user_password(self, username):
        return self.db_manager.execute_query_one("SELECT password FROM users WHERE username = ?", (username,))
    
    def insert_user(self, username, password):
        self.db_manager.execute_update("INSERT INTO users (username, password) VALUES (%s, %s)",
                                        (username, password))
    
    def delete_user(self, username):
        # NOTE: might need this in the future
        pass