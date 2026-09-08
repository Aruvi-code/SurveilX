FROM python:3.11-slim

# System dependencies for OpenCV & audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (Docker cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create evidence_logs directory
RUN mkdir -p evidence_logs

# Expose port
EXPOSE 5000

# Start the server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
