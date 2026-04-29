from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from werkzeug.utils import secure_filename
from config import supabase
from utils.storage import upload_file_to_supabase

engineer_bp = Blueprint('engineer', __name__)

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
            'attendance_status': data.get('status', 'present')
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
