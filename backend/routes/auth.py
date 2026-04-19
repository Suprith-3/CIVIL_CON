from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
import bcrypt
import logging
from config import supabase

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

# Allowed user types
VALID_USER_TYPES = ['user', 'worker', 'engineer', 'shopkeeper', 'admin']

@auth_bp.route('/register', methods=['POST'])
def register():
    # Handle both JSON and Multipart Form Data (for files)
    if request.is_json:
        data = request.get_json()
    else:
        # Include both form fields and files
        data = request.form.to_dict()
        
    if not data:
        return jsonify({'error': 'Bad Request', 'message': 'No registration data received'}), 400
        
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('user_type')
    
    if not email or not password or not user_type:
        return jsonify({'error': 'Bad Request', 'message': 'Missing email, password, or user_type'}), 400
        
    try:
        # Check if user already exists
        if supabase:
            existing = supabase.table('users').select('*').eq('email', email).execute()
            if existing.data:
                return jsonify({'error': 'Conflict', 'message': 'User already exists'}), 409
        
        # Hash password
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        # 1. Insert into base 'users' table
        new_user = {
            'email': email,
            'password_hash': hashed,
            'user_type': user_type,
            'is_active': True
        }
        
        if supabase:
            res = supabase.table('users').insert(new_user).execute()
            if not res.data:
                raise Exception("Failed to create user account")
            user_id = res.data[0]['id']
            
            # 2. Insert into specialized registration table based on role
            if user_type == 'engineer':
                # Handle File Saving
                import os
                from werkzeug.utils import secure_filename
                
                upload_folder = os.path.join(os.getcwd(), 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)

                # Save certificates
                docs = {}
                for field in ['comp_cert', 'civil_cert', 'aadhar']:
                    file = request.files.get(field)
                    if file and file.filename:
                        filename = secure_filename(f"{user_id}_{field}_{file.filename}")
                        file.save(os.path.join(upload_folder, filename))
                        docs[field] = f"/uploads/{filename}"
                    else:
                        docs[field] = "not_provided"

                reg_data = {
                    'user_id': user_id,
                    'name': data.get('name', 'New Engineer'),
                    'phone': data.get('phone', ''),
                    'status': 'pending',
                    'aadhar_image_url': docs['aadhar'],
                    'civil_eng_cert_url': docs['civil_cert'],
                    'completion_cert_url': docs['comp_cert']
                }
                supabase.table('engineer_registrations').insert(reg_data).execute()
                
            elif user_type == 'worker':
                # Handle File Saving for Worker
                import os
                from werkzeug.utils import secure_filename
                
                upload_folder = os.path.join(os.getcwd(), 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)

                # Save Aadhar
                aadhar_url = "not_provided"
                file = request.files.get('aadhar')
                if file and file.filename:
                    filename = secure_filename(f"{user_id}_aadhar_{file.filename}")
                    file.save(os.path.join(upload_folder, filename))
                    aadhar_url = f"/uploads/{filename}"

                reg_data = {
                    'user_id': user_id,
                    'name': data.get('name', 'New Worker'),
                    'phone': data.get('phone', ''),
                    'work_type': data.get('work_type', 'General'),
                    'daily_wages': data.get('daily_wages', 0),
                    'location': {
                        'address': data.get('address', 'Not set'),
                        'lat': data.get('lat', 12.9716),
                        'lng': data.get('lng', 77.5946)
                    },
                    'status': 'pending',
                    'aadhar_image_url': aadhar_url
                }
                supabase.table('worker_registrations').insert(reg_data).execute()
                
            elif user_type == 'shopkeeper':
                reg_data = {
                    'user_id': user_id,
                    'name': data.get('name', 'New shopkeeper'),
                    'phone': data.get('phone', ''),
                    'shop_location': {'address': data.get('address', 'Not set')},
                    'status': 'pending'
                }
                supabase.table('shopkeeper_registrations').insert(reg_data).execute()

        return jsonify({
            'message': 'Registration submitted for review',
            'user': {'email': email, 'user_type': user_type}
        }), 201
        
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Bad Request', 'message': 'Missing JSON data'}), 400
        
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Bad Request', 'message': 'Missing email or password'}), 400

    # Hardcoded ADMIN check
    if email == 'supreethm763@gmail.com' and password == '9742446286':
        admin_ident = {'id': 'admin-0', 'email': email, 'user_type': 'admin'}
        access_token = create_access_token(identity=admin_ident)
        refresh_token = create_refresh_token(identity=admin_ident)
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': admin_ident
        }), 200

    try:
        user_data = None
        if supabase:
            # Fetch user from db
            res = supabase.table('users').select('*').eq('email', email).execute()
            if not res.data:
                return jsonify({'error': 'Unauthorized', 'message': 'Invalid credentials'}), 401
            
            user_data = res.data[0]
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash'].encode('utf-8')):
                return jsonify({'error': 'Unauthorized', 'message': 'Invalid credentials'}), 401
            
            # Check approval status for roles that require it
            role = user_data['user_type']
            if role in ['engineer', 'worker', 'shopkeeper']:
                table_map = {
                    'engineer': 'engineer_registrations',
                    'worker': 'worker_registrations',
                    'shopkeeper': 'shopkeeper_registrations'
                }
                status_res = supabase.table(table_map[role]).select('status').eq('user_id', user_data['id']).execute()
                
                if status_res.data:
                    status = status_res.data[0].get('status', 'pending')
                    if status != 'approved':
                        return jsonify({
                            'error': 'Forbidden', 
                            'message': f'Your {role} account is still pending approval by admin.'
                        }), 403

            ident = {
                'id': user_data['id'],
                'email': user_data['email'],
                'user_type': user_data['user_type']
            }
        else:
            logger.warning("Supabase not configured. Mocking login failure.")
            return jsonify({'error': 'Internal Error', 'message': 'Database not configured'}), 500
            
        access_token = create_access_token(identity=ident)
        refresh_token = create_refresh_token(identity=ident)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user_data['id'],
                'email': user_data['email'],
                'user_type': user_data['user_type']
            }
        }), 200

    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({
        'access_token': access_token
    }), 200

@auth_bp.route('/status', methods=['GET'])
@jwt_required()
def get_status():
    user = get_jwt_identity()
    user_id = user['id']
    role = user['user_type']
    
    table_map = {
        'engineer': 'engineer_registrations',
        'worker': 'worker_registrations',
        'shopkeeper': 'shopkeeper_registrations'
    }
    
    if role not in table_map:
        return jsonify({'status': 'approved'}), 200 # Admin/Users are implicitly approved
        
    try:
        res = supabase.table(table_map[role]).select('status').eq('user_id', user_id).execute()
        if res.data:
            return jsonify({'status': res.data[0]['status']}), 200
        return jsonify({'status': 'not_found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    current_user = get_jwt_identity()
    return jsonify({
        'user': current_user
    }), 200
