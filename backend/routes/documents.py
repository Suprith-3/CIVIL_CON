import os
import requests
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
from datetime import datetime

from services.supabase_service import SupabaseService
from services.google_drive_service import GoogleDriveService

# Standard logging
logger = logging.getLogger(__name__)

documents_bp = Blueprint('documents', __name__)

# Lazy initialization helpers
def get_supabase_svc():
    return SupabaseService()

def get_google_drive_svc():
    # Use environment or default credentials path
    cred_path = os.environ.get('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    # Use absolute path if relative
    if not os.path.isabs(cred_path):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cred_path = os.path.join(root_dir, cred_path)
    return GoogleDriveService(cred_path)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. IP Restriction: Only allow requests from this laptop (localhost)
        client_ip = request.remote_addr
        if client_ip not in ['127.0.0.1', '::1']:
            logger.warning(f"Unauthorized admin attempt from IP: {client_ip}")
            return jsonify({'error': 'Admin actions restricted to local machine only'}), 403

        # 2. Token Check
        token = request.headers.get('X-Admin-Backup-Token')
        if not token or token != os.environ.get('ADMIN_BACKUP_TOKEN'):
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

@documents_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    role = request.form.get('role')
    user_id = get_jwt_identity()

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not role:
        return jsonify({'error': 'Role is required'}), 400

    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    file_path = f"{user_id}/{filename}"
    
    try:
        supabase_svc = get_supabase_svc()
        # 1. Upload to Supabase Storage
        file_content = file.read()
        supabase_svc.upload_document(file_path, file_content, file.content_type)

        # 2. Save Metadata
        metadata = {
            'user_id': user_id,
            'role': role,
            'file_path': file_path,
            'status': 'pending',
            'uploaded_at': datetime.utcnow().isoformat()
        }
        supabase_svc.save_metadata(metadata)

        return jsonify({'message': 'Document uploaded successfully', 'path': file_path}), 201

    except Exception as e:
        logger.error(f"Upload flow failed: {str(e)}")
        return jsonify({'error': 'Internal server error during upload'}), 500

@documents_bp.route('/all', methods=['GET'])
@admin_required
def get_all_docs():
    try:
        supabase_svc = get_supabase_svc()
        docs = supabase_svc.get_all_documents()
        return jsonify(docs), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/approve/<int:doc_id>', methods=['POST'])
@admin_required
def approve_doc(doc_id):
    status = request.json.get('status') # 'approved' or 'rejected'
    if status not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400
    
    try:
        supabase_svc = get_supabase_svc()
        supabase_svc.update_status(doc_id, status)
        return jsonify({'message': f'Document {status}'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/backup-file', methods=['POST'])
@admin_required
def backup_file():
    """
    Triggered by admin or automated process.
    Downloads from Supabase via Signed URL and uploads to Google Drive.
    """
    file_path = request.json.get('file_path')
    user_id = request.json.get('user_id')

    if not file_path or not user_id:
        return jsonify({'error': 'Missing file_path or user_id'}), 400

    try:
        supabase_svc = get_supabase_svc()
        google_drive_svc = get_google_drive_svc()

        if not google_drive_svc.service:
            return jsonify({'error': 'Google Drive service not configured'}), 503

        # 1. Generate Signed URL from Supabase
        signed_url = supabase_svc.create_signed_url(file_path)
        if not signed_url:
            return jsonify({'error': 'Could not generate signed URL'}), 500

        # 2. Download file
        response = requests.get(signed_url)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to download file from storage'}), 500

        # 3. Upload to Google Drive
        filename = os.path.basename(file_path)
        mime_type = response.headers.get('Content-Type', 'application/octet-stream')
        
        drive_file_id = google_drive_svc.upload_file(
            file_content=response.content,
            filename=filename,
            mime_type=mime_type,
            user_id=user_id
        )

        return jsonify({
            'message': 'Backup successful',
            'drive_file_id': drive_file_id
        }), 200

    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
