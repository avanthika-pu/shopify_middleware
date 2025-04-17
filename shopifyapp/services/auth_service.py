from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import jwt
from ..models.user import User, db
from flask import current_app, request, jsonify
from functools import wraps

class AuthService:
    @staticmethod
    def register(email: str, password: str, first_name: str = None, last_name: str = None) -> Tuple[Dict, int]:
        """
        Register a new user.
        
        Args:
            email: User's email address
            password: User's password
            first_name: Optional first name
            last_name: Optional last name
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            # Check if user already exists
            if User.query.filter_by(email=email).first():
                return {'error': 'Email already registered'}, 400
            
            # Create new user
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Generate access token
            token = AuthService.generate_token(user.id)
            
            return {
                'message': 'User registered successfully',
                'token': token,
                'user': user.to_dict()
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    @staticmethod
    def login(email: str, password: str) -> Tuple[Dict, int]:
        """
        Authenticate a user and return a token.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            # Find user by email
            user = User.query.filter_by(email=email).first()
            
            if not user or not user.check_password(password):
                return {'error': 'Invalid email or password'}, 401
            
            if not user.is_active:
                return {'error': 'Account is inactive'}, 401
            
            # Generate access token
            token = AuthService.generate_token(user.id)
            
            return {
                'message': 'Login successful',
                'token': token,
                'user': user.to_dict()
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500

    @staticmethod
    def generate_token(user_id: int) -> str:
        """
        Generate a JWT token for the user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=1),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_token(token: str) -> Optional[int]:
        """
        Verify a JWT token and return the user ID.
        
        Args:
            token: JWT token string
            
        Returns:
            User ID if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            return payload['user_id']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

def auth_required(f):
    """
    Decorator to protect routes with JWT authentication.

    Parameters:
        f: Function to decorate

    Returns:
        Decorated function that checks for valid JWT token

    Usage:
        @auth_required
        def protected_route():
            pass
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
            
        try:
            # Decode token
            data = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=["HS256"]
            )
            
            # Get current user
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
                
            # Pass user to route
            return f(current_user, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
            
    return decorated 