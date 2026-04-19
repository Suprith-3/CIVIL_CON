from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from config import supabase
import razorpay
import os

orders_bp = Blueprint('orders', __name__)

# Razorpay Client Initialization (Testing mode)
# You will put your real keys in the .env file later
client = razorpay.Client(auth=(os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder"), os.getenv("RAZORPAY_KEY_SECRET", "placeholder_secret")))

@orders_bp.route('/create', methods=['POST'])
@jwt_required()
def create_order():
    try:
        user_id = get_jwt_identity()
        data = request.json
        amount = int(data.get('amount')) * 100  # Amount in paise

        # Create Razorpay Order
        razorpay_order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": "1"
        })

        # Save to Supabase (Pending state)
        new_order = {
            'user_id': user_id,
            'razorpay_order_id': razorpay_order['id'],
            'amount': data.get('amount'),
            'total_amount': data.get('amount'), # Fixed: Matching your specific DB column
            'status': 'ordered',
            'items': data.get('items'),
            'address': data.get('address'),
            'payment_status': 'pending'
        }
        
        supabase.table('orders').insert(new_order).execute()
        
        return jsonify(razorpay_order), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/verify', methods=['POST'])
@jwt_required()
def verify_payment():
    try:
        data = request.json
        # Check if the payment signature is real
        client.utility.verify_payment_signature(data)
        
        # Update order status in Supabase
        supabase.table('orders').update({'payment_status': 'paid'}).eq('razorpay_order_id', data.get('razorpay_order_id')).execute()
        
        return jsonify({'success': True, 'message': 'Payment successful!'}), 200
    except:
        return jsonify({'error': 'Invalid payment signature'}), 400

@orders_bp.route('/my-orders', methods=['GET'])
@jwt_required()
def get_my_orders():
    user_id = get_jwt_identity()
    res = supabase.table('orders').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
    return jsonify(res.data), 200

@orders_bp.route('/all', methods=['GET'])
@jwt_required()
def get_all_orders():
    res = supabase.table('orders').select('*').order('created_at', desc=True).execute()
    return jsonify(res.data), 200

@orders_bp.route('/update/<order_id>', methods=['POST'])
@jwt_required()
def update_order(order_id):
    try:
        data = request.json
        status = data.get('status')
        tracking_id = data.get('tracking_id')
        update_data = {}
        if status: update_data['status'] = status
        if tracking_id: update_data['tracking_id'] = tracking_id
        supabase.table('orders').update(update_data).eq('id', order_id).execute()
        return jsonify({'success': True, 'message': 'Order updated!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
