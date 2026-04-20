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
        
        # Add basic profile info for generic 'user' (customer)
        if user_type == 'user':
            new_user.update({
                'full_name': data.get('name'),
                'contact_number': data.get('phone'),
                'location': {
                    'address': data.get('address'),
                    'lat': data.get('lat'),
                    'lng': data.get('lng')
                }
            })
        
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
                # Handle File Saving for Shopkeeper
                import os
                from werkzeug.utils import secure_filename
                
                upload_folder = os.path.join(os.getcwd(), 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)

                docs = {}
                for field in ['gst_doc', 'shop_photo']:
                    file = request.files.get(field)
                    if file and file.filename:
                        filename = secure_filename(f"{user_id}_{field}_{file.filename}")
                        file.save(os.path.join(upload_folder, filename))
                        docs[field] = f"/uploads/{filename}"
                    else:
                        docs[field] = "not_provided"

                reg_data = {
                    'user_id': user_id,
                    'name': data.get('name', 'New shopkeeper'),
                    'shop_name': data.get('shop_name', ''),
                    'phone': data.get('phone', ''),
                    'shop_location': {
                        'address': data.get('address', 'Not set'),
                        'lat': data.get('lat'),
                        'lng': data.get('lng')
                    },
                    'status': 'pending',
                    'gst_doc': docs['gst_doc'],
                    'shop_photo': docs['shop_photo']
                }
                supabase.table('shopkeeper_registrations').insert(reg_data).execute()

            elif user_type == 'renter':
                # Handle File Saving for Renter
                import os
                from werkzeug.utils import secure_filename
                
                upload_folder = os.path.join(os.getcwd(), 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)

                doc_url = "not_provided"
                file = request.files.get('verification_doc')
                if file and file.filename:
                    filename = secure_filename(f"{user_id}_renter_doc_{file.filename}")
                    file.save(os.path.join(upload_folder, filename))
                    doc_url = f"/uploads/{filename}"

                reg_data = {
                    'user_id': user_id,
                    'name': data.get('full_name', 'New Renter'),
                    'phone': data.get('phone', ''),
                    'email': email,
                    'status': 'pending',
                    'verification_doc_url': doc_url,
                    'location': {
                        'lat': data.get('lat'),
                        'lng': data.get('lng'),
                        'manual_address': data.get('manual_address')
                    }
                }
                supabase.table('renter_registrations').insert(reg_data).execute()

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
                    'shopkeeper': 'shopkeeper_registrations',
                    'renter': 'renter_registrations'
                }
                status_res = supabase.table(table_map[role]).select('status').eq('user_id', user_data['id']).execute()
                
                if status_res.data:
                    status = status_res.data[0].get('status', 'pending')
                    if status != 'approved':
                        return jsonify({
                            'error': 'Forbidden', 
                            'message': f'Your {role} account is still pending approval by admin.'
                        }), 403

        ident = user_data['id']
            
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
        # Handle Photo Upload
        profile_pic_url = None
        file = request.files.get('photo')
        if file and file.filename:
            upload_folder = os.path.join(os.getcwd(), 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            filename = secure_filename(f"user_{user_id}_{file.filename}")
            file.save(os.path.join(upload_folder, filename))
            profile_pic_url = f"/uploads/{filename}"

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
            upload_folder = os.path.join(os.getcwd(), 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            for file in files:
                if file and file.filename:
                    filename = secure_filename(f"shop_{user_id}_{os.urandom(4).hex()}_{file.filename}")
                    file.save(os.path.join(upload_folder, filename))
                    shop_image_urls.append(f"/uploads/{filename}")

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
        import os
        upload_folder = os.path.join(os.getcwd(), 'uploads', 'verifications')
        if not os.path.exists(upload_folder): os.makedirs(upload_folder)
        
        a_path = os.path.join(upload_folder, f"aadhar_{user_id}_{aadhar.filename}")
        d_path = os.path.join(upload_folder, f"dl_{user_id}_{dl.filename}")
        
        aadhar.save(a_path)
        dl.save(d_path)

        # Update user record
        supabase.table('users').update({
            'is_id_verified': False, 
            'aadhar_url': f"/uploads/verifications/{os.path.basename(a_path)}",
            'dl_url': f"/uploads/verifications/{os.path.basename(d_path)}",
            'verification_status': 'pending'
        }).eq('id', user_id).execute()

        return jsonify({'message': 'Documents uploaded successfully. Admin review pending.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
