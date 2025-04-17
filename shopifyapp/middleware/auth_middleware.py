from functools import wraps
from flask import request, jsonify, g
from ..services.auth_service import AuthService
from ..models.user import User

def token_required(f):
    """Decorator to protect routes with JWT authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = AuthService.verify_token(token)
        
        if user_id is None:
            return jsonify({'error': 'Invalid or expired token'}), 401
            
        # Get user from database
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        if not user.is_active:
            return jsonify({'error': 'User account is inactive'}), 401
            
        # Store user in flask.g for route handlers
        g.user = user
        return f(*args, **kwargs)
        
    return decorated

def admin_required(f):
    """Decorator to protect admin-only routes."""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if not g.user.is_admin:
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
        
    return decorated 