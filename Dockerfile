# image 
FROM python:3.11-slim

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# working directory
WORKDIR /app

# for Install system dependencies (Tesseract + build tools)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    gcc \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# requirements  for Docker cache optimization
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create runtime directories
RUN mkdir -p uploads outputs

# Expose Flask port
EXPOSE 5000

# Environment variables (Docker-safe defaults)
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV TESSERACT_PATH=/usr/bin/tesseract

# Start the app
CMD ["python", "app.py"]
