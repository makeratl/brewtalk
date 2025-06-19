# BrewTalk TTS API Server

A high-quality text-to-speech API service using VCTK and Bark models for podcast-style voice generation.

## Features
- 🎙️ VCTK model for podcast-style speech synthesis
- 🐕 Bark model for expressive voice generation
- 🌐 REST API with CORS support
- 📊 Health monitoring endpoint
- 📝 Detailed error logging

## Setup Instructions

### Prerequisites
- Python 3.10
- Linux environment (recommended)

### Installation
```bash
# Create virtual environment and install dependencies
chmod +x install.sh
./install.sh

# Download models (run in virtual environment)
huggingface-cli download suno/bark --local-dir bark_model
```

### Running the Server
```bash
source venv/bin/activate
python tts_api_server.py
```

## API Endpoints

### Text-to-Speech (VCTK Model)
**Endpoint**: `POST /api/tts`  
**Request Body**:
```json
{
  "text": "Hello world",
  "speaker_id": "p225"
}
```

**Response**: WAV audio file

### Text-to-Speech (Bark Model)
**Endpoint**: `POST /api/tts/bark`  
**Request Body**:
```json
{
  "text": "Hello world"
}
```

### List Available Speakers
**Endpoint**: `GET /api/speakers`  
**Response**:
```json
{
  "speakers": ["p225", "p226", ...]
}
```

### Health Check
**Endpoint**: `GET /health`  
**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2023-07-15T12:34:56.789Z",
  "model_loaded": true
}
```

## Usage Examples

### Python Client
```python
import requests

# VCTK TTS
response = requests.post(
    "http://localhost:5002/api/tts",
    json={"text": "Welcome to BrewTalk", "speaker_id": "p225"}
)
with open("output.wav", "wb") as f:
    f.write(response.content)

# Bark TTS
response = requests.post(
    "http://localhost:5002/api/tts/bark",
    json={"text": "Hello from Bark!"}
)
```

### cURL Examples
```bash
# VCTK TTS
curl -X POST http://localhost:5002/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world"}' \
  --output output.wav

# List speakers
curl http://localhost:5002/api/speakers
```

## Configuration
- Server runs on `0.0.0.0:5002` by default
- Logs are stored in `tts_server.log`
- Models are cached in `bark_model/` directory

## Troubleshooting
- Check `tts_server.log` for detailed error messages
- Ensure models are downloaded to `bark_model/`
- Verify Python version is 3.10
