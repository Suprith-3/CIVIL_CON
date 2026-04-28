import os
import sys
import subprocess

# Monkey patch gevent BEFORE importing other libs
try:
    from gevent import monkey
    monkey.patch_all()
except:
    pass

# Auto-install missing dependencies
try:
    from flask_compress import Compress
    from flask_limiter import Limiter
    from waitress import serve
except ImportError:
    print("📦 Missing dependencies detected. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask-compress", "flask-limiter", "waitress", "gevent", "bleach"])
    print("✅ Installation complete! Restarting...")
    os.execv(sys.executable, ['python'] + sys.argv)

from app import create_app

app = create_app()

def start_server():
    port = int(os.environ.get("PORT", 10000))
    
    if sys.platform == "win32":
        # WINDOWS: Use Waitress for high performance
        from waitress import serve
        print(f"🚀 Starting Production Server (Waitress) on http://0.0.0.0:{port}")
        serve(app, host='0.0.0.0', port=port, threads=8)
    else:
        # LINUX/RENDER: This script is a fallback; usually Gunicorn is used in Procfile
        print(f"🚀 Starting Production Server on port {port}")
        app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    start_server()
