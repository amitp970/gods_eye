import sqlite3

class DatabaseManager:
    def __init__(self, db_path=r"./src/server/db/server_db.db"):
        self.db_path = db_path

    def __create_connection(self):
        """Create a database connection to the SQLite database specified by DB_FILE."""
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            print(e)
        return None

    def execute_query_all(self, query, params=()):
        with self.__create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        
    def execute_query_one(self, query, params=()):
        with self.__create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()


    def execute_update(self, query, params=()):
        with self.__create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()