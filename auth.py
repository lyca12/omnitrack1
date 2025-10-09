# database.py

import psycopg2  # Assuming you're using psycopg2 for PostgreSQL, adjust for your DB
from typing import Optional, Dict

class DatabaseManager:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def get_user(self, username: str) -> Optional[Dict]:
        """Retrieve a user from the database by username"""
        try:
            query = "SELECT * FROM users WHERE username = %s"
            cursor = self.db_connection.cursor()
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            cursor.close()
            
            if user:
                return {
                    'id': user[0],  # Assuming 'id' is the first column in your schema
                    'username': user[1],  # Assuming 'username' is the second column
                    'password_hash': user[2],  # Assuming 'password_hash' is the third column
                    'role': user[3],  # Assuming 'role' is the fourth column
                    'created_at': user[4]  # Assuming 'created_at' is the fifth column
                }
            return None
        except Exception as e:
            print(f"Error retrieving user {username}: {e}")
            return None

    def create_user(self, username: str, password_hash: str, role: str) -> bool:
        """Create a new user in the database"""
        try:
            query = "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)"
            cursor = self.db_connection.cursor()
            cursor.execute(query, (username, password_hash, role))
            self.db_connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error creating user {username}: {e}")
            return False
