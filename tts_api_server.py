from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import io
from TTS.utils.synthesizer import Synthesizer
from TTS.utils.manage import ModelManager
import uvicorn
import os
import logging
import traceback
from datetime import datetime
from typing import Optional
from transformers import pipeline
import scipy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tts_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="TTS API Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize TTS models
try:
    logger.info("Initializing TTS models...")
    model_manager = ModelManager()

    # VCTK model
    logger.info("Loading VCTK model...")
    model_name_vctk = "tts_models/en/vctk/vits"
    model_path_vctk, config_path_vctk, model_item_vctk = model_manager.download_model(model_name_vctk)
    vocoder_name_vctk = model_item_vctk.get("default_vocoder", None)
    vocoder_path_vctk, vocoder_config_path_vctk, _ = (None, None, None)
    if vocoder_name_vctk:
        vocoder_path_vctk, vocoder_config_path_vctk, _ = model_manager.download_model(vocoder_name_vctk)
    synthesizer_vctk = Synthesizer(
        tts_checkpoint=model_path_vctk,
        tts_config_path=config_path_vctk,
        vocoder_checkpoint=vocoder_path_vctk,
        vocoder_config=vocoder_config_path_vctk,
        use_cuda=False
    )
    logger.info("VCTK model loaded.")

    # Bark model
    logger.info("Loading Bark model...")
    model_name_bark = "tts_models/multilingual/multi-dataset/bark"
    model_path_bark, config_path_bark, model_item_bark = model_manager.download_model(model_name_bark)
    vocoder_name_bark = model_item_bark.get("default_vocoder", None)
    vocoder_path_bark, vocoder_config_path_bark, _ = (None, None, None)
    if vocoder_name_bark:
        vocoder_path_bark, vocoder_config_path_bark, _ = model_manager.download_model(vocoder_name_bark)

except Exception as e:
    logger.error(f"Failed to initialize TTS models: {str(e)}")
    logger.error(traceback.format_exc())
    raise

# Hugging Face Bark setup
try:
    bark_pipeline = pipeline("text-to-speech", "suno/bark")
except Exception as e:
    logging.error(f"Failed to initialize Hugging Face Bark pipeline: {e}")
    bark_pipeline = None

class TTSRequest(BaseModel):
    text: str
    speaker_id: str = None
    language_id: str = None

class BarkTTSRequest(BaseModel):
    text: str

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_details = {
        "error_id": error_id,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "traceback": traceback.format_exc()
    }
    logger.error(f"Error ID {error_id}: {error_details}")
    return JSONResponse(
        status_code=500,
        content=error_details
    )

@app.post("/api/tts")
@app.get("/api/tts")
async def text_to_speech(request: Request, tts_request: TTSRequest = None):
    try:
        # Log request details
        logger.info(f"Received request: {request.method} {request.url}")
        
        # Handle both GET and POST requests
        if tts_request is None:
            # For GET requests, get parameters from query
            text = request.query_params.get("text", "")
            speaker_id = request.query_params.get("speaker_id", None)
            language_id = request.query_params.get("language_id", None)
        else:
            # For POST requests, use the request body
            text = tts_request.text
            speaker_id = tts_request.speaker_id
            language_id = tts_request.language_id

        logger.info(f"Processing text: {text[:100]}...")  # Log first 100 chars of text

        if not text:
            logger.warning("Empty text parameter received")
            raise HTTPException(status_code=400, detail="Text parameter is required")

        # FIXED SPEECH GENERATION
        synthesis_params = {}
        if speaker_id and hasattr(synthesizer_vctk.tts_model, 'speaker_manager'):
            # Verify speaker exists
            if speaker_id not in synthesizer_vctk.tts_model.speaker_manager.speaker_names:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid speaker_id. Valid options: {synthesizer_vctk.tts_model.speaker_manager.speaker_names[:5]}..."
                )
            synthesis_params['speaker_name'] = speaker_id
        
        wavs = synthesizer_vctk.tts(text, **synthesis_params)
        
        # Convert to bytes
        logger.info("Converting to audio bytes...")
        out = io.BytesIO()
        synthesizer_vctk.save_wav(wavs, out)
        out.seek(0)
        
        logger.info("Successfully generated audio")
        # Return audio file
        return StreamingResponse(
            out,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=tts_output.wav"
            }
        )
    except Exception as e:
        logger.error(f"Error in text_to_speech: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@app.get("/health")
async def health_check():
    try:
        # Test TTS functionality with a simple string
        test_text = "Health check"
        wavs = synthesizer_vctk.tts(test_text, speaker_id="p225")
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "model_loaded": True
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/api/speakers")
async def list_speakers():
    try:
        if hasattr(synthesizer_vctk.tts_model, 'speaker_manager'):
            return {
                "speakers": synthesizer_vctk.tts_model.speaker_manager.speaker_names
            }
        return {"speakers": [], "message": "Current model doesn't support multiple speakers"}
    except Exception as e:
        logger.error(f"Error listing speakers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tts/bark")
async def bark_text_to_speech(bark_request: BarkTTSRequest):
    try:
        if bark_pipeline is None:
            raise HTTPException(status_code=500, detail="Bark model not available.")
        text = bark_request.text
        speech = bark_pipeline(text, forward_params={"do_sample": True})
        wav_bytes = io.BytesIO()
        scipy.io.wavfile.write(wav_bytes, rate=speech["sampling_rate"], data=speech["audio"])
        wav_bytes.seek(0)
        return StreamingResponse(
            wav_bytes,
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=bark_output.wav"}
        )
    except Exception as e:
        logging.error(f"Error in bark_text_to_speech: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002) 