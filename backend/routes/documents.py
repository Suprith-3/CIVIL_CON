import os
import requests
import time
from flask import Blueprint, request, jsonify, current_app
from services.supabase_service import SupabaseService
from services.google_drive_service import GoogleDriveService
from utils.auth_helpers import admin_required
from config import Config

documents_bp = Blueprint('documents', __name__)

# Initialize services (urls/keys are from Config)
supabase_svc = SupabaseService(Config.SUPABASE_URL, Config.SUPABASE_KEY)
google_drive_svc = GoogleDriveService(os.environ.get('GOOGLE_CREDENTIALS_PATH', 'credentials.json'))

@documents_bp.route('/upload', methods=['POST'])
def upload_document():
    """
    User upload endpoint.
    Expects: file, user_id, role
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    user_id = request.form.get('user_id')
    role = request.form.get('role') # engineer, worker, shopkeeper

    if not file or not user_id or not role:
        return jsonify({'error': 'Missing required fields (file, user_id, role)'}), 400

    filename = file.filename
    file_path = f"{user_id}/{filename}"
    content_type = file.content_type

    try:
        # 1. Upload to Supabase Storage
        supabase_svc.upload_file("documents", file_path, file.read(), content_type)

        # 2. Store metadata in database
        metadata = {
            "user_id": user_id,
            "role": role,
            "file_path": file_path,
            "status": "pending",
            "filename": filename
        }
        db_res = supabase_svc.insert_metadata("user_documents", metadata)
        doc_id = db_res[0]['id']

        # 3. Trigger Backup (Optionally asynchronous, but here we do it via internal call or separate trigger)
        # The requirement says "After a file is uploaded, call a backend API (/backup-file)"
        # We can return the doc_id and let the client or a background task call /backup-file
        
        return jsonify({
            'message': 'File uploaded successfully',
            'doc_id': doc_id,
            'file_path': file_path,
            'status': 'pending'
        }), 201

    except Exception as e:
        current_app.logger.error(f"Upload failed: {str(e)}")
        return jsonify({'error': 'Upload failed', 'details': str(e)}), 500

@documents_bp.route('/admin/all', methods=['GET'])
@admin_required
def get_all_documents():
    """Admin feature: View all uploaded documents."""
    try:
        docs = supabase_svc.get_all_documents("user_documents")
        return jsonify(docs), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch documents', 'details': str(e)}), 500

@documents_bp.route('/admin/review', methods=['POST'])
@admin_required
def review_document():
    """Admin feature: Approve/Reject document."""
    data = request.json
    doc_id = data.get('doc_id')
    status = data.get('status') # approved, rejected

    if not doc_id or status not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid request data'}), 400

    try:
        res = supabase_svc.update_metadata("user_documents", doc_id, {"status": status})
        return jsonify({'message': f'Document {status}', 'data': res}), 200
    except Exception as e:
        return jsonify({'error': 'Update failed', 'details': str(e)}), 500

@documents_bp.route('/admin/preview/<doc_id>', methods=['GET'])
@admin_required
def get_preview_url(doc_id):
    """Admin feature: Generate signed URL for secure preview."""
    try:
        doc = supabase_svc.get_document_by_id("user_documents", doc_id)
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        
        signed_url = supabase_svc.get_signed_url("documents", doc['file_path'])
        return jsonify({'signed_url': signed_url}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to generate preview', 'details': str(e)}), 500

@documents_bp.route('/backup-file', methods=['POST'])
@admin_required
def backup_file():
    """
    Auto Backup to Google Drive.
    Expects: doc_id
    """
    data = request.json
    doc_id = data.get('doc_id')
    
    if not doc_id:
        return jsonify({'error': 'doc_id is required'}), 400

    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 1. Get document info
            doc = supabase_svc.get_document_by_id("user_documents", doc_id)
            if not doc:
                return jsonify({'error': 'Document not found'}), 404

            # 2. Generate signed URL from Supabase
            signed_url = supabase_svc.get_signed_url("documents", doc['file_path'])

            # 3. Download file securely
            response = requests.get(signed_url)
            if response.status_code != 200:
                raise Exception(f"Failed to download file from Supabase: {response.status_code}")
            
            file_content = response.content
            mime_type = response.headers.get('Content-Type', 'application/octet-stream')

            # 4. Upload to Google Drive
            drive_file_id = google_drive_svc.upload_file(
                file_content=file_content,
                filename=doc['filename'],
                mime_type=mime_type,
                user_id=doc['user_id']
            )

            # 5. Update database with Drive ID
            supabase_svc.update_metadata("user_documents", doc_id, {
                "google_drive_id": drive_file_id,
                "backed_up_at": "now()" # Supabase/Postgres helper
            })

            current_app.logger.info(f"Backup successful for doc {doc_id}: Drive ID {drive_file_id}")
            return jsonify({
                'status': 'success',
                'message': 'Backup completed',
                'google_drive_id': drive_file_id
            }), 200

        except Exception as e:
            retry_count += 1
            current_app.logger.warning(f"Backup attempt {retry_count} failed for doc {doc_id}: {str(e)}")
            if retry_count >= max_retries:
                current_app.logger.error(f"Backup failed after {max_retries} attempts for doc {doc_id}")
                return jsonify({'error': 'Backup failed', 'attempts': retry_count, 'details': str(e)}), 500
            time.sleep(2) # Wait before retry

@documents_bp.route('/admin/backups', methods=['GET'])
@admin_required
def list_backed_up_files():
    """List all files that have been successfully backed up."""
    try:
        res = supabase_svc.supabase.table("user_documents").select("*").not_.is_("google_drive_id", "null").execute()
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({'error': 'Fetch failed', 'details': str(e)}), 500
