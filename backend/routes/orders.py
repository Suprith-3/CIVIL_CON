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

@orders_bp.route('/create-rental', methods=['POST'])
@jwt_required()
def create_rental():
    try:
        user_id = get_jwt_identity()
        data = request.json
        
        # 1. Fetch user's docs from 'users' table
        user_profile = supabase.table('users').select('aadhar_url, dl_url').eq('id', user_id).single().execute()
        
        # 2. Fetch item's insurance from 'items' table
        item_data = supabase.table('items').select('insurance_url, name').eq('id', data['item_id']).single().execute()

        new_rental = {
            'user_id': user_id,
            'owner_id': data['owner_id'],
            'item_id': data['item_id'],
            'item_name': item_data.data['name'],
            'total_price': data['total_price'],
            'paid_advance': data['paid_advance'],
            'status': 'booked',
            'aadhar_snapshot': user_profile.data.get('aadhar_url'),
            'dl_snapshot': user_profile.data.get('dl_url'),
            'insurance_snapshot': item_data.data.get('insurance_url')
        }
        
        supabase.table('rental_bookings').insert(new_rental).execute()
        return jsonify({'success': True, 'message': 'Rental booking created!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/rental-list', methods=['GET'])
@jwt_required()
def get_rental_list():
    try:
        role = request.args.get('role', 'user') # 'user' or 'owner'
        user_id = get_jwt_identity()
        column = 'user_id' if role == 'user' else 'owner_id'
        
        res = supabase.table('rental_bookings').select('*').eq(column, user_id).order('created_at', desc=True).execute()
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/rental-approve/<booking_id>', methods=['POST'])
@jwt_required()
def approve_rental(booking_id):
    try:
        supabase.table('rental_bookings').update({'status': 'approved'}).eq('id', booking_id).execute()
        return jsonify({'message': 'Rental approved by owner'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
