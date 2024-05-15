"""
This module defines a DatabaseManager class that handles basic database operations using SQLite.

Imports:
    - sqlite3: SQLite database module.
"""

import sqlite3

class DatabaseManager:
    """
    A class to manage basic database operations using SQLite.
    """

    def __init__(self, db_path=r"./src/server/db/server_db.db"):
        """
        Initializes the DatabaseManager with the given database path.

        Args:
            db_path (str): The file path to the SQLite database. Defaults to './src/server/db/server_db.db'.
        """
        self.db_path = db_path

    def __create_connection(self):
        """
        Creates a database connection to the SQLite database specified by db_path.

        Returns:
            sqlite3.Connection: The connection object or None if an error occurred.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            print(e)
        return None

    def execute_query_all(self, query, params=()):
        """
        Executes a query and fetches all results.

        Args:
            query (str): The SQL query to execute.
            params (tuple): The parameters to pass with the query. Defaults to an empty tuple.

        Returns:
            list: A list of all fetched results.
        """
        with self.__create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        
    def execute_query_one(self, query, params=()):
        """
        Executes a query and fetches one result.

        Args:
            query (str): The SQL query to execute.
            params (tuple): The parameters to pass with the query. Defaults to an empty tuple.

        Returns:
            tuple: The first fetched result or None if no result found.
        """
        with self.__create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()

    def execute_update(self, query, params=()):
        """
        Executes an update query (INSERT, UPDATE, DELETE).

        Args:
            query (str): The SQL query to execute.
            params (tuple): The parameters to pass with the query. Defaults to an empty tuple.
        """
        with self.__create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

# Create an instance of DatabaseManager
db_manager = DatabaseManager()
