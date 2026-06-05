import os
from functools import wraps
from flask import request, jsonify

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Simple token-based check
        admin_token = os.environ.get('ADMIN_BACKUP_TOKEN', 'super_secret_admin_token')
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'Unauthorized', 'message': 'Missing Authorization Header'}), 401
            
        # Check if it starts with 'Bearer ' or is just the token
        token = auth_header.split(" ")[1] if " " in auth_header else auth_header
        
        if token != admin_token:
            return jsonify({'error': 'Forbidden', 'message': 'Invalid Admin Token'}), 403
            
        return f(*args, **kwargs)
    return decorated_function
