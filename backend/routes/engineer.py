import razorpay
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from werkzeug.utils import secure_filename
from config import supabase
from utils.storage import upload_file_to_supabase
from datetime import datetime

engineer_bp = Blueprint('engineer', __name__)
logger = logging.getLogger(__name__)

# Initialize Razorpay Client
razorpay_client = razorpay.Client(auth=(os.environ.get("RAZORPAY_KEY_ID"), os.environ.get("RAZORPAY_KEY_SECRET")))

@engineer_bp.route('/create-advance-order', methods=['POST'])
def create_advance_order():
    try:
        data = request.json
        amount = int(float(data.get('amount')) * 100) # Razorpay expects paise
        
        order_data = {
            'amount': amount,
            'currency': 'INR',
            'payment_capture': 1 # Auto capture
        }
        
        order = razorpay_client.order.create(data=order_data)
        return jsonify({
            'order_id': order['id'], 
            'amount': amount,
            'key_id': os.environ.get("RAZORPAY_KEY_ID")
        }), 200
    except Exception as e:
        logger.error(f"Order Creation Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@engineer_bp.route('/verify-advance-payment', methods=['POST'])
def verify_advance_payment():
    try:
        data = request.json
        # Verify signature
        params_dict = {
            'razorpay_order_id': data.get('razorpay_order_id'),
            'razorpay_payment_id': data.get('razorpay_payment_id'),
            'razorpay_signature': data.get('razorpay_signature')
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Save to database
        advance_data = {
            'engineer_id': data.get('engineer_id'),
            'worker_code': data.get('worker_code'),
            'amount': float(data.get('amount')),
            'payment_id': data.get('razorpay_payment_id'),
            'note': data.get('note'),
            'date': data.get('date', datetime.now().date().isoformat())
        }
        
        supabase.table('worker_advances').insert(advance_data).execute()
        
        # Notify worker
        try:
            # Try to find worker_id by code in worker_registrations OR worker_management
            recipient_id = None
            
            # 1. Try worker_registrations (Formal account)
            worker_reg = supabase.table('worker_registrations').select('user_id').eq('worker_code', data.get('worker_code')).execute()
            if worker_reg.data:
                recipient_id = worker_reg.data[0]['user_id']
            else:
                # 2. Try worker_management (Tracking table)
                worker_track = supabase.table('worker_management').select('worker_id').eq('worker_code', data.get('worker_code')).execute()
                if worker_track.data and worker_track.data[0].get('worker_id'):
                    recipient_id = worker_track.data[0]['worker_id']

            if recipient_id:
                msg = f"💰 Advance Received: You have received ₹{data.get('amount')} as advance from Engineer."
                supabase.table('messages').insert({
                    'sender_id': data.get('engineer_id'),
                    'recipient_id': recipient_id,
                    'message': msg
                }).execute()
        except Exception as e:
            logger.error(f"Notification Error: {str(e)}")

        return jsonify({'message': 'Payment verified and advance recorded!'}), 200
    except Exception as e:
        return jsonify({'error': f'Payment verification failed: {str(e)}'}), 500

@engineer_bp.route('/project', methods=['POST'])
def add_project():
    user_id = request.form.get('engineer_id')
    
    # CRITICAL: Never use a fallback hardcoded ID. Require the real engineer ID.
    if not user_id:
        return jsonify({'error': 'Missing engineer_id. Please log out and log in again.'}), 400
    
    data = request.form
    
    # 1. Save Sketch to Supabase (media bucket)
    sketch_file = request.files.get('sketch')
    sketch_url = upload_file_to_supabase(sketch_file, 'media') or "not_provided"

    # 2. Save Multiple Photos to Supabase (media bucket)
    image_files = request.files.getlist('images')
    
    image_urls = []
    for img in image_files:
        url = upload_file_to_supabase(img, 'media')
        if url: image_urls.append(url)

    try:
        project_data = {
            'engineer_id': user_id,
            'title': data.get('title'),
            'description': data.get('description'),
            'cost': float(data.get('cost', 0)),
            'location': data.get('location'),
            'duration_days': int(data.get('duration', 0)),
            'sketch_url': sketch_url,
            'images': image_urls
        }
        supabase.table('engineer_projects').insert(project_data).execute()
        return jsonify({'message': 'Project published successfully!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@engineer_bp.route('/portfolio', methods=['GET'])
def get_portfolio():
    user_id = request.args.get('engineer_id')
    if not user_id:
        return jsonify({'projects': [], 'error': 'Missing engineer_id'}), 200
    try:
        res = supabase.table('engineer_projects').select('*').eq('engineer_id', user_id).execute()
        return jsonify({'projects': res.data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@engineer_bp.route('/attendance', methods=['POST'])
def add_attendance():
    data = request.json
    engineer_id = data.get('engineer_id')
    if not engineer_id:
        return jsonify({'error': 'Missing engineer_id'}), 400
    try:
        supabase.table('worker_management').insert({
            'engineer_id': engineer_id,
            'worker_name': data.get('worker_name'),
            'worker_code': data.get('worker_code'),
            'location': data.get('location'),
            'assigned_work': data.get('assigned_work'),
            'status': data.get('status', 'assigned'),
            'attendance_status': data.get('attendance_status', 'present')
        }).execute()
        return jsonify({'message': 'Attendance logged successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@engineer_bp.route('/attendance', methods=['GET'])
def get_attendance():
    engineer_id = request.args.get('engineer_id')
    if not engineer_id:
        return jsonify({'attendance': []}), 200
    res = supabase.table('worker_management').select('*').eq('engineer_id', engineer_id).execute()
    return jsonify({'attendance': res.data}), 200

@engineer_bp.route('/certification', methods=['POST'])
def add_certification():
    data = request.form
    engineer_id = data.get('engineer_id')
    if not engineer_id:
        return jsonify({'error': 'Missing engineer_id'}), 400
    # Save Certification to Supabase Storage (documents bucket)
    file = request.files.get('cert_file')
    img_url = upload_file_to_supabase(file, 'documents') or "not_uploaded"

    try:
        supabase.table('engineer_certifications').insert({
            'engineer_id': engineer_id,
            'title': data.get('title'),
            'category': data.get('category', 'Material'),
            'image_url': img_url
        }).execute()
        return jsonify({'message': 'Certification uploaded!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@engineer_bp.route('/certification', methods=['GET'])
def get_certification():
    engineer_id = request.args.get('engineer_id')
    if not engineer_id:
        return jsonify({'certifications': []}), 200
    res = supabase.table('engineer_certifications').select('*').eq('engineer_id', engineer_id).execute()
    return jsonify({'certifications': res.data}), 200

@engineer_bp.route('/all-projects', methods=['GET'])
def get_all_recent_projects():
    try:
        # Only show projects from APPROVED engineers
        approved_res = supabase.table('engineer_registrations').select('user_id').eq('status', 'approved').execute()
        approved_ids = [row['user_id'] for row in approved_res.data]
        
        if not approved_ids:
            return jsonify({'projects': []}), 200
        
        res = supabase.table('engineer_projects').select('*').in_('engineer_id', approved_ids).order('created_at', desc=True).limit(10).execute()
        return jsonify({'projects': res.data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@engineer_bp.route('/project/<project_id>', methods=['GET'])
def get_project_detail(project_id):
    try:
        res = supabase.table('engineer_projects').select('*').eq('id', project_id).single().execute()
        return jsonify({'project': res.data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
