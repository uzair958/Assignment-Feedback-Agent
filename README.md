# AI Assignment Feedback Platform

An end-to-end full-stack system for evaluating assignment submissions with a hybrid architecture:
- deterministic multi-agent pipeline (ingest -> NLP -> rubric match -> report)
- MCP-compatible orchestration and protocol server
- chat bridge for document-grounded, session-based follow-up Q/A

This repository uses this file as the single markdown documentation source.

## Core Features

- Upload assignment files (.txt, .pdf, .docx)
- Build and save rubric criteria
- Generate structured feedback reports with score breakdowns
- Chat with the same uploaded document after first prompt using session memory
- Continue follow-up Q/A without re-upload (session_id-backed context)
- MCP protocol server support (stdio, sse, streamable-http)

## Architecture Overview

- Backend: FastAPI + Pydantic + LangChain tools + MCP SDK + Groq client
- Frontend: React + TypeScript + Vite
- Data persistence: local JSON storage under backend/data

Backend high-level flow:
1. Ingest file to normalized text
2. Run NLP analysis
3. Match rubric criteria
4. Generate final report
5. Orchestrate via MCP bridge for chat and tool chaining

## Project Structure

- backend/app/api: REST endpoints (upload, rubric, feedback, mcp bridge)
- backend/app/agents: pipeline agents
- backend/app/mcp: orchestration, MCP tools, protocol server, session store
- backend/app/models: request/response schemas
- backend/app/utils: file parsing, storage, LLM client
- backend/tests: backend tests
- frontend/my-react-app/src: React UI, chat panel, API client

## API Endpoints

- GET /health
- POST /api/upload
- POST /api/rubric
- POST /api/feedback/run
- GET /api/feedback/{feedback_id}
- POST /api/mcp/bridge

## Run the Project

### Option 1: One-command startup

From repository root:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
./start-dev.ps1
```

### Option 2: Start services manually

Backend:

```powershell
cd "c:\Users\hp\OneDrive\Desktop\Agentic AI project\backend"
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd "c:\Users\hp\OneDrive\Desktop\Agentic AI project\frontend\my-react-app"
npm install
npm run dev
```

Frontend default URL: http://localhost:5173  
Backend default URL: http://localhost:8000

## Environment Configuration

Backend .env keys:
- GROQ_API_KEY=<your_key>
- GROQ_MODEL=llama3-70b-8192 (default)
- FRONTEND_URL=http://localhost:5173
- DATA_DIR=data

## MCP Usage

The official MCP protocol server is available in backend/app/mcp/protocol_server.py.

Run from backend directory:
- stdio transport
- sse transport
- streamable-http transport

Use CLI flags in protocol_server.py to choose host, port, and transport.

## Chat Memory and Follow-up Behavior

- First prompt can include upload and/or raw_text.
- Session state is keyed by session_id.
- Follow-up prompts reuse saved context (document + artifacts + history).
- Chat responses include contextual answers for question-style follow-ups.

## Testing

From backend directory:

```powershell
.\.venv\Scripts\python -m pytest -q
```

Current test coverage includes:
- API health
- file parsing
- pipeline shape checks
- MCP bridge behavior
- assistant-message formatting
- conversation memory follow-ups

## Tech Stack

- FastAPI
- Pydantic
- LangChain
- LangGraph (installed dependency)
- MCP Python SDK
- Groq SDK
- spaCy
- language-tool-python
- React
- TypeScript
- Vite

## Notes

- Runtime outputs are stored under backend/data.
- For production scaling, move session memory from in-process store to persistent backend (e.g., LangGraph checkpointer with Postgres/Redis).
