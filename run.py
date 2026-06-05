import os
import sys
from dotenv import load_dotenv

# Mock pkg_resources to prevent errors on Python 3.14+ where it was removed from setuptools
from types import ModuleType
class MockPkgResources(ModuleType):
    class DistributionNotFound(Exception):
        pass
    def require(self, *args, **kwargs):
        class MockDist:
            version = "1.4.1"
        return [MockDist()]

sys.modules['pkg_resources'] = MockPkgResources('pkg_resources')

# Add backend directory to sys.path to resolve imports correctly
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

# Load .env file from the backend folder
env_path = os.path.join(backend_dir, '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
    print(f"Loaded environment variables from {env_path}")
else:
    load_dotenv()
    print("Warning: No .env file found in backend folder. Using system environment variables.")

from app import create_app

if __name__ == '__main__':
    app = create_app()
    # Use the port assigned by environment or default to 10000
    port = int(os.environ.get("PORT", 10000))
    debug_mode = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    
    print(f"Starting development server on http://127.0.0.1:{port} (debug={debug_mode})...")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
