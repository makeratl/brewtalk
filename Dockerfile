# Use Python 3.10 base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ ffmpeg espeak-ng && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements_api.txt .
RUN pip install --no-cache-dir -r requirements_api.txt

# Copy application files
COPY . .

# Expose API port
EXPOSE 5002

# Run the FastAPI server with Uvicorn
CMD ["uvicorn", "tts_api_server:app", "--host", "0.0.0.0", "--port", "5002"] 