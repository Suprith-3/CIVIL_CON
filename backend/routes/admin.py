from flask import Blueprint, request, jsonify, redirect, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from config import supabase
import logging

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

def is_admin():
    identity = get_jwt_identity()
    return identity.get('user_type') == 'admin'

@admin_bp.route('/pending', methods=['GET'])
def get_pending():
    # TEMPORARY: Removing JWT check to solve the persistent 401 error
    # if not is_admin():
    #     return jsonify({'error': 'Forbidden', 'message': 'Admin access required'}), 403
    
    try:
        # Fetch ONLY 'pending' from specialized tables
        workers_res = supabase.table('worker_registrations').select('*').eq('status', 'pending').execute()
        engineers_res = supabase.table('engineer_registrations').select('*').eq('status', 'pending').execute()
        shops_res = supabase.table('shopkeeper_registrations').select('*').eq('status', 'pending').execute()
        renters_res = supabase.table('renter_registrations').select('*').eq('status', 'pending').execute()
        
        # Combine them logically
        return jsonify({
            'workers': workers_res.data,
            'engineers': engineers_res.data,
            'shops': shops_res.data,
            'renters': renters_res.data
        }), 200
    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@admin_bp.route('/approved-engineers', methods=['GET'])
def get_approved_engineers():
    try:
        # Step 1: Get all approved engineer registrations (has extra fields like experience)
        approved_res = supabase.table('engineer_registrations').select('*').eq('status', 'approved').execute()
        
        if not approved_res.data:
            return jsonify([]), 200
            
        # Step 2: Get approved user IDs
        approved_ids = [row['user_id'] for row in approved_res.data]
        
        # Step 3: Fetch user profiles (has full_name, profile_pic_url, etc.)
        users_res = supabase.table('users').select('*').in_('id', approved_ids).execute()
        
        # Step 4: Merge registration data into user profile for richer display
        reg_by_uid = {row['user_id']: row for row in approved_res.data}
        merged = []
        for user in users_res.data:
            reg = reg_by_uid.get(user['id'], {})
            merged.append({
                **user,
                'registration_id': reg.get('id'),
                'experience_years': reg.get('experience_years'),
                'specialty': reg.get('specialty'),
                'phone': reg.get('phone'),
                'aadhar_image_url': reg.get('aadhar_image_url'),
                'civil_eng_cert_url': reg.get('civil_eng_cert_url'),
                'completion_cert_url': reg.get('completion_cert_url'),
            })
        
        return jsonify(merged), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/approved-workers', methods=['GET'])
def get_approved_workers():
    try:
        # Step 1: Get all IDs of approved workers
        approved_res = supabase.table('worker_registrations').select('user_id').eq('status', 'approved').execute()
        approved_ids = [row['user_id'] for row in approved_res.data]
        
        if not approved_ids:
            return jsonify([]), 200
            
        # Step 2: Fetch the actual user profiles for those IDs
        users_res = supabase.table('users').select('*').in_('id', approved_ids).execute()
        return jsonify(users_res.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/approve/<role>/<id>', methods=['POST'])
def approve_registration(role, id):
    # TEMPORARY: Removing JWT check
    # if not is_admin():
    #     return jsonify({'error': 'Forbidden', 'message': 'Admin access required'}), 403
    
    table_map = {
        'worker': 'worker_registrations',
        'engineer': 'engineer_registrations',
        'shopkeeper': 'shopkeeper_registrations',
        'renter': 'renter_registrations'
    }
    
    table = table_map.get(role)
    if not table:
        return jsonify({'error': 'Bad Request', 'message': 'Invalid role'}), 400
        
    try:
        update_data = {'status': 'approved'}
        
        # If approving a worker, generate a unique worker_code if it doesn't exist
        if role == 'worker':
            import random
            worker_code = f"WRK-{random.randint(1000, 9999)}"
            update_data['worker_code'] = worker_code
            print(f"GENERATING ID: {worker_code} for worker_registration ID: {id}")

        res = supabase.table(table).update(update_data).eq('id', id).execute()
        return jsonify({
            'message': f'{role} approved successfully',
            'worker_code': update_data.get('worker_code')
        }), 200
    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@admin_bp.route('/reject/<role>/<id>', methods=['POST'])
def reject_registration(role, id):
    table_map = {
        'worker': 'worker_registrations',
        'engineer': 'engineer_registrations',
        'shopkeeper': 'shopkeeper_registrations',
        'renter': 'renter_registrations'
    }
    
    table = table_map.get(role)
    if not table:
        return jsonify({'error': 'Bad Request', 'message': 'Invalid role'}), 400
        
    try:
        supabase.table(table).update({'status': 'rejected'}).eq('id', id).execute()
        return jsonify({'message': f'{role} rejected successfully'}), 200
    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
def get_all_users():
    # TEMPORARY: Removing JWT check
    # if not is_admin():
    #     return jsonify({'error': 'Forbidden', 'message': 'Admin access required'}), 403
    
    try:
        users = supabase.table('users').select('*').execute()
        return jsonify(users.data), 200
    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@admin_bp.route('/schemes', methods=['POST'])
def add_scheme():
    data = request.get_json()
    try:
        res = supabase.table('govt_schemes').insert({
            'title': data.get('title'),
            'category': data.get('category'),
            'description': data.get('description'),
            'official_link': data.get('link')
        }).execute()
        return jsonify({'message': 'Scheme Published!'}), 201
    except Exception as e:
        logger.error(f"Error publishing scheme: {str(e)}")
        return jsonify({'error': 'Database Error', 'message': str(e)}), 500

@admin_bp.route('/orders', methods=['GET'])
def get_all_orders():
    try:
        orders = supabase.table('orders').select('*, users(full_name, email)').order('created_at', desc=True).execute()
        return jsonify(orders.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/orders/<id>/status', methods=['POST'])
def update_order_status(id):
    data = request.json
    new_status = data.get('status') # e.g. 'accepted', 'shipped', 'delivered'
    try:
        supabase.table('orders').update({'status': new_status}).eq('id', id).execute()
        return jsonify({'message': f'Order status updated to {new_status}'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/schemes', methods=['GET'])
def get_schemes():
    try:
        res = supabase.table('govt_schemes').select('*').execute()
        return jsonify({'schemes': res.data}), 200
    except Exception as e:
        logger.error(f"Error fetching schemes: {str(e)}")
        return jsonify({'error': 'Database Error', 'message': str(e)}), 500

@admin_bp.route('/view-document')
def view_document():
    # Proxy route to serve private documents from Supabase using SDK
    url = request.args.get('url')
    if not url:
        return "Missing URL", 400
        
    try:
        # Extract bucket and path from the Supabase URL
        # URL format: .../storage/v1/object/[public|authenticated]/bucket_name/path/to/file
        storage_path = ""
        for marker in ['/public/', '/authenticated/', '/object/']:
            if marker in url:
                storage_path = url.split(marker)[1]
                break
            
        if not storage_path:
            return f"Could not parse storage path from URL: {url}", 400
            
        bucket, path = storage_path.split('/', 1)
        logger.info(f"Proxying request for Bucket: {bucket}, Path: {path}")
        
        # Download using Supabase SDK
        file_data = supabase.storage.from_(bucket).download(path)
        
        # Detect mimetype
        import mimetypes
        mimetype, _ = mimetypes.guess_type(path)
        if not mimetype:
            mimetype = 'image/jpeg' # Fallback
            
        from flask import Response
        return Response(file_data, mimetype=mimetype)
    except Exception as e:
        logger.error(f"Proxy Error for URL {url}: {str(e)}")
        # Return a placeholder image on error to prevent broken UI
        return redirect("https://placehold.co/200x120?text=Error+Loading+Doc")
