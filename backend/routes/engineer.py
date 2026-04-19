from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from werkzeug.utils import secure_filename
from config import supabase

engineer_bp = Blueprint('engineer', __name__)

@engineer_bp.route('/project', methods=['POST'])
def add_project():
    user_id = request.form.get('engineer_id') or "397b607d-ecab-4803-9c58-523dc22b0144" 
    data = request.form
    
    upload_folder = os.path.join(os.getcwd(), 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # 1. Save Sketch
    sketch_file = request.files.get('sketch')
    sketch_url = "not_provided"
    if sketch_file and sketch_file.filename:
        filename = secure_filename(f"sketch_{user_id}_{sketch_file.filename}")
        sketch_file.save(os.path.join(upload_folder, filename))
        sketch_url = f"/uploads/{filename}"

    # 2. Save Multiple Photos
    image_files = request.files.getlist('images')
    image_urls = []
    for img in image_files:
        if img and img.filename:
            filename = secure_filename(f"proj_{user_id}_{img.filename}")
            img.save(os.path.join(upload_folder, filename))
            image_urls.append(f"/uploads/{filename}")

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
    user_id = request.args.get('engineer_id') or "397b607d-ecab-4803-9c58-523dc22b0144"
    try:
        res = supabase.table('engineer_projects').select('*').eq('engineer_id', user_id).execute()
        return jsonify({'projects': res.data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@engineer_bp.route('/attendance', methods=['POST'])
def add_attendance():
    data = request.json
    engineer_id = data.get('engineer_id') or "397b607d-ecab-4803-9c58-523dc22b0144"
    try:
        supabase.table('worker_management').insert({
            'engineer_id': engineer_id,
            'worker_name': data.get('worker_name'),
            'location': data.get('location'),
            'assigned_work': data.get('assigned_work'),
            'attendance_status': data.get('status', 'present')
        }).execute()
        return jsonify({'message': 'Attendance logged successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@engineer_bp.route('/attendance', methods=['GET'])
def get_attendance():
    engineer_id = request.args.get('engineer_id') or "397b607d-ecab-4803-9c58-523dc22b0144"
    res = supabase.table('worker_management').select('*').eq('engineer_id', engineer_id).execute()
    return jsonify({'attendance': res.data}), 200

@engineer_bp.route('/certification', methods=['POST'])
def add_certification():
    data = request.form
    engineer_id = data.get('engineer_id') or "397b607d-ecab-4803-9c58-523dc22b0144"
    file = request.files.get('cert_file')
    img_url = "not_uploaded"
    if file:
        filename = secure_filename(f"cert_{engineer_id}_{file.filename}")
        file.save(os.path.join(os.getcwd(), 'uploads', filename))
        img_url = f"/uploads/{filename}"

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
    engineer_id = request.args.get('engineer_id') or "397b607d-ecab-4803-9c58-523dc22b0144"
    res = supabase.table('engineer_certifications').select('*').eq('engineer_id', engineer_id).execute()
    return jsonify({'certifications': res.data}), 200

@engineer_bp.route('/all-projects', methods=['GET'])
def get_all_recent_projects():
    try:
        # Fetching the latest 10 projects from all engineers to show on home screen
        res = supabase.table('engineer_projects').select('*').order('created_at', desc=True).limit(10).execute()
        return jsonify({'projects': res.data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
