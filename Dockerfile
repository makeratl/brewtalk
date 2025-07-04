# Use Python 3.10 base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc g++ ffmpeg libsndfile1-dev espeak-ng && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements_api.txt .
RUN pip install --no-cache-dir -r requirements_api.txt && \
    pip install --no-cache-dir "transformers>=4.31.0" scipy huggingface_hub

# Copy application files
COPY . .

# Download Bark models (optional)
RUN huggingface-cli download suno/bark --local-dir bark_model || \
    echo "Warning: Bark model download failed. Continuing without Bark support."

# Add model verification step
RUN python -c "from TTS.utils.manage import ModelManager; ModelManager().download_model('tts_models/en/vctk/vits')"

# Expose API port
EXPOSE 5002

# Start the server