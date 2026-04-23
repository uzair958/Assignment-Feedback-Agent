# 🤖 AI-Powered Academic Assignment Feedback Agent — Master Build Prompt

## Project Overview

You are an expert full-stack AI engineer. Your task is to build a complete, production-ready **AI-Powered Academic Assignment Feedback Agent** — a multi-agent agentic pipeline that evaluates student submissions against instructor-defined rubrics and generates detailed, actionable feedback reports.

**All components must be free and open-source. No paid APIs.**

---

## Tech Stack (Strictly Enforced)

| Layer | Technology |
|---|---|
| LLM Inference | Groq API (Free Tier) — Model: `llama3-70b-8192` |
| Backend | Python + FastAPI |
| Agent Framework | LangChain (or pure Python with Groq SDK) |
| Inter-Agent Protocol | MCP (Model Context Protocol) — FastAPI-based tool server |
| Frontend | Vite + React + TypeScript (minimal, functional UI) |
| Document Parsing | `python-docx`, `PyMuPDF` (fitz), `python-pptx` |
| NLP Utilities | `spacy`, `language_tool_python` (local grammar check) |
| Auth (optional) | JWT via `python-jose` |

---

## Architecture

```
[Vite + React + TypeScript Frontend]
        ↕  REST / SSE
[FastAPI Backend — MCP Tool Server]
        ↕
[Coordinator Agent]
    ├── Agent 1: Document Ingestion Agent
    ├── Agent 2: NLP Analysis Agent
    ├── Agent 3: Rubric Matching Agent
    └── Agent 4: Feedback Report Generator Agent
        ↕
[Groq API — LLaMA 3 70B (Free)]
```

Each agent is implemented as an **MCP tool** registered on the FastAPI server. The Coordinator Agent calls each tool in sequence via MCP tool-use protocol, passing context between agents.

---

## Why MCP?

Use **Model Context Protocol (MCP)** because:
- Each agent exposes itself as a structured tool with a JSON schema input/output — clean, modular, debuggable.
- The Coordinator LLM (running on Groq) uses MCP tool-calling to orchestrate the pipeline, just like Claude or GPT uses function calling — but entirely on your own server.
- MCP makes each agent independently testable and swappable.
- It fits perfectly with FastAPI: each MCP tool = one FastAPI route + schema.

---

## Detailed Agent Specifications

### Agent 1 — Document Ingestion Agent
**MCP Tool Name:** `ingest_document`

**Input Schema:**
```json
{
  "file_path": "string",
  "file_type": "pdf | docx | txt"
}
```

**Responsibilities:**
- Accept student submission as PDF, DOCX, or plain text.
- Extract raw text using `PyMuPDF` (for PDF) or `python-docx` (for DOCX).
- Normalize: strip headers/footers, clean whitespace, detect sections/headings.
- Output a clean, structured text blob with metadata (word count, section headers, paragraph count).

**Output Schema:**
```json
{
  "raw_text": "string",
  "word_count": "int",
  "paragraph_count": "int",
  "detected_sections": ["Introduction", "Methodology", "..."],
  "language": "en"
}
```

---

### Agent 2 — NLP Analysis Agent
**MCP Tool Name:** `analyze_text`

**Input:** Output from Agent 1 (`raw_text`)

**Responsibilities:**
- **Grammar Check:** Use `language_tool_python` (local, free) to detect grammar/spelling errors. Count and categorize them.
- **Sentence Structure:** Use `spacy` to assess average sentence length, passive voice ratio, sentence variety.
- **Vocabulary Richness:** Type-Token Ratio (TTR), lexical diversity score.
- **Paragraph Coherence:** Use Groq (LLaMA 3 70B) with a prompt to score each paragraph's coherence (1–5 scale).
- **Logical Flow:** Ask the LLM to assess whether arguments flow logically between sections.

**Groq Prompt for Coherence (example):**
```
You are an academic writing evaluator. Analyze the following paragraph for coherence, logical flow, and clarity. Return a JSON object with keys: coherence_score (1-5), issues (list of strings), suggestions (list of strings).

Paragraph:
{paragraph}
```

**Output Schema:**
```json
{
  "grammar_errors": [{"type": "SPELLING", "message": "...", "offset": 12}],
  "grammar_error_count": 5,
  "avg_sentence_length": 18.4,
  "passive_voice_ratio": 0.12,
  "ttr": 0.61,
  "paragraph_coherence": [{"paragraph_index": 0, "score": 4, "issues": [], "suggestions": []}],
  "overall_flow_score": 3.5,
  "flow_comments": "string"
}
```

---

### Agent 3 — Rubric Matching Agent
**MCP Tool Name:** `match_rubric`

**Input:** Rubric JSON (instructor-defined) + NLP analysis output + raw text

