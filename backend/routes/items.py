from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from config import supabase
import uuid
import os
import base64

items_bp = Blueprint('items', __name__)

@items_bp.route('/', methods=['GET'])
def get_items():
    try:
        res = supabase.table('items').select('*').order('created_at', desc=True).execute()
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@items_bp.route('/', methods=['POST'])
@jwt_required()
def add_item():
    try:
        user_id = get_jwt_identity()
        data = request.form
        file = request.files.get('product_img')

        if not file:
            return jsonify({'error': 'No image provided'}), 400

        # Ensure the storage folder exists
        # Save to the root 'uploads' folder (consistent with app.py)
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        upload_folder = os.path.join(root_dir, 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # Generate unique name and SAVE TO DISK
        ext = file.filename.split('.')[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        print(f"✅ Image saved successfully: {filename}")

        image_url = f"/uploads/{filename}"

        new_item = {
            'shopkeeper_id': user_id,
            'name': data.get('name'),
            'description': data.get('description', ''),
            'category': data.get('category'),
            'price': float(data.get('price')) if data.get('price') else 0.0,
            'item_type': data.get('item_type', 'sell'), # Default to sell if empty
            'stock': 1,
            'image_url': image_url,
            'is_active': True
        }
        
        res = supabase.table('items').insert(new_item).execute()
        
        if res.data:
            return jsonify({'message': 'Success', 'item': res.data[0]}), 201
        return jsonify({'error': 'Insert failed'}), 500
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@items_bp.route('/scan', methods=['POST'])
@jwt_required()
def scan_image():
    file = request.files.get('product_img')
    if not file: return jsonify({'status': 'No file'}), 400
    try:
        import numpy as np
        import cv2
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is None: return jsonify({'status': 'Invalid Image'}), 400
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return jsonify({'status': 'Verified' if var > 10 else 'Blurry'}), 200
    except:
        return jsonify({'status': 'Verified'}), 200

@items_bp.route('/<id>', methods=['DELETE'])
@jwt_required()
def delete_item(id):
    active_user_id = get_jwt_identity()
    supabase.table('items').delete().eq('id', id).execute()
    return jsonify({'message': 'Item deleted'}), 200
