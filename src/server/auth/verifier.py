import bcrypt

from src.server.db.users_db_manager import UsersDbManager
from .session_manager import SessionManager

class Verifier:
    def __init__(self):
        self.users_manager = UsersDbManager()
        self.session_manager = SessionManager()
    
    def add_user(self, username, password, role=1):
        
        # Check if user exists
        record = self.users_manager.get_user_password(username)

        if not record:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            self.users_manager.insert_user(username, hashed_password.decode(), role)
            return True, "Success: User added"
        else:
            return False, "Failed: username already exists"
    
    def check_password(self, username, password):
        record = self.users_manager.get_user_password(username)

        if record:
            stored_password = record[0]

            is_verified = bcrypt.checkpw(password=password.encode('utf-8'), 
                                         hashed_password=stored_password.encode('utf-8'))
        else:
            return False, "Failed: username doesn't exists"
                    
        return is_verified, username
    
    def get_user_role(self, username):
        record = self.users_manager.get_user_role(username)

        if record:
            user_role = record[0]

            return user_role
        
        return None
    
    def check_role(self, session_id, required_role) -> bool:
        username = self.session_manager.find_user(session_id)

        if (user_role := self.get_user_role(username)) != None:

            return user_role <= required_role
        else:
            return False

    def generate_session(self, username):
        return self.session_manager.generate_session_id(username)

    def check_session(self, session_id):
        return self.session_manager.is_session_valid(session_id)
    

    def get_users(self):
        return self.users_manager.get_users()


    def remove_user(self, username):

        if user_role := self.get_user_role(username):

            if user_role != 0:
                self.users_manager.delete_user(username)

                return True    
        
        return False