import os
import requests
import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)
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
        prompt = (
            "List 5 current ongoing Indian government schemes related specifically to civil engineering, home construction, or construction workers (e.g., PMAY-U, DAY-NULM, BOCW benefits).\n"
            "For each scheme, provide:\n"
            "1. Name\n"
            "2. Category (Civil/Worker/Housing)\n"
            "3. Key Benefits\n"
            "4. OFFICIAL APPLYING LINK (or official portal URL)\n"
            "Format the output as a clean, readable list with headers for each point."
        )
        
        ai_response = call_groq(prompt)
        return jsonify({'schemes': ai_response}), 200
    except Exception as e:
        return jsonify({'error': 'AI Error', 'message': str(e)}), 500

@ai_bp.route('/schemes', methods=['GET'])
def get_schemes():
    query = request.args.get('query', 'construction workers and housing in India')
    prompt = (
        f"List the latest active major government schemes in India related to '{query}'.\n"
        "Crucially, for every scheme you mention, you MUST include the OFFICIAL Government Application Link or the specific Department Portal URL where a user can apply.\n"
        "Provide details on eligibility, benefits, and the step-by-step applying process if possible."
    )
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
        
        # Correct Groq Vision Models (Updated for 2026)
        models_to_try = [
            "llama-3.2-11b-vision-preview",
            "pixtral-12b-2409",
            "llava-v1.5-7b-4096-preview"
        ]
        
        last_error = "Unknown Error"
        
        for model in models_to_try:
            logger.info(f"Trying AI Model: {model}")
            
            # Send the image to the vision model
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
                "max_tokens": 150, # Reduced tokens for faster response
                "temperature": 0.1
            }
            
            try:
                response = requests.post(GROQ_URL, headers=headers, json=vision_payload, timeout=20)
                if response.status_code == 200:
                    try:
                        res_json = response.json()
                    except Exception as json_err:
                        logger.error(f"Failed to parse Groq response as JSON: {response.text}")
                        last_error = f"Invalid JSON from AI: {str(json_err)}"
                        continue

                    ai_text = res_json['choices'][0]['message']['content']
                    is_valid = ai_text.upper().startswith('TRUE')
                    reason = ai_text.split(':', 1)[1].strip() if ':' in ai_text else ai_text
                    
                    return jsonify({
                        'valid': is_valid,
                        'message': reason,
                        'ai_response': ai_text
                    }), 200
                else:
                    try:
                        err_json = response.json()
                        last_error = err_json.get('error', {}).get('message', f"API Error {response.status_code}")
                    except:
                        last_error = f"HTTP Error {response.status_code}"
                    logger.warning(f"Model {model} failed: {last_error}")
                    continue
            except Exception as e:
                last_error = str(e)
                logger.error(f"Request to {model} failed: {last_error}")
                continue

        # If all models fail
        return jsonify({
            'valid': False, 
            'message': f'AI Verification Service Unavailable. Error: {last_error}',
            'error': last_error
        }), 200 # Return 200 so the frontend can read the valid:false status gracefully


    except Exception as e:
        return jsonify({'error': 'AI Verification Error', 'message': str(e)}), 500
