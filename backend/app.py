try:
    import os
    if os.environ.get('PORT') or os.environ.get('RENDER'):
        import gevent.monkey
        gevent.monkey.patch_all()
except ImportError:
    pass

import os
from flask import Flask, jsonify, request, redirect, current_app
from flask_jwt_extended import JWTManager
from extensions import limiter, compress
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    # Request logging middleware
    @app.before_request
    def log_request_info():
        app.logger.info(f"REQUEST: {request.method} {request.path}")

    # Initialize extensions
    from flask_cors import CORS
    # 1. CORS with Restricted Origins
    CORS(app, resources={r"/*": {"origins": Config.ALLOWED_ORIGINS}}, supports_credentials=True)

    # 2. Gzip Compression
    compress.init_app(app)
    
    # 3. Rate Limiting
    limiter.init_app(app)
    
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
    from routes.documents import documents_bp
    
    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(items_bp, url_prefix='/api/items')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(engineer_bp, url_prefix='/api/engineer')
    app.register_blueprint(worker_bp, url_prefix='/api/worker')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(documents_bp, url_prefix='/api/docs')

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
        return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500

    @app.route('/')
    def index():
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')
        from flask import send_from_directory
        return send_from_directory(frontend_dir, 'index.html')

    @app.route('/google1d267d2c32708f29.html')
    def google_verification():
        from flask import send_from_directory
        return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'google1d267d2c32708f29.html')

    # Serve Frontend Static Files
    @app.route('/<path:path>')
    def serve_static(path):
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')
        if os.path.exists(os.path.join(frontend_dir, path)):
            from flask import send_from_directory
            return send_from_directory(frontend_dir, path)
        return jsonify({'error': 'Not Found', 'message': f'Path {path} not found'}), 404

    @app.route('/health', methods=['GET'])
    def health_check():
        from config import supabase
        return jsonify({
            'status': 'healthy', 
            'message': 'API is running smoothly',
            'database': 'connected' if supabase else 'disconnected'
        }), 200

    @app.after_request
    def add_security_headers(response):
        """
        Injects mandatory security headers into every response.
        Configured for production environments like Render (Gunicorn).
        """
        # 1. Strict-Transport-Security (HSTS)
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # 2. Hardened Content-Security-Policy (CSP)
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://translate.google.com https://translate.googleapis.com https://unpkg.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://translate.googleapis.com https://unpkg.com",
            "img-src 'self' data: https: blob: *.openstreetmap.org",
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:",
            "connect-src 'self' https://*.supabase.co https://*.googleapis.com https://www.google-analytics.com",
            "media-src 'self' https://www.pexels.com https://*.pexels.com blob: data:",
            "frame-src 'self' https://www.googletagmanager.com https://www.google.com",
            "form-action 'self'",
            "manifest-src 'self'",
            "frame-ancestors 'self'",
            "object-src 'none'",
            "base-uri 'self'"
        ]
        response.headers['Content-Security-Policy'] = "; ".join(csp_directives)
        
        # 3. Anti-Clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # 4. Anti-MIME Sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # 5. XSS Protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # 6. Referrer-Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # 7. Permissions-Policy
        response.headers['Permissions-Policy'] = 'geolocation=(self), microphone=(self), camera=(self), interest-cohort=()'
        
        # 8. Cache-Control (API vs Static)
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
        else:
            response.headers['Cache-Control'] = 'public, no-cache, must-revalidate'

        # 9. Prevent Information Disclosure
        response.headers.pop('Server', None)
        response.headers.pop('X-Powered-By', None)
        
        return response

    return app

if __name__ == '__main__':
    app = create_app()
    # Use the port assigned by Render or default to 10000
    port = int(os.environ.get("PORT", 10000))
    logging.info(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
