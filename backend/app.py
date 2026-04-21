import os
from flask import Flask, jsonify, request, redirect, current_app
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

    # Initialize extensions
    CORS(app, resources={r"/*": {"origins": "*"}})
    jwt = JWTManager(app)

    # JWT Error handlers
    @jwt.unauthorized_loader
    def unauthorized_response(callback):
        print("DEBUG: Unauthorized access attempt. Headers:", request.headers)
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Missing Authorization Header'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_response(callback):
        return jsonify({
            'error': 'Invalid Token',
            'message': 'Token format is invalid'
        }), 401

    @jwt.expired_token_loader
    def expired_token_response(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token Expired',
            'message': 'The token has expired'
        }), 401

    # Import Blueprints here
    # Add a route to serve uploaded files
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory, current_app
        # Paths
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        primary_path = os.path.join(root_dir, 'uploads')
        backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
        
        current_app.logger.info(f"SERVING FILE: {filename}")
        current_app.logger.info(f"Checking primary: {primary_path}")
        current_app.logger.info(f"Checking backend: {backend_path}")

        if os.path.exists(os.path.join(primary_path, filename)):
            return send_from_directory(primary_path, filename)
        
        if os.path.exists(os.path.join(backend_path, filename)):
            return send_from_directory(backend_path, filename)

        # Speed/UX: If file is missing (common on Render ephemeral disks), fallback to an engineering placeholder
        return redirect("https://images.unsplash.com/photo-1541888946425-d81bb19480c5?auto=format&fit=crop&q=80&w=300&h=300")

    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.items import items_bp
    from routes.ai import ai_bp
    from routes.engineer import engineer_bp
    from routes.worker import worker_bp
    from routes.orders import orders_bp
    
    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(items_bp, url_prefix='/api/items')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(engineer_bp, url_prefix='/api/engineer')
    app.register_blueprint(worker_bp, url_prefix='/api/worker')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')

    # Base error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden', 'message': str(error)}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not Found', 'message': 'The requested URL was not found on the server.'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error has occurred.'}), 500

    @app.route('/')
    def index():
        return jsonify({
            'status': 'online',
            'service': 'CivilConnect API',
            'version': '1.0.0',
            'message': 'Construction Marketplace Backend is running successfully.'
        }), 200

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'API is running smoothly'}), 200

    return app

if __name__ == '__main__':
    app = create_app()
    # Use the port assigned by Render or default to 10000
    port = int(os.environ.get("PORT", 10000))
    logging.info(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