**Rubric Format (instructor uploads this as JSON or fills a form):**
```json
{
  "criteria": [
    {"name": "Thesis Clarity", "max_points": 20, "description": "Is the thesis clearly stated in the introduction?"},
    {"name": "Evidence & Support", "max_points": 25, "description": "Are claims supported with evidence and citations?"},
    {"name": "Structure & Organization", "max_points": 20, "description": "Is the paper logically organized with clear sections?"},
    {"name": "Grammar & Mechanics", "max_points": 15, "description": "Is the writing free of grammatical errors?"},
    {"name": "Conclusion", "max_points": 20, "description": "Does the conclusion effectively summarize and reflect?"}
  ]
}
```

**Responsibilities:**
- For each rubric criterion, prompt Groq LLaMA 3 70B with:
  - The criterion name + description + max points
  - Relevant excerpt from the student text
  - NLP analysis data (grammar errors, coherence scores, etc.)
- LLM returns: awarded points, justification, specific improvement suggestions.

**Groq Prompt (per criterion):**
```
You are an academic assignment evaluator. Evaluate the student's submission against the following rubric criterion.

Criterion: {criterion_name}
Description: {criterion_description}
Maximum Points: {max_points}
Student Text Excerpt: {relevant_excerpt}
NLP Data: {nlp_summary}

Return ONLY a JSON object with:
- awarded_points (number, 0 to max_points)
- justification (string, 2-3 sentences)
- strengths (list of strings)
- improvements (list of strings)
```

**Output Schema:**
```json
{
  "rubric_scores": [
    {
      "criterion": "Thesis Clarity",
      "max_points": 20,
      "awarded_points": 16,
      "justification": "...",
      "strengths": ["..."],
      "improvements": ["..."]
    }
  ],
  "total_score": 74,
  "total_possible": 100
}
```

---

### Agent 4 — Feedback Report Generator
**MCP Tool Name:** `generate_feedback_report`

**Input:** All previous agent outputs

**Responsibilities:**
- Synthesize all agent outputs into a cohesive, student-friendly feedback report.
- Use Groq LLaMA 3 70B to write the final narrative report.
- Format: structured JSON that the frontend renders nicely.

**Groq Prompt:**
```
You are a compassionate and expert academic writing coach. Based on the rubric scores and NLP analysis below, write a comprehensive, actionable feedback report for the student. Be specific, encouraging, and constructive.

Rubric Scores: {rubric_scores_json}
NLP Analysis: {nlp_summary_json}
Total Score: {total_score}/{total_possible}

Return ONLY a JSON object with:
- overall_summary (string, 3-4 sentences of holistic feedback)
- grade_breakdown (array of criterion feedback objects)
- top_strengths (list of 3 strings)
- priority_improvements (list of 3-5 strings, most important first)
- suggested_next_steps (list of actionable strings)
```

**Output:** Complete feedback report JSON → rendered in React frontend.

---

## FastAPI Backend Structure

```
backend/
├── main.py                  # FastAPI app entry point
├── routers/
│   ├── upload.py            # File upload endpoint
│   ├── rubric.py            # Rubric CRUD endpoints
│   └── feedback.py          # Trigger full pipeline, return report
├── agents/
│   ├── coordinator.py       # Orchestrates agent pipeline
│   ├── ingestion_agent.py   # Agent 1
│   ├── nlp_agent.py         # Agent 2
│   ├── rubric_agent.py      # Agent 3
│   └── report_agent.py      # Agent 4
├── mcp/
│   ├── server.py            # MCP tool registry
│   └── tools.py             # Tool schemas + handlers
├── models/
│   ├── rubric.py            # Pydantic models
│   └── feedback.py
├── utils/
│   ├── file_parser.py       # PDF/DOCX/TXT extraction
│   └── groq_client.py       # Groq API wrapper
├── requirements.txt
└── .env                     # GROQ_API_KEY (free key from console.groq.com)
```

### Key FastAPI Endpoints

```
POST /api/upload          → Upload student submission (returns file_id)
POST /api/rubric          → Save instructor rubric (returns rubric_id)
GET  /api/rubric/{id}     → Fetch rubric
POST /api/feedback/run    → Trigger full agent pipeline → returns feedback report
GET  /api/feedback/{id}   → Retrieve stored feedback report
```

---

## MCP Tool Server Implementation

In `mcp/server.py`, register each agent as an MCP tool:

```python
from fastapi import FastAPI
from pydantic import BaseModel

MCP_TOOLS = [
    {
        "name": "ingest_document",
        "description": "Extract and normalize text from a student submission file",
        "input_schema": { ... }  # JSON Schema
    },
    {
        "name": "analyze_text",
        "description": "Perform NLP analysis on extracted text",
        "input_schema": { ... }
    },
    {
        "name": "match_rubric",
        "description": "Score the submission against each rubric criterion using LLM",
        "input_schema": { ... }
    },
    {
        "name": "generate_feedback_report",
        "description": "Synthesize all analysis into a student-facing feedback report",
        "input_schema": { ... }
    }
]
```

