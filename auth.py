import bcrypt
import os
from typing import Optional, Dict
from database import DatabaseManager

class AuthManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.session_secret = os.getenv('SESSION_SECRET', 'default_secret_key')
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def register_user(self, username: str, password: str, role: str = 'customer') -> bool:
        """Register a new user"""
        if not username or not password:
            return False
        
        # Check if username already exists
        if self.db.get_user(username):
            return False
        
        hashed_password = self.hash_password(password)
        return self.db.create_user(username, hashed_password, role)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate a user and return user data"""
        if not username or not password:
            return None
        
        # Handle demo accounts
        if username.endswith('_demo'):
            role = username.replace('_demo', '')
            if role in ['admin', 'staff', 'customer']:
                return {
                    'id': 0,
                    'username': username,
                    'role': role,
                    'created_at': '2024-01-01 00:00:00'
                }
            return None
        
        user = self.db.get_user(username)
        if not user:
            return None
        
        if self.verify_password(password, user['password_hash']):
            return {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'created_at': user['created_at']
            }
        
        return None
    
    def create_admin_user(self, username: str, password: str) -> bool:
        """Create an admin user"""
        return self.register_user(username, password, 'admin')
    
    def create_staff_user(self, username: str, password: str) -> bool:
        """Create a staff user"""
        return self.register_user(username, password, 'staff')
