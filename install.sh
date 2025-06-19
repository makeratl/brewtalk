python3.10 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn transformers scipy TTS
pip freeze > requirements_api.txt
pip install --upgrade pip
pip install --upgrade "transformers>=4.31.0" scipy
pip install huggingface_hub
#huggingface-cli download suno/bark --local-dir bark_model