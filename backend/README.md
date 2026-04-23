# Backend

FastAPI backend for AI-powered assignment feedback.

## Run

1. Activate the existing backend virtualenv.
2. Install dependencies: `uv sync` or `pip install -e .`.
3. Download spaCy model: `python -m spacy download en_core_web_sm`.
4. Start server: `uvicorn main:app --reload --port 8000`.
