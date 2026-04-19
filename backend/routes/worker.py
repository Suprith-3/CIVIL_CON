from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from werkzeug.utils import secure_filename
from config import supabase

worker_bp = Blueprint('worker', __name__)

import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371 # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) * math.sin(dLat / 2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon / 2) * math.sin(dLon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@worker_bp.route('/nearby', methods=['GET'])
def get_nearby_workers():
    user_lat = request.args.get('lat', type=float)
    user_lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', default=20.0, type=float)
    
    if user_lat is None or user_lng is None:
        return jsonify({'error': 'Missing coordinates'}), 400
        
    try:
        # Fetch all approved workers
        res = supabase.table('worker_registrations').select('*').eq('status', 'approved').execute()
        nearby = []
        
        for w in res.data:
            loc = w.get('location', {})
            w_lat = loc.get('lat')
            w_lng = loc.get('lng')
            
            if w_lat and w_lng:
                dist = haversine(user_lat, user_lng, float(w_lat), float(w_lng))
                if dist <= radius:
                    w['distance'] = round(dist, 2)
                    nearby.append(w)
                    
        return jsonify({'workers': nearby}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@worker_bp.route('/portfolio', methods=['POST'])
def add_work():
    # Attempt to get ID from token, fallback to form data for now
    user_id = request.form.get('worker_id')
    print(f"DEBUG: Receiving work upload for user: {user_id}")
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

@worker_bp.route('/profile', methods=['GET'])
def get_profile():
    user_id = request.args.get('worker_id')
    try:
        res = supabase.table('worker_registrations').select('*').eq('user_id', user_id).execute()
        if res.data:
            return jsonify({'profile': res.data[0]}), 200
        return jsonify({'error': 'Profile not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@worker_bp.route('/profile', methods=['POST'])
def update_profile():
    user_id = request.form.get('worker_id')
    data = request.form
    
    upload_folder = os.path.join(os.getcwd(), 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    update_data = {
        'name': data.get('name'),
        'age': int(data.get('age', 0)) if data.get('age') else None,
        'work_type': data.get('work_type'),
        'experience_years': int(data.get('experience', 0)) if data.get('experience') else None,
        'daily_wages': float(data.get('daily_wages', 0)) if data.get('daily_wages') else 0,
        'bio': data.get('bio')
    }

    # Handle Profile Pic
    file = request.files.get('profile_pic')
    if file and file.filename:
        filename = secure_filename(f"profile_{user_id}_{file.filename}")
        file.save(os.path.join(upload_folder, filename))
        update_data['profile_pic_url'] = f"/uploads/{filename}"

    try:
        supabase.table('worker_registrations').update(update_data).eq('user_id', user_id).execute()
        return jsonify({'message': 'Profile updated successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@worker_bp.route('/all-portfolio', methods=['GET'])
def get_all_portfolio():
    try:
        res = supabase.table('worker_portfolio').select('*').order('created_at', desc=True).execute()
        return jsonify({'portfolio': res.data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@worker_bp.route('/list-approved', methods=['GET'])
def list_approved_workers():
    try:
        # Fetch only approved workers
        res = supabase.table('worker_registrations').select('*').eq('status', 'approved').execute()
        return jsonify({'workers': res.data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
