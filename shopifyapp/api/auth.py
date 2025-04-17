from flask import Blueprint, request, jsonify
from shopifyapp.services.auth_service import AuthService
from shopifyapp.models.user import User
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def validate_auth_input(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        if not isinstance(email, str) or not isinstance(password, str):
            return jsonify({'error': 'Invalid input type'}), 400

        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/register', methods=['POST'])
@validate_auth_input
def register():
    data = request.get_json()
    response, status_code = AuthService.register_user(
        email=data['email'],
        password=data['password'],
        first_name=data.get('first_name'),
        last_name=data.get('last_name')
    )
    return jsonify(response), status_code

@auth_bp.route('/login', methods=['POST'])
@validate_auth_input
def login():
    data = request.get_json()
    response, status_code = AuthService.login_user(
        email=data['email'],
        password=data['password']
    )
    return jsonify(response), status_code

# Authentication middleware
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header:
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        user = AuthService.verify_token(token)
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401

        return f(user, *args, **kwargs)
    return decorated 