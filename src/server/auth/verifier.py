import bcrypt

from src.server.db.users_db_manager import UsersDbManager
from session_manager import SessionManager

class Verifier:
    def __init__(self):
        self.db_manager = UsersDbManager()
        self.session_manager = SessionManager()
    
    def add_user(self, username, password):
        
        # Check if user exists
        record = self.db_manager.get_user_password(username)

        if not record:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            self.db_manager.insert_user(username, hashed_password.decode())
            return True, "Success: User added"
        else:
            return False, "Failed: username already exists"
    
    def check_password(self, username, password):
        record = self.db_manager.get_user_password(username)

        if record:
            stored_password = record[0]

            is_verified = bcrypt.checkpw(password=password.encode('utf-8'), 
                                         hashed_password=stored_password.encode('utf-8'))
        else:
            return False, "Failed: username doesn't exists"
                    
        return is_verified, None

    def generate_session(self, username):
        return self.session_manager.generate_session_id(username)

    def check_session(self, session_id):
        return self.session_manager.is_session_valid(session_id)
    

    