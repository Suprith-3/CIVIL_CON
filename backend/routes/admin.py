from flask import Blueprint, request, jsonify, redirect, Response, send_file
import csv
import io
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
    try:
        # Fetch 'pending' from specialized tables with individual error handling
        workers = []
        engineers = []
        shops = []
        renters = []

        try:
            res = supabase.table('worker_registrations').select('*').eq('status', 'pending').execute()
            workers = res.data or []
        except Exception as e:
            logger.error(f"Error fetching pending workers: {e}")

        try:
            res = supabase.table('engineer_registrations').select('*').eq('status', 'pending').execute()
            engineers = res.data or []
        except Exception as e:
            logger.error(f"Error fetching pending engineers: {e}")

        try:
            res = supabase.table('shopkeeper_registrations').select('*').eq('status', 'pending').execute()
            shops = res.data or []
        except Exception as e:
            logger.error(f"Error fetching pending shops: {e}")

        try:
            res = supabase.table('renter_registrations').select('*').eq('status', 'pending').execute()
            renters = res.data or []
        except Exception as e:
            logger.error(f"Error fetching pending renters: {e}")
        
        return jsonify({
            'workers': workers,
            'engineers': engineers,
            'shops': shops,
            'renters': renters
        }), 200
    except Exception as e:
        logger.error(f"Global Pending Fetch Error: {e}")
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
        # Step 1: Get all approved worker registrations (has work_type, wages, pic etc.)
        approved_res = supabase.table('worker_registrations').select('*').eq('status', 'approved').execute()
        
        if not approved_res.data:
            return jsonify([]), 200
            
        # Step 2: Get approved user IDs
        approved_ids = [row['user_id'] for row in approved_res.data]
        
        # Step 3: Fetch user profiles
        users_res = supabase.table('users').select('*').in_('id', approved_ids).execute()
        
        # Step 4: Merge registration data into user profile for richer display
        reg_by_uid = {row['user_id']: row for row in approved_res.data}
        merged = []
        for user in users_res.data:
            reg = reg_by_uid.get(user['id'], {})
            merged.append({
                **user,
                'registration_id': reg.get('id'),
                'worker_code': reg.get('worker_code'),
                'work_type': reg.get('work_type'),
                'daily_wages': reg.get('daily_wages'),
                'experience_years': reg.get('experience_years'),
                'profile_pic_url': reg.get('profile_pic_url') or user.get('profile_pic_url'),
                'worker_name': reg.get('name'),
                'phone': reg.get('phone'),
                'location': reg.get('location'),
                'bio': reg.get('bio'),
                'aadhar_image_url': reg.get('aadhar_image_url'),
            })
        
        return jsonify(merged), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/approved-shopkeepers', methods=['GET'])
def get_approved_shopkeepers():
    try:
        # Step 1: Get all approved shopkeeper registrations
        approved_res = supabase.table('shopkeeper_registrations').select('*').eq('status', 'approved').execute()
        
        if not approved_res.data:
            return jsonify([]), 200
            
        # Step 2: Get approved user IDs
        approved_ids = [row['user_id'] for row in approved_res.data]
        
        # Step 3: Fetch user profiles
        users_res = supabase.table('users').select('*').in_('id', approved_ids).execute()
        
        # Step 4: Merge registration data into user profile
        reg_by_uid = {row['user_id']: row for row in approved_res.data}
        merged = []
        for user in users_res.data:
            reg = reg_by_uid.get(user['id'], {})
            merged.append({
                **user,
                'registration_id': reg.get('id'),
                'shop_name': reg.get('shop_name'),
                'phone': reg.get('phone'),
                'shop_location': reg.get('shop_location'),
                'gst_doc': reg.get('gst_doc'),
                'shop_photo': reg.get('shop_photo'),
                'shopkeeper_name': reg.get('name'),
            })
        
        return jsonify(merged), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/approved-renters', methods=['GET'])
def get_approved_renters():
    try:
        # Step 1: Get all approved renter registrations
        approved_res = supabase.table('renter_registrations').select('*').eq('status', 'approved').execute()
        
        if not approved_res.data:
            return jsonify([]), 200
            
        # Step 2: Get approved user IDs
        approved_ids = [row['user_id'] for row in approved_res.data]
        
        # Step 3: Fetch user profiles
        users_res = supabase.table('users').select('*').in_('id', approved_ids).execute()
        
        # Step 4: Merge registration data into user profile
        reg_by_uid = {row['user_id']: row for row in approved_res.data}
        merged = []
        for user in users_res.data:
            reg = reg_by_uid.get(user['id'], {})
            merged.append({
                **user,
                'registration_id': reg.get('id'),
                'renter_name': reg.get('name'),
                'phone': reg.get('phone'),
                'location': reg.get('location'),
                'verification_doc_url': reg.get('verification_doc_url'),
            })
        
        return jsonify(merged), 200
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

@admin_bp.route('/export/<table_name>', methods=['GET'])
def export_table(table_name):
    allowed_tables = [
        'users', 'worker_registrations', 'engineer_registrations', 
        'shopkeeper_registrations', 'renter_registrations', 
        'items', 'orders', 'messages', 'govt_schemes'
    ]
    
    if table_name not in allowed_tables:
        return jsonify({'error': 'Table not allowed for export'}), 400
        
    try:
        # Fetch all data from the table
        res = supabase.table(table_name).select('*').execute()
        data = res.data
        
        if not data:
            return jsonify({'message': 'No data to export'}), 404
            
        # Prepare CSV in memory
        output = io.StringIO()
        
        # Flatten the data structure for CSV (handle nested dicts/lists)
        flattened_rows = []
        fieldnames = set()
        
        for row in data:
            flat_row = {}
            for key, value in row.items():
                if isinstance(value, dict):
                    # Flatten dicts (e.g. location -> location_lat, location_lng)
                    for k, v in value.items():
                        new_key = f"{key}_{k}"
                        flat_row[new_key] = v
                        fieldnames.add(new_key)
                elif isinstance(value, list):
                    # Convert lists to comma-separated strings
                    flat_row[key] = ", ".join([str(i) for i in value])
                    fieldnames.add(key)
                else:
                    flat_row[key] = value
                    fieldnames.add(key)
            flattened_rows.append(flat_row)
            
        # Sort fieldnames for consistency
        sorted_fields = sorted(list(fieldnames))
        
        writer = csv.DictWriter(output, fieldnames=sorted_fields)
        writer.writeheader()
        writer.writerows(flattened_rows)
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={table_name}_export.csv"}
        )
    except Exception as e:
        logger.error(f"Export Error for {table_name}: {str(e)}")
        return jsonify({'error': 'Export failed', 'message': str(e)}), 500

@admin_bp.route('/export-all', methods=['GET'])
def export_all():
    return jsonify({
        'message': 'Use /api/admin/export/<table_name> to download CSV',
        'available_tables': [
            'users', 'worker_registrations', 'engineer_registrations', 
            'shopkeeper_registrations', 'renter_registrations', 
            'items', 'orders', 'messages', 'govt_schemes'
        ]
    }), 200
