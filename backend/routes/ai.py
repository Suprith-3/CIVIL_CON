import os
import requests
from flask import Blueprint, request, jsonify

ai_bp = Blueprint('ai', __name__)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_groq(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5
    }
    
    response = requests.post(GROQ_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    return f"Error: {response.text}"

@ai_bp.route('/search-schemes', methods=['GET'])
def search_live_schemes():
    try:
        # Specialized prompt for Indian Gov Schemes related to construction
        prompt = "List 5 current/live Indian government schemes related to home construction, civil engineering, or laborers (e.g., PMAY). Provide Name, Key Benefits, and Official Link for each. Format as a simple list for display."
        
        ai_response = call_groq(prompt)
        return jsonify({'schemes': ai_response}), 200
    except Exception as e:
        return jsonify({'error': 'AI Error', 'message': str(e)}), 500

@ai_bp.route('/schemes', methods=['GET'])
def get_schemes():
    query = request.args.get('query', 'construction workers and farmers in India')
    prompt = f"List the latest major government schemes in India for {query}. Provide details on eligibility and benefits."
    result = call_groq(prompt)
    return jsonify({'result': result}), 200

@ai_bp.route('/recommend', methods=['POST'])
def recommend_products():
    data = request.get_json()
    user_query = data.get('query')
    # In a real scenario, we'd pass available products context to Groq
    prompt = f"A user is looking for: '{user_query}' in a construction marketplace. Suggest what categories of workers, engineers, or products they should look for."
    result = call_groq(prompt)
    return jsonify({'recommendation': result}), 200

@ai_bp.route('/verify-document', methods=['POST'])
def verify_document():
    try:
        data = request.get_json()
        image_data = data.get('image') # Base64 string
        doc_type = data.get('type') # 'aadhar', 'completion_cert', 'civil_cert'
        
        if not image_data or not doc_type:
            return jsonify({'valid': False, 'message': 'Missing image or document type'}), 400

        # Document labels for AI context
        doc_names = {
            'comp_cert': 'Engineering Degree Completion Certificate',
            'civil_cert': 'Civil Engineering Level Certificate',
            'aadhar': 'Indian Aadhar Card'
        }
        target_name = doc_names.get(doc_type, 'Official Document')

        # Specialized prompt for Document Verification (Extremely Strict)
        prompt = (
            f"SYSTEM: You are an expert document verification AI.\n"
            f"TASK: Determine if the uploaded image is strictly a {target_name}.\n"
            f"RULES:\n"
            f"1. Only approve if the image is clearly an official certificate or identification card.\n"
            f"2. If the image is a person, a landscape, a building, a random screenshot, or a blank page, reject it.\n"
            f"3. High confidence is required. If in doubt, reject.\n"
            f"OUTPUT FORMAT:\n"
            f"If valid: 'TRUE: Confirmed as {target_name}'\n"
            f"If invalid: 'FALSE: The uploaded image does not appear to be a {target_name}. Please upload a clear photo of the actual document.'\n"
            f"DO NOT add any other text."
        )
        
        # Call Groq with Vision Model
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # List of vision models to try
        models_to_try = [
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "llama-4-scout-17b-16e-instruct",
            "llama-4-scout-17b",
            "meta-llama/llama-3.2-11b-vision-instruct",
            "llama-3.2-11b-vision-preview"
        ]
        
        last_error = "Unknown Error"
        
        for model in models_to_try:
            print(f"DEBUG: Trying AI Model: {model}")
            
            # 1. First, check if the model is even accessible with a simple text message
            test_payload = {
                "model": model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5
            }
            test_res = requests.post(GROQ_URL, headers=headers, json=test_payload)
            if test_res.status_code == 404 or (test_res.status_code == 400 and "model" in test_res.text.lower()):
                print(f"DEBUG: Model {model} not found or decommissioned.")
                continue
            if test_res.status_code == 403 or (test_res.status_code == 400 and "blocked" in test_res.text.lower()):
                print(f"DEBUG: Model {model} is blocked at org level.")
                last_error = test_res.json().get('error', {}).get('message', 'Blocked')
                continue

            # 2. If text test passes, send the image
            vision_payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                        ]
                    }
                ],
                "max_tokens": 300
            }
            
            response = requests.post(GROQ_URL, headers=headers, json=vision_payload)
            
            try:
                res_json = response.json()
            except:
                res_json = {"raw": response.text}

            if response.status_code == 200:
                ai_text = res_json['choices'][0]['message']['content']
                is_valid = ai_text.upper().startswith('TRUE')
                reason = ai_text.split(':', 1)[1].strip() if ':' in ai_text else ai_text
                
                return jsonify({
                    'valid': is_valid,
                    'message': reason,
                    'ai_response': ai_text
                }), 200
            else:
                last_error = res_json.get('error', {}).get('message', 'Unknown Error')
                print(f"DEBUG: Model {model} vision request failed: {last_error}")
                # If vision fails but text worked, it might be the image format
                if "image" in last_error.lower() or "multimodal" in last_error.lower():
                    # Stop here, this model doesn't support vision
                    continue

        return jsonify({
            'valid': False, 
            'message': f'AI Verification Service Unavailable: {last_error}. Please ensure "Llama 4 Scout" is enabled in your Groq Project Limits.',
            'groq_error': last_error
        }), 400

    except Exception as e:
        return jsonify({'error': 'AI Verification Error', 'message': str(e)}), 500
