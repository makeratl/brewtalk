python3.10 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn TTS
pip freeze > requirements_api.txt
pip install --upgrade pip