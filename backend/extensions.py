from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress

# Initialize extensions without app context
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

compress = Compress()
