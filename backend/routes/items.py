from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from config import supabase
import uuid

items_bp = Blueprint('items', __name__)

@items_bp.route('/', methods=['GET'])
def get_items():
    category = request.args.get('category')
    item_type = request.args.get('type') # buy or rent
    
    query = supabase.table('items').select('*').eq('is_active', True)
    
    if category:
        query = query.eq('category', category)
    if item_type:
        query = query.eq('item_type', item_type)
        
    res = query.execute()
    return jsonify(res.data), 200

@items_bp.route('/', methods=['POST'])
@jwt_required()
def add_item():
    identity = get_jwt_identity()
    if identity.get('user_type') != 'shopkeeper':
        return jsonify({'error': 'Forbidden', 'message': 'Only shopkeepers can add items'}), 403
    
    data = request.get_json()
    new_item = {
        'shopkeeper_id': identity.get('id'),
        'name': data.get('name'),
        'description': data.get('description'),
        'category': data.get('category'),
        'price': data.get('price'),
        'item_type': data.get('item_type'),
        'stock': data.get('stock', 0),
        'image_url': data.get('image_url')
    }
    
    res = supabase.table('items').insert(new_item).execute()
    return jsonify(res.data), 201

@items_bp.route('/<id>', methods=['DELETE'])
@jwt_required()
def delete_item(id):
    identity = get_jwt_identity()
    # Check if owner or admin
    item = supabase.table('items').select('shopkeeper_id').eq('id', id).single().execute()
    
    if not item.data:
        return jsonify({'error': 'Not Found'}), 404
        
    if identity.get('user_type') != 'admin' and item.data['shopkeeper_id'] != identity.get('id'):
        return jsonify({'error': 'Forbidden'}), 403
        
    supabase.table('items').delete().eq('id', id).execute()
    return jsonify({'message': 'Item deleted'}), 200
