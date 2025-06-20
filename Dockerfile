# Use Python 3.10 base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements_api.txt .
RUN pip install --no-cache-dir -r requirements_api.txt && \
    pip install --no-cache-dir "transformers>=4.31.0" scipy huggingface_hub

# Copy application files
COPY . .

# Download Bark model
RUN huggingface-cli download suno/bark --local-dir bark_model

# Expose API port
EXPOSE 5002

# Start the server
CMD ["python", "tts_api_server.py"] 