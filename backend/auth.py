"""
Authentication and User Management Module
Handles user registration, login, password hashing, and JWT tokens
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
import mysql.connector
from mysql.connector import Error


class AuthManager:
    """Manages user authentication and authorization"""
    
    def __init__(self, database):
        self.db = database
        self.jwt_secret = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        self.access_token_expires = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))
    
    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """
        Register a new user
        
        Args:
            username: Unique username
            email: User email address
            password: Plain text password (will be hashed)
        
        Returns:
            Dict with user_id and success status
        
        Raises:
            ValueError: If username or email already exists
        """
        try:
            # Check if username exists
            existing_user = self.db.execute_query(
                "SELECT id FROM users WHERE username = %s",
                (username,),
                fetch=True
            )
            if existing_user:
                raise ValueError('Username already exists')
            
            # Check if email exists
            existing_email = self.db.execute_query(
                "SELECT id FROM users WHERE email = %s",
                (email,),
                fetch=True
            )
            if existing_email:
                raise ValueError('Email already exists')
            
            # Hash password
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            
            # Insert user
            query = """
                INSERT INTO users (username, email, password_hash, created_at)
                VALUES (%s, %s, %s, NOW())
            """
            self.db.execute_query(query, (username, email, password_hash), fetch=False)
            
            # Get the inserted user ID
            user = self.db.execute_query(
                "SELECT id, username, email, created_at, profile_pic, bio FROM users WHERE username = %s",
                (username,),
                fetch=True
            )
            
            if user:
                return {
                    'success': True,
                    'user_id': user[0]['id'],
                    'username': user[0]['username'],
                    'email': user[0]['email']
                }
            else:
                raise Exception('Failed to retrieve created user')
                
        except Error as e:
            print(f"Database error during registration: {e}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user credentials
        
        Args:
            username: Username
            password: Plain text password
        
        Returns:
            User dict if authentication successful, None otherwise
        """
        try:
            query = """
                SELECT id, username, email, password_hash, created_at, last_login, role, profile_pic, bio, suspended_until
                FROM users
                WHERE username = %s
            """
            result = self.db.execute_query(query, (username,), fetch=True)
            
            if not result:
                return None
            
            user = result[0]
            
            # Verify password
            if check_password_hash(user['password_hash'], password):
                # Update last login
                self.db.execute_query(
                    "UPDATE users SET last_login = NOW() WHERE id = %s",
                    (user['id'],),
                    fetch=False
                )
                
                # Remove password hash from returned data
                user.pop('password_hash', None)
                return user
            
            return None
            
        except Error as e:
            print(f"Database error during authentication: {e}")
            return None
    
    def generate_tokens(self, user_id: int, username: str) -> Dict[str, str]:
        """
        Generate JWT access and refresh tokens
        
        Args:
            user_id: User ID
            username: Username
        
        Returns:
            Dict with access_token and refresh_token
        """
        # Use username as identity (string) - simpler and more compatible
        identity = username
        
        access_token = create_access_token(
            identity=identity,
            expires_delta=timedelta(seconds=self.access_token_expires)
        )
        
        refresh_token = create_refresh_token(
            identity=identity,
            expires_delta=timedelta(days=30)
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': self.access_token_expires
        }
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information by ID"""
        try:
            query = """
                SELECT id, username, email, created_at, last_login, role, profile_pic, bio, suspended_until
                FROM users
                WHERE id = %s
            """
            result = self.db.execute_query(query, (user_id,), fetch=True)
            return result[0] if result else None
        except Error as e:
            print(f"Error fetching user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information by username"""
        try:
            query = """
                SELECT id, username, email, created_at, last_login, role, profile_pic, bio, suspended_until
                FROM users
                WHERE username = %s
            """
            result = self.db.execute_query(query, (username,), fetch=True)
            return result[0] if result else None
        except Error as e:
            print(f"Error fetching user: {e}")
            return None
    
    def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """Update user dietary preferences and restrictions"""
        try:
            query = """
                UPDATE users
                SET dietary_preferences = %s, allergies = %s
                WHERE id = %s
            """
            dietary_prefs = preferences.get('dietary_preferences', [])
            allergies = preferences.get('allergies', [])
            
            # Convert lists to JSON strings
            import json
            self.db.execute_query(
                query,
                (json.dumps(dietary_prefs), json.dumps(allergies), user_id),
                fetch=False
            )
            return True
        except Error as e:
            print(f"Error updating preferences: {e}")
            return False
    
    def save_user_favorite(self, user_id: int, recipe_id: int) -> bool:
        """Save a recipe to user's favorites"""
        try:
            query = """
                INSERT INTO user_favorites (user_id, recipe_id, created_at)
                VALUES (%s, %s, NOW())
                ON DUPLICATE KEY UPDATE created_at = NOW()
            """
            self.db.execute_query(query, (user_id, recipe_id), fetch=False)
            return True
        except Error as e:
            print(f"Error saving favorite: {e}")
            return False
    
    def remove_user_favorite(self, user_id: int, recipe_id: int) -> bool:
        """Remove a recipe from user's favorites"""
        try:
            query = "DELETE FROM user_favorites WHERE user_id = %s AND recipe_id = %s"
            self.db.execute_query(query, (user_id, recipe_id), fetch=False)
            return True
        except Error as e:
            print(f"Error removing favorite: {e}")
            return False
    
    def get_user_favorites(self, user_id: int) -> list:
        """Get all favorite recipe IDs for a user"""
        try:
            query = """
                SELECT recipe_id, created_at
                FROM user_favorites
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            results = self.db.execute_query(query, (user_id,), fetch=True)
            return [r['recipe_id'] for r in results] if results else []
        except Error as e:
            print(f"Error fetching favorites: {e}")
            return []
