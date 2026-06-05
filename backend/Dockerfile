FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV and other libs
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

# Optimized Gunicorn command for production
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:create_app()", "--workers", "4", "--threads", "2", "--timeout", "120"]
