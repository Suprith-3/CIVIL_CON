from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
import bcrypt
import logging
from config import Config, supabase
from utils.storage import upload_file_to_supabase
from extensions import limiter

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

# Allowed user types
VALID_USER_TYPES = ['user', 'worker', 'engineer', 'shopkeeper', 'admin']

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("3 per minute")  # Strict registration limit
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
        
        # Hash password - Reduced rounds to 10 for balancing speed (<250ms target) and security
        salt = bcrypt.gensalt(rounds=10)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        user_id = None
        
        # 1. Insert into base 'users' table
        new_user = {
            'email': email,
            'password_hash': hashed,
            'user_type': user_type,
            'is_active': True
        }
        
        # Add basic profile info for generic 'user' (customer)
        if user_type == 'user':
            new_user.update({
                'full_name': data.get('name') or data.get('full_name'),
                'contact_number': data.get('phone') or data.get('contact_number'),
                'location': {
                    'address': data.get('address'),
                    'lat': data.get('lat'),
                    'lng': data.get('lng')
                }
            })
        
        if not supabase:
            logger.error("Supabase client is not initialized. Check environment variables.")
            return jsonify({'error': 'Configuration Error', 'message': 'Database connection is missing. Please contact administrator.'}), 500

        try:
            res = supabase.table('users').insert(new_user).execute()
            if not res.data:
                logger.error(f"Supabase Insert Error: No data returned. Response: {res}")
                raise Exception("Failed to create user account record in database.")
            user_id = res.data[0]['id']
        except Exception as db_err:
            logger.error(f"Database insertion failed: {str(db_err)}")
            return jsonify({'error': 'Database Error', 'message': f'Failed to create user: {str(db_err)}'}), 500
        # 2. Insert into specialized registration table based on role
        try:
            def safe_float(val, default=0.0):
                try: 
                    return float(val) if val and str(val).strip() else default
                except: 
                    return default

            logger.info(f"Processing specialized registration for: {user_type}")

            if user_type == 'engineer':
                # Save certificates to Supabase Storage (documents bucket)
                docs = {}
                for field in ['comp_cert', 'civil_cert', 'aadhar']:
                    file = request.files.get(field)
                    url = upload_file_to_supabase(file, 'documents')
                    docs[field] = url if url else "not_provided"

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
                # Save Aadhar to Supabase Storage (documents bucket)
                file = request.files.get('aadhar')
                aadhar_url = upload_file_to_supabase(file, 'documents') or "not_provided"

                reg_data = {
                    'user_id': user_id,
                    'name': data.get('name', 'New Worker'),
                    'phone': data.get('phone', ''),
                    'work_type': data.get('work_type', 'General'),
                    'daily_wages': safe_float(data.get('daily_wages'), 0.0),
                    'location': {
                        'address': data.get('address', 'Not set'),
                        'lat': safe_float(data.get('lat'), 12.9716),
                        'lng': safe_float(data.get('lng'), 77.5946)
                    },
                    'status': 'pending',
                    'aadhar_image_url': aadhar_url
                }
                supabase.table('worker_registrations').insert(reg_data).execute()
                
            elif user_type == 'shopkeeper':
                # Save Shopkeeper documents to Supabase Storage (documents bucket for GST, media for photo)
                docs = {}
                docs['gst_doc'] = upload_file_to_supabase(request.files.get('gst_doc'), 'documents') or "not_provided"
                docs['shop_photo'] = upload_file_to_supabase(request.files.get('shop_photo'), 'media') or "not_provided"

                reg_data = {
                    'user_id': user_id,
                    'name': data.get('name', 'New shopkeeper'),
                    'shop_name': data.get('shop_name', ''),
                    'phone': data.get('phone', ''),
                    'shop_location': {
                        'address': data.get('address', 'Not set'),
                        'lat': safe_float(data.get('lat')),
                        'lng': safe_float(data.get('lng'))
                    },
                    'status': 'pending',
                    'gst_doc': docs['gst_doc'],
                    'shop_photo': docs['shop_photo']
                }
                supabase.table('shopkeeper_registrations').insert(reg_data).execute()

            elif user_type == 'renter':
                # Save Renter verification to Supabase Storage (documents bucket)
                file = request.files.get('verification_doc')
                doc_url = upload_file_to_supabase(file, 'documents') or "not_provided"

                reg_data = {
                    'user_id': user_id,
                    'name': data.get('full_name') or data.get('name', 'New Renter'),
                    'phone': data.get('phone', ''),
                    'email': email,
                    'status': 'pending',
                    'verification_doc_url': doc_url,
                    'location': {
                        'lat': safe_float(data.get('lat')),
                        'lng': safe_float(data.get('lng')),
                        'manual_address': data.get('manual_address')
                    }
                }
                supabase.table('renter_registrations').insert(reg_data).execute()

            logger.info(f"Specialized registration completed for: {user_type}")
        except Exception as e:
            logger.error(f"Specialized registration failed for {user_type}: {str(e)}")
            # Even if specialized insert fails, the user was created. 
            return jsonify({
                'error': 'Registration Partial Failure', 
                'message': f'Basic account created but details failed: {str(e)}',
                'debug_info': f"Role: {user_type}, UserID: {user_id}"
            }), 500

        return jsonify({
            'message': 'Registration submitted for review',
            'user': {'email': email, 'user_type': user_type}
        }), 201
        
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # Brute force protection
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Bad Request', 'message': 'Missing JSON data'}), 400
        
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Bad Request', 'message': 'Missing email or password'}), 400

    # Admin check (Rock solid check)
    from config import Config
    if email.lower() == Config.ADMIN_EMAIL.lower() and password == Config.ADMIN_PASSWORD:
        logger.info(f"Admin login attempt successful for: {email}")
        admin_ident = {'id': 'admin-0', 'email': email, 'user_type': 'admin', 'full_name': 'Super Admin'}
        access_token = create_access_token(identity='admin-0')
        refresh_token = create_refresh_token(identity='admin-0')
        return jsonify({
            'message': 'Admin login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': admin_ident
        }), 200

    try:
        user_data = None
        if supabase:
            # 1. Fetch user from db
            res = supabase.table('users').select('*').eq('email', email).execute()
            if not res.data:
                return jsonify({'error': 'Unauthorized', 'message': 'Invalid credentials'}), 401
            
            user_data = res.data[0]
            
            # 2. Verify password (BCrypt is the main lag, but essential)
            if not bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash'].encode('utf-8')):
                return jsonify({'error': 'Unauthorized', 'message': 'Invalid credentials'}), 401
            
            # 3. Check approval status for roles that require it
            role = user_data['user_type']
            if role in ['engineer', 'worker', 'shopkeeper']:
                table_map = {
                    'engineer': 'engineer_registrations',
                    'worker': 'worker_registrations',
                    'shopkeeper': 'shopkeeper_registrations'
                }
                # Combined lookup for status
                status_res = supabase.table(table_map[role]).select('status').eq('user_id', user_data['id']).single().execute()
                
                if status_res.data:
                    if status_res.data.get('status') != 'approved':
                        return jsonify({
                            'error': 'Forbidden', 
                            'message': f'Your {role} account is still pending approval.'
                        }), 403

        # 4. Bundle basic profile info into login response to speed up dashboard loading
        if not user_data:
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid credentials or database error'}), 401
            
        user_info = {
            'id': user_data['id'],
            'email': user_data['email'],
            'user_type': user_data['user_type'],
            'full_name': user_data.get('full_name'),
            'profile_pic_url': user_data.get('profile_pic_url')
        }
            
        access_token = create_access_token(identity=user_data['id'])
        refresh_token = create_refresh_token(identity=user_data['id'])
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_info
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

