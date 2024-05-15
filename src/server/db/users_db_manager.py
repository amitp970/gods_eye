"""
This module defines a UsersDbManager class that handles user-related database operations using the DatabaseManager.

Imports:
    - .database_manager.db_manager: Instance of DatabaseManager for executing database operations.
"""

from .database_manager import db_manager

class UsersDbManager:
    """
    A class to manage user-related database operations.
    """

    def __init__(self):
        """
        Initializes the UsersDbManager and ensures the users table exists.
        """
        self.db_manager = db_manager
        self.initialize_users_table()

    def initialize_users_table(self):
        """
        Creates the users table if it doesn't exist.
        """
        self.db_manager.execute_update('''CREATE TABLE IF NOT EXISTS users (
                            username TEXT PRIMARY KEY,
                            password TEXT NOT NULL, role INTEGER NOT NULL)''')
    
    def get_user_password(self, username):
        """
        Retrieves the password for the given username.

        Args:
            username (str): The username to look up.

        Returns:
            tuple: The password associated with the username, or None if not found.
        """
        return self.db_manager.execute_query_one("SELECT password FROM users WHERE username = ?", (username,))
    
    def insert_user(self, username, password, role):
        """
        Inserts a new user into the users table.

        Args:
            username (str): The username.
            password (str): The password.
            role (int): The role of the user.
        """
        self.db_manager.execute_update("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                                        (username, password, role))
        
    def get_user_role(self, username):
        """
        Retrieves the role for the given username.

        Args:
            username (str): The username to look up.

        Returns:
            tuple: The role associated with the username, or None if not found.
        """
        return self.db_manager.execute_query_one("SELECT role FROM users WHERE username = ?", (username,))
    
    def delete_user(self, username):
        """
        Deletes a user from the users table.

        Args:
            username (str): The username of the user to delete.
        """
        self.db_manager.execute_update("DELETE FROM users WHERE username = ?", (username,))

    def get_users(self):
        """
        Retrieves all users from the users table.

        Returns:
            list: A list of all usernames and their roles.
        """
        return self.db_manager.execute_query_all("SELECT username, role FROM users")
