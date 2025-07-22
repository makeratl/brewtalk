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
synthesizer_vctk = None

# Initialize VCTK model (primary model for podcast)
try:
    logger.info("Initializing VCTK model...")
    model_manager = ModelManager()
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
    logger.info("VCTK model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to initialize VCTK model: {str(e)}")
    logger.error(traceback.format_exc())
    # Don't raise here - let the server start even if VCTK fails



class TTSRequest(BaseModel):
    text: str
    speaker_id: Optional[str] = None
    language_id: Optional[str] = None

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
async def text_to_speech(request: Request, tts_request: Optional[TTSRequest] = None):
    try:
        # Check if VCTK model is available
        if synthesizer_vctk is None:
            raise HTTPException(
                status_code=503, 
                detail="VCTK TTS model is not available. Please check server logs for initialization errors."
            )
            
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
        
        # Backwards compatibility: if no speaker_id is provided, use a default
        speaker_manager = getattr(getattr(synthesizer_vctk, 'tts_model', None), 'speaker_manager', None)
        
        if not speaker_id:
            # Use the first available speaker as default
            if speaker_manager and hasattr(speaker_manager, 'name_to_id') and speaker_manager.name_to_id:
                # Get the first available speaker ID from the name_to_id mapping
                default_speaker_id = list(speaker_manager.name_to_id.keys())[0]
                logger.info(f"No speaker_id provided, using default speaker: {default_speaker_id}")
                synthesis_params['speaker_name'] = default_speaker_id
            else:
                logger.info("No speaker_id provided and no speaker manager available, proceeding without speaker selection")
        elif speaker_manager and hasattr(speaker_manager, 'name_to_id'):
            # Verify speaker exists in the name_to_id mapping
            clean_speaker_id = speaker_id.strip()
            if clean_speaker_id not in speaker_manager.name_to_id:
                available_speakers = list(speaker_manager.name_to_id.keys())[:5]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid speaker_id. Valid options: {available_speakers}..."
                )
            synthesis_params['speaker_name'] = clean_speaker_id
        
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
        wavs = synthesizer_vctk.tts(test_text, speaker_name="p225")
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
        speaker_manager = getattr(getattr(synthesizer_vctk, 'tts_model', None), 'speaker_manager', None)
        if speaker_manager and hasattr(speaker_manager, 'name_to_id'):
            return {
                "speakers": list(speaker_manager.name_to_id.keys())
            }
        return {"speakers": [], "message": "Current model doesn't support multiple speakers"}
    except Exception as e:
        logger.error(f"Error listing speakers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    # Run the Flask app with explicit host and port binding
    app.run(host='0.0.0.0', port=5002, debug=True) 