# AI Assignment Feedback System

End-to-end multi-agent assignment feedback platform with FastAPI backend and React frontend.

## Architecture

- Frontend: Vite + React + TypeScript.
- Backend: FastAPI + MCP-style tool endpoints.
- Agents:
  - `ingest_document`
  - `analyze_text`
  - `match_rubric`
  - `generate_feedback_report`
- Coordinator chains agents and persists rubric/feedback metadata to local JSON storage.

## Backend setup (use existing backend venv)

```powershell
cd "c:\Users\hp\OneDrive\Desktop\Agentic AI project\backend"
uv add -r requirements.txt
uv run python -m spacy download en_core_web_sm
uv run uvicorn main:app --reload --port 8000
```

### Backend API

- `POST /api/upload`
- `POST /api/rubric`
- `GET /api/rubric/{id}`
- `POST /api/feedback/run`
- `POST /api/feedback`
- `GET /api/feedback/{id}`
- `GET /mcp/tools`
- `POST /mcp/tools/run`

## Frontend setup

```powershell
cd "c:\Users\hp\OneDrive\Desktop\Agentic AI project\frontend\my-react-app"
npm install
npm run dev
```

Set backend URL with `VITE_API_BASE_URL` (defaults to `http://localhost:8000/api`).

## Testing

```powershell
cd "c:\Users\hp\OneDrive\Desktop\Agentic AI project\backend"
uv run pytest

cd "c:\Users\hp\OneDrive\Desktop\Agentic AI project\frontend\my-react-app"
npm run lint
npm run build
```
