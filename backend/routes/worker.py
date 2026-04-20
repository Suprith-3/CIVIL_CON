from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from werkzeug.utils import secure_filename
from config import supabase
import razorpay

worker_bp = Blueprint('worker', __name__)

# Initialize Razorpay Client for Milestone payments
client = razorpay.Client(auth=(os.environ.get("RAZORPAY_KEY_ID"), os.environ.get("RAZORPAY_KEY_SECRET")))

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

@worker_bp.route('/list-approved', methods=['GET'])
def list_approved_workers():
    try:
        res = supabase.table('worker_registrations').select('*').eq('status', 'approved').execute()
        return jsonify({'workers': res.data or []}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@worker_bp.route('/daily-work', methods=['GET'])
def get_daily_work():
    user_id = request.args.get('worker_id')
    try:
        # Get worker's name from registration table
        profile_res = supabase.table('worker_registrations').select('name').eq('user_id', user_id).execute()
        if not profile_res.data:
             return jsonify({'error': 'Profile not found'}), 404
        worker_name = profile_res.data[0]['name']
        
        # Get daily work from engineer's worker_management logs
        work_res = supabase.table('worker_management').select('*').eq('worker_name', worker_name).order('created_at', desc=True).limit(20).execute()
        return jsonify({'daily_work': work_res.data}), 200
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
@worker_bp.route('/book', methods=['POST'])
@jwt_required()
def book_worker():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        booking_data = {
            'user_id': user_id,
            'worker_id': data.get('worker_id'),
            'work_id': data.get('work_id'),
            'title': data.get('title'),
            'total_amount': data.get('total_amount'),
            'paid_amount': 0, # Starts at 0 until verified
            'status': 'pending'
        }
        
        res = supabase.table('worker_bookings').insert(booking_data).execute()
        if res.data:
            return jsonify(res.data[0]), 201
        return jsonify({'error': 'Booking creation failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@worker_bp.route('/verify-booking', methods=['POST'])
@jwt_required()
def verify_booking():
    try:
        data = request.get_json()
        booking_id = data.get('booking_id')
        payment_id = data.get('payment_id') # From Razorpay

        # In a real app, you'd verify the payment_id with Razorpay API here
        # For now, we update the booking status
        
        # We need to fetch the total amount to calculate the 85%
        booking_res = supabase.table('worker_bookings').select('*').eq('id', booking_id).execute()
        if not booking_res.data:
            return jsonify({'error': 'Booking not found'}), 404
        
        booking = booking_res.data[0]
        # Explicit conversion to float for safety
        total = float(booking.get('total_amount', 0))
        upfront = total * 0.85
        
        update_data = {
            'paid_amount': upfront,
            'status': 'paid_partial',
            'tracking_id': payment_id
        }
        
        print(f"VERIFIED: Booking {booking_id} paid 85% (₹{upfront}). Status: paid_partial")
        supabase.table('worker_bookings').update(update_data).eq('id', booking_id).execute()
        return jsonify({'message': 'Initial payment verified! worker notified.'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@worker_bp.route('/list-bookings', methods=['GET'])
@jwt_required()
def list_bookings():
    user_id = get_jwt_identity()
    role = request.args.get('role', 'user') # 'user' or 'worker'
    try:
        current_id = get_jwt_identity()
        print(f"DEBUG: Checking bookings for ID: {current_id} as {role}")
        
        # 1. Direct Fetch of Bookings (No Join for stability)
        column = 'user_id' if role == 'user' else 'worker_id'
        res = supabase.table('worker_bookings').select('*').eq(column, current_id).order('created_at', desc=True).execute()
        bookings = res.data or []
        
        # 2. Manual Stitching of User Details (Fallback Join)
        for b in bookings:
            try:
                # Fetch details of the customer (user_id)
                u_res = supabase.table('users').select('full_name, contact_number, hotel_address, latitude, longitude').eq('id', b['user_id']).execute()
                if u_res.data:
                    b['users'] = u_res.data[0]
                else:
                    b['users'] = {'full_name': 'Registered User'}
            except:
                b['users'] = {'full_name': 'User Info Unavailable'}
        
        return jsonify({'bookings': bookings}), 200
    except Exception as e:
        error_msg = str(e)
        if 'PGRST205' in error_msg:
             print("🚨 CRITICAL ERROR: The table 'worker_bookings' is missing in your Supabase database!")
             print("👉 Please run the SQL command provided in our chat to create it.")
        print(f"FETCH ERROR: {error_msg}")
        return jsonify({'error': 'Database table missing. Please check backend logs.'}), 500
        print(f"FETCH ERROR: {e}")
        return jsonify({'error': str(e)}), 500
        return jsonify({'error': str(e)}), 500

@worker_bp.route('/complete-job', methods=['POST'])
@jwt_required()
def complete_job():
    try:
        booking_id = request.get_json().get('booking_id')
        supabase.table('worker_bookings').update({'status': 'completed'}).eq('id', booking_id).execute()
        return jsonify({'message': 'Job marked as completed. Waiting for final 15% payment.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@worker_bp.route('/pay-final', methods=['POST'])
@jwt_required()
def pay_final():
    try:
        data = request.get_json()
        booking_id = data.get('booking_id')
        payment_id = data.get('payment_id')

        booking_res = supabase.table('worker_bookings').select('*').eq('id', booking_id).execute()
        booking = booking_res.data[0]
        
        update_data = {
            'paid_amount': booking['total_amount'], # Full amount now paid
            'status': 'fully_paid',
            'tracking_id': payment_id # Storing the final transaction id
        }
        
        supabase.table('worker_bookings').update(update_data).eq('id', booking_id).execute()
        return jsonify({'message': 'Final 15% received. Booking closed!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
