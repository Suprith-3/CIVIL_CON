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
        # Check if an owner_id is passed to filter (for dashboards)
        owner_id = request.args.get('owner_id')
        
        query = supabase.table('items').select('*')
        
        if owner_id:
            query = query.eq('owner_id', owner_id)
            
        res = query.order('created_at', desc=True).execute()
        
        if hasattr(res, 'data'):
            return jsonify(res.data), 200
        else:
            return jsonify({'error': 'Database Error', 'message': 'Failed to retrieve data'}), 500
    except Exception as e:
        import logging
        logging.error(f"Inventory Fetch Error: {str(e)}")
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@items_bp.route('/', methods=['POST'])
@jwt_required()
def add_item():
    try:
        user_id = get_jwt_identity()
        data = request.form
        main_file = request.files.get('product_img')
        extra_files = request.files.getlist('extra_images')
        insurance_file = request.files.get('insurance_doc')

        if not main_file:
            return jsonify({'error': 'Primary image is required'}), 400

        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        upload_folder = os.path.join(root_dir, 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        def save_file_to_supabase(file, prefix='item'):
            if not file or not file.filename:
                return None
            
            try:
                # 1. Ensure bucket exists (Speed: only runs if config is present)
                try:
                    bucket = supabase.storage.get_bucket('media')
                except:
                    supabase.storage.create_bucket('media', options={'public': True})

                # 2. Upload file
                ext = file.filename.split('.')[-1]
                fname = f"{uuid.uuid4()}_{prefix}.{ext}"
                
                # Reserving the file read
                file.seek(0)
                file_content = file.read()
                
                supabase.storage.from_('media').upload(
                    path=fname,
                    file=file_content,
                    file_options={"content-type": file.content_type}
                )
                
                # 3. Return the public URL
                res = supabase.storage.from_('media').get_public_url(fname)
                return res
            except Exception as e:
                import logging
                logging.error(f"SUPABASE UPLOAD ERROR: {str(e)}")
                return None

        image_url = save_file_to_supabase(main_file, 'main')
        
        extra_urls = []
        for ef in extra_files:
            url = save_file_to_supabase(ef, 'extra')
            if url: extra_urls.append(url)
        
        ins_url = save_file_to_supabase(insurance_file, 'ins')

        new_item = {
            'owner_id': user_id,
            'shopkeeper_id': user_id, # Keep compatibility with older schema
            'name': data.get('name'),
            'description': data.get('description', ''),
            'category': data.get('category'),
            'price': float(data.get('price')) if data.get('price') else 0.0,
            'price_unit': data.get('price_unit', 'piece'),
            'item_type': data.get('item_type', 'sell'),
            'stock': int(data.get('stock', 1)),
            'image_url': image_url,
            'extra_images': extra_urls,
            'insurance_url': ins_url,
            'is_active': True
        }
        
        res = supabase.table('items').insert(new_item).execute()
        
        if res.data:
            return jsonify({'message': 'Item listed successfully', 'item': res.data[0]}), 201
        return jsonify({'error': 'Failed to save item to database'}), 500
            
    except Exception as e:
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