The Coordinator Agent uses Groq with tool-use to call these MCP tools in order, passing outputs as context.

---

## Groq Configuration

```python
# utils/groq_client.py
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])  # Free key from console.groq.com

def call_llm(prompt: str, system: str = "", json_mode: bool = True) -> dict:
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": system or "You are a helpful academic assistant. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"} if json_mode else None,
        temperature=0.3,
        max_tokens=2048
    )
    return json.loads(response.choices[0].message.content)
```

---

## Vite + React + TypeScript Frontend Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── UploadForm.tsx        # Drag-and-drop file upload
│   │   ├── RubricBuilder.tsx     # Instructor rubric form
│   │   ├── FeedbackReport.tsx    # Main feedback display
│   │   ├── ScoreCard.tsx         # Per-criterion score cards
│   │   └── LoadingState.tsx      # Pipeline progress indicator
│   ├── pages/
│   │   ├── InstructorPage.tsx    # Upload rubric + view results
│   │   └── StudentPage.tsx       # Upload submission + view feedback
│   ├── api/
│   │   └── client.ts             # Axios API calls to FastAPI
│   ├── types/
│   │   └── feedback.ts           # TypeScript interfaces
│   ├── App.tsx
│   └── main.tsx
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

### Key TypeScript Interfaces

```typescript
// types/feedback.ts
export interface RubricCriterion {
  name: string;
  max_points: number;
  description: string;
}

export interface CriterionScore {
  criterion: string;
  max_points: number;
  awarded_points: number;
  justification: string;
  strengths: string[];
  improvements: string[];
}

export interface FeedbackReport {
  overall_summary: string;
  total_score: number;
  total_possible: number;
  grade_breakdown: CriterionScore[];
  top_strengths: string[];
  priority_improvements: string[];
  suggested_next_steps: string[];
}
```

---

## Development Setup Instructions

### 1. Get a Free Groq API Key
Go to [console.groq.com](https://console.groq.com) → Sign up → Create API Key → Add to `.env`

### 2. Backend Setup
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn groq langchain spacy language_tool_python \
            pymupdf python-docx python-jose python-multipart pydantic
python -m spacy download en_core_web_sm
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install axios react-router-dom @types/react
npm run dev
```

---

## Implementation Order (3-Week Sprint)

### Week 1 — Core Pipeline
- [ ] Set up FastAPI skeleton + Groq client
- [ ] Implement Agent 1: Document Ingestion (PDF + DOCX parsing)
- [ ] Implement Agent 2: NLP Analysis (spacy + language_tool + Groq coherence)
- [ ] Register both as MCP tools on the FastAPI MCP server
- [ ] Write unit tests for each agent

### Week 2 — Agent Pipeline + API
- [ ] Implement Agent 3: Rubric Matching with Groq per-criterion scoring
- [ ] Implement Agent 4: Feedback Report Generation
- [ ] Build Coordinator Agent that chains all 4 MCP tools
- [ ] Wire up all FastAPI endpoints (upload, rubric, feedback/run)
- [ ] Integration test the full pipeline end-to-end

### Week 3 — Frontend + Polish
- [ ] Build Vite + React + TS frontend: UploadForm, RubricBuilder, FeedbackReport
- [ ] Connect frontend to FastAPI via Axios
- [ ] Add loading states + error handling
- [ ] End-to-end testing with real student assignment samples
- [ ] Documentation: README, API docs (FastAPI auto-docs at `/docs`)

---

## Quality & Safety Rules

1. **Never hallucinate rubric scores** — always ground scores in actual student text quotes.
2. **Groq rate limits** — the free tier has rate limits (6000 RPM for LLaMA 3 70B). Add retry logic with exponential backoff.
3. **File size limits** — reject files > 10MB at the upload endpoint.
4. **JSON output enforcement** — always use `response_format={"type": "json_object"}` with Groq to prevent non-JSON output from breaking the pipeline.
5. **Error propagation** — if any agent fails, the coordinator returns a partial report with the error surfaced to the frontend — never a silent failure.
6. **No student data persistence** — by default, do not store submission text in a database. Store only the feedback report + metadata.

---

## Environment Variables

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx   # Free from console.groq.com
GROQ_MODEL=llama3-70b-8192
FRONTEND_URL=http://localhost:5173       # For CORS
MAX_FILE_SIZE_MB=10
```

---

## Expected Deliverables

| Deliverable | Description |
|---|---|
| `/backend` | Fully functional FastAPI app with 4 MCP-registered agents |
| `/frontend` | Vite + React + TS minimal UI for instructor + student |
| `README.md` | Setup guide, architecture diagram, API reference |
| `sample_rubric.json` | Example rubric instructors can use |
| `sample_submission.pdf` | Test student assignment for demo |

---

*Built with: Groq (LLaMA 3 70B, free) · FastAPI · LangChain · MCP · Vite + React + TypeScript · spaCy · PyMuPDF · python-docx*
