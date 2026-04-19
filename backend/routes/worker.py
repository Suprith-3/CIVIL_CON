from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from werkzeug.utils import secure_filename
from config import supabase

worker_bp = Blueprint('worker', __name__)

@worker_bp.route('/portfolio', methods=['POST'])
def add_work():
    # Attempt to get ID from token, fallback to form data for now
    user_id = request.form.get('worker_id')
    data = request.form
    
    upload_folder = os.path.join(os.getcwd(), 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # 2. Save Multiple Photos
    image_files = request.files.getlist('work_images')
    image_urls = []
    for img in image_files:
        if img and img.filename:
            filename = secure_filename(f"work_{user_id}_{img.filename}")
            img.save(os.path.join(upload_folder, filename))
            image_urls.append(f"/uploads/{filename}")

    try:
        work_data = {
            'worker_id': user_id,
            'title': data.get('title'),
            'description': data.get('description'),
            'cost': float(data.get('cost', 0)),
            'duration_days': int(data.get('duration', 0)),
            'image_url': image_urls[0] if image_urls else "not_provided", # Main display image
            'image_list': image_urls # Storing full list
        }
        # We'll use a table named 'worker_portfolio' to store these
        supabase.table('worker_portfolio').insert(work_data).execute()
        return jsonify({'message': 'Work added to your profile successfully!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@worker_bp.route('/portfolio', methods=['GET'])
def get_portfolio():
    user_id = request.args.get('worker_id')
    try:
        res = supabase.table('worker_portfolio').select('*').eq('worker_id', user_id).execute()
        return jsonify({'portfolio': res.data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@worker_bp.route('/all-portfolio', methods=['GET'])
def get_all_portfolio():
    try:
        res = supabase.table('worker_portfolio').select('*').order('created_at', desc=True).execute()
        return jsonify({'portfolio': res.data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
