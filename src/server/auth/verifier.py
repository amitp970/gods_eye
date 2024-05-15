"""
This module defines a Verifier class that handles user authentication, session management, and role-based access control.

Imports:
    - bcrypt: Library for hashing passwords.
    - src.server.db.users_db_manager.UsersDbManager: Custom module to manage user data in the database.
    - .session_manager.SessionManager: Custom module to manage user sessions.
"""

import bcrypt

from src.server.db.users_db_manager import UsersDbManager
from .session_manager import SessionManager

class Verifier:
    """
    A class to handle user authentication, session management, and role-based access control.
    """
    def __init__(self):
        """
        Initializes the Verifier with a UsersDbManager and a SessionManager.
        """
        self.users_manager = UsersDbManager()
        self.session_manager = SessionManager()
    
    def add_user(self, username, password, role=1):
        """
        Adds a new user to the database.

        Args:
            username (str): The username of the new user.
            password (str): The password of the new user.
            role (int): The role of the new user. Defaults to 1.

        Returns:
            tuple: A tuple containing a boolean indicating success and a message.
        """
        # Check if user exists
        record = self.users_manager.get_user_password(username)

        if not record:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            self.users_manager.insert_user(username, hashed_password.decode(), role)
            return True, "Success: User added"
        else:
            return False, "Failed: username already exists"
    
    def check_password(self, username, password):
        """
        Checks if the provided password matches the stored password for the given username.

        Args:
            username (str): The username to check.
            password (str): The password to check.

        Returns:
            tuple: A tuple containing a boolean indicating if the password is correct and a message.
        """
        record = self.users_manager.get_user_password(username)

        if record:
            stored_password = record[0]
            is_verified = bcrypt.checkpw(password=password.encode('utf-8'), 
                                         hashed_password=stored_password.encode('utf-8'))
        else:
            return False, "Failed: username doesn't exists"
                    
        return is_verified, username
    
    def get_user_role(self, username):
        """
        Retrieves the role of the specified user.

        Args:
            username (str): The username whose role is to be retrieved.

        Returns:
            int: The role of the user, or None if the user does not exist.
        """
        record = self.users_manager.get_user_role(username)

        if record:
            user_role = record[0]
            return user_role
        
        return None
    
    def check_role(self, session_id, required_role) -> bool:
        """
        Checks if the user associated with the session has the required role.

        Args:
            session_id (str): The session ID of the user.
            required_role (int): The required role.

        Returns:
            bool: True if the user has the required role, False otherwise.
        """
        username = self.session_manager.find_user(session_id)

        if (user_role := self.get_user_role(username)) != None:
            return user_role <= required_role
        else:
            return False

    def generate_session(self, username):
        """
        Generates a new session ID for the specified user.

        Args:
            username (str): The username for which to generate a session ID.

        Returns:
            str: The generated session ID.
        """
        return self.session_manager.generate_session_id(username)

    def check_session(self, session_id):
        """
        Checks if the session ID is valid.

        Args:
            session_id (str): The session ID to check.

        Returns:
            bool: True if the session is valid, False otherwise.
        """
        return self.session_manager.is_session_valid(session_id)

    def get_users(self):
        """
        Retrieves all users from the database.

        Returns:
            list: A list of all users.
        """
        return self.users_manager.get_users()

    def remove_user(self, username):
        """
        Removes a user from the database if they are not an admin.

        Args:
            username (str): The username of the user to remove.

        Returns:
            bool: True if the user was removed, False otherwise.
        """
        if user_role := self.get_user_role(username):
            if user_role != 0:
                self.users_manager.delete_user(username)
                return True    
        
        return False