@auth_bp.route('/messages', methods=['GET'])
def get_messages():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    try:
        res = supabase.table('messages').select('*').eq('recipient_id', user_id).order('created_at', desc=True).execute()
        return jsonify({'messages': res.data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/messages/read', methods=['POST'])
def mark_messages_read():
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    try:
        supabase.table('messages').update({'is_read': True}).eq('recipient_id', user_id).execute()
        return jsonify({'message': 'Messages marked as read'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/status', methods=['GET'])
def get_status():
    # Try to get identity from JWT first
    user_id = None
    try:
        from flask_jwt_extended import decode_token
        auth_header = request.headers.get('Authorization')
        if auth_header and 'Bearer ' in auth_header:
            token = auth_header.split(' ')[1]
            decoded = decode_token(token)
            user_id = decoded['sub']
    except:
        pass
    
    # Fallback to query param
    if not user_id:
        user_id = request.args.get('user_id')
        
    if not user_id:
        return jsonify({'error': 'Missing identity'}), 401
    
    try:
        # Fetch user role from db
        user_res = supabase.table('users').select('user_type').eq('id', user_id).execute()
        if not user_res.data:
            return jsonify({'status': 'not_found'}), 404
            
        role = user_res.data[0]['user_type']
        
        table_map = {
            'engineer': 'engineer_registrations',
            'worker': 'worker_registrations',
            'shopkeeper': 'shopkeeper_registrations',
            'renter': 'renter_registrations'
        }
        
        if role not in table_map:
            return jsonify({'status': 'approved', 'role': role}), 200
            
        try:
            res = supabase.table(table_map[role]).select('status').eq('user_id', user_id).execute()
            if res.data:
                return jsonify({'status': res.data[0]['status'], 'role': role}), 200
        except:
            # Fallback for temporary db glitches
            return jsonify({'status': 'approved', 'role': role}), 200
            
        return jsonify({'status': 'not_found'}), 404
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        # If all fails, return a safe status to avoid 500 crashes
        return jsonify({'status': 'approved', 'role': 'user'}), 200

@auth_bp.route('/profile', methods=['GET'])
def get_user_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    try:
        # Select all fields including new map and gallery columns
        res = supabase.table('users').select('*').eq('id', user_id).execute()
        if res.data:
            return jsonify({'profile': res.data[0]}), 200
        return jsonify({'error': 'Not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['POST'])
def update_user_profile():
    import os
    from werkzeug.utils import secure_filename
    
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
        
    def safe_int(val):
        try: return int(val) if val and str(val).strip() else None
        except: return None
        
    def safe_float(val):
        try: return float(val) if val and str(val).strip() else None
        except: return None

    try:
        # Handle Photo Upload to Supabase Storage (media bucket)
        file = request.files.get('photo')
        profile_pic_url = upload_file_to_supabase(file, 'media')

        # Build update object
        update_data = {
            'full_name': request.form.get('name'),
            'age': safe_int(request.form.get('age')),
            'bio': request.form.get('bio'),
            'experience_years': safe_int(request.form.get('experience_years')),
            'completed_projects': safe_int(request.form.get('completed_projects')),
            'address': request.form.get('address'),
            'location': {
                'address': request.form.get('address'),
                'lat': safe_float(request.form.get('lat')),
                'lng': safe_float(request.form.get('lng'))
            }
        }
        
        if profile_pic_url:
            update_data['profile_pic_url'] = profile_pic_url

        supabase.table('users').update(update_data).eq('id', user_id).execute()
        return jsonify({'message': 'Profile updated successfully!'}), 200
        
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        return jsonify({'error': 'Database Error', 'message': str(e)}), 500

@auth_bp.route('/update-profile', methods=['POST'])
@jwt_required()
def update_profile():
    try:
        user_id = get_jwt_identity()
        
        # Handle Multi-part form data
        data = request.form.to_dict()
        
        # Handle Multiple Image Uploads
        import os
        from werkzeug.utils import secure_filename
        
        shop_image_urls = []
        files = request.files.getlist('shop_images')
        
        if files:
            for file in files:
                url = upload_file_to_supabase(file, 'media')
                if url: shop_image_urls.append(url)

        update_fields = {
            'full_name': data.get('name') or data.get('full_name'),
            'contact_number': data.get('contact_number') or data.get('phone'),
            'opening_hours': data.get('opening_hours'),
            'shop_address': data.get('shop_address') or data.get('address'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'bio': data.get('bio')
        }

        # If we uploaded new images, add them to the update
        if shop_image_urls:
            update_fields['shop_images'] = shop_image_urls

        # Remove keys that are None to avoid overwriting existing data with nulls
        update_fields = {k: v for k, v in update_fields.items() if v is not None}

        if supabase:
            supabase.table('users').update(update_fields).eq('id', user_id).execute()
            return jsonify({'success': True, 'message': 'Profile and Gallery updated!'}), 200
        else:
            raise Exception("Database connection not available")

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/all-shops', methods=['GET'])
def get_all_shops():
    try:
        # Fetch only shopkeepers with valid map locations
        res = supabase.table('users')\
            .select('id, full_name, latitude, longitude, shop_address, shop_images, opening_hours')\
            .eq('user_type', 'shopkeeper')\
            .not_.is_('latitude', 'null')\
            .execute()
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify-customer', methods=['POST'])
def verify_customer():
    user_id = request.form.get('user_id')
    aadhar = request.files.get('aadhar_file')
    dl = request.files.get('dl_file')
    
    if not (user_id and aadhar and dl):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Save verification documents to Supabase Storage (documents bucket)
        aadhar_url = upload_file_to_supabase(aadhar, 'documents')
        dl_url = upload_file_to_supabase(dl, 'documents')

        # Update user record
        supabase.table('users').update({
            'is_id_verified': False, 
            'aadhar_url': aadhar_url,
            'dl_url': dl_url,
            'verification_status': 'pending'
        }).eq('id', user_id).execute()

        return jsonify({'message': 'Documents uploaded successfully. Admin review pending.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
