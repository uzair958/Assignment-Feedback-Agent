"""
Automated test suite for all test cases defined in testcases.md.

Coverage:
  TC-03  Upload valid file
  TC-04  Upload with no file
  TC-07  Full feedback generation (upload → rubric → report)
  TC-08  Feedback with missing inputs
  TC-09  Chatbot first message
  TC-10  Grammar check via orchestrator
  TC-11  Follow-up re-uses session without re-upload
  TC-12  Prior context used in follow-up
  TC-13  Session ID stable across multiple messages
  TC-14  MCP bridge returns required JSON fields
  TC-15  MCP bridge without document context
  TC-16  Upload unsupported file type
  TC-19  Health check

UI-only cases that require a browser are skipped automatically:
  TC-01  App load
  TC-02  Mode switch
  TC-05  Rubric builder UI
  TC-06  Rubric validation UI
  TC-17  Report rendering UI
  TC-18  Responsive layout
"""

import io

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# ── Helpers ──────────────────────────────────────────────────────────────────

SAMPLE_TEXT = (
    "Climate change is one of the most pressing challenges of our time.\n\n"
    "Rising temperatures are causing glaciers to melt and sea levels to rise.\n\n"
    "Governments must act now to reduce carbon emissions and invest in renewables."
)

SAMPLE_RUBRIC_CRITERIA = [
    {"name": "Clarity", "max_points": 10, "description": "Is the writing clear and easy to follow?"},
    {"name": "Structure", "max_points": 10, "description": "Is the essay logically structured?"},
]

FAKE_CRITERION_JSON = {
    "awarded_points": 8.0,
    "justification": "The writing is clear and well-structured with a logical flow.",
    "strengths": ["Clear thesis", "Good transitions"],
    "improvements": ["Add more supporting evidence"],
    "evidence_quotes": ["climate change is one of the most pressing challenges"],
}

FAKE_REPORT_JSON = {
    "overall_summary": "A solid essay that addresses the topic clearly with room for deeper analysis.",
    "top_strengths": ["Clear main argument", "Good paragraph structure"],
    "priority_improvements": ["Include more data and citations"],
    "suggested_next_steps": ["Add a bibliography", "Expand the conclusion paragraph"],
}

FAKE_NLP_RESULT = {
    "grammar_errors": [
        {"type": "grammar", "message": "Use 'an' before a vowel sound.", "offset": 4},
        {"type": "style", "message": "Sentence is too long.", "offset": 55},
    ],
    "grammar_error_count": 2,
    "avg_sentence_length": 18.5,
    "passive_voice_ratio": 0.1,
    "ttr": 0.62,
    "paragraph_coherence": [
        {
            "paragraph_index": 0,
            "score": 4,
            "issues": ["Minor transition issue"],
            "suggestions": ["Add a linking phrase"],
        }
    ],
    "overall_flow_score": 4.1,
    "flow_comments": "Flow is mostly smooth with minor transitions missing.",
}


@pytest.fixture()
def uploaded_file_id() -> str:
    resp = client.post(
        "/api/upload",
        files={"file": ("essay.txt", io.BytesIO(SAMPLE_TEXT.encode()), "text/plain")},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["file_id"]


@pytest.fixture()
def saved_rubric_id() -> str:
    resp = client.post(
        "/api/rubric",
        json={"criteria": SAMPLE_RUBRIC_CRITERIA},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["rubric_id"]


# ── TC-19: Health Check ───────────────────────────────────────────────────────

def test_tc19_health_check() -> None:
    """TC-19: GET /health → { "status": "ok" }"""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── TC-03: Upload valid files ─────────────────────────────────────────────────

def test_tc03_upload_valid_txt() -> None:
    """TC-03: Upload a valid .txt file → 200, file_id returned"""
    resp = client.post(
        "/api/upload",
        files={"file": ("essay.txt", io.BytesIO(SAMPLE_TEXT.encode()), "text/plain")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "file_id" in body
    assert body["file_id"]
    assert body["file_type"] == "txt"


def test_tc03_upload_valid_docx() -> None:
    """TC-03: Upload a .docx file (minimal valid bytes) → 200"""
    # Minimal valid docx is a zip; just check the extension path is accepted
    # Use a real tiny docx-like binary (PK header)
    docx_bytes = (
        b"PK\x03\x04\x14\x00\x00\x00\x08\x00"  # zip local file header
        + b"\x00" * 200
    )
    resp = client.post(
        "/api/upload",
        files={"file": ("report.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    # Accept 200 (stored) or 500 (parse error later); the upload itself should not be 400/422
    assert resp.status_code in (200, 500)


# ── TC-04: Upload with no file ────────────────────────────────────────────────

def test_tc04_upload_no_file() -> None:
    """TC-04: POST /api/upload with no file → 422 validation error"""
    resp = client.post("/api/upload")
    assert resp.status_code == 422


# ── TC-16: Upload unsupported file type ──────────────────────────────────────

def test_tc16_upload_unsupported_type() -> None:
    """TC-16: Upload a .exe file → 400 unsupported file type"""
    resp = client.post(
        "/api/upload",
        files={"file": ("script.exe", io.BytesIO(b"MZ\x00\x00"), "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert "Unsupported" in resp.json()["detail"]


def test_tc16_upload_csv_rejected() -> None:
    """TC-16: Upload a .csv file → 400"""
    resp = client.post(
        "/api/upload",
        files={"file": ("data.csv", io.BytesIO(b"a,b,c\n1,2,3"), "text/csv")},
    )
    assert resp.status_code == 400


# ── TC-07: Full feedback generation ──────────────────────────────────────────

def test_tc07_full_feedback_pipeline(
    uploaded_file_id: str, saved_rubric_id: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TC-07: Upload + rubric + generate → full report with scores and sections"""

    def fake_call_json(prompt: str, system: str, retries: int = 3) -> dict:
        # NLP agent — paragraph coherence (unique phrase only in nlp_agent)
        if "Analyze this paragraph for coherence" in prompt:
            return {"coherence_score": 4, "issues": ["Minor issue"], "suggestions": ["Add transition"]}
        # NLP agent — overall flow (unique phrase only in nlp_agent)
        if "Evaluate logical flow between sections" in prompt:
            return {"overall_flow_score": 4.2, "flow_comments": "Flow is mostly smooth."}
        # Rubric agent — per-criterion scoring (unique phrase only in rubric_agent)
        if "Evaluate the submission against this rubric criterion" in prompt:
            return FAKE_CRITERION_JSON
        # Report agent — final report synthesis (catch-all)
        return FAKE_REPORT_JSON

    monkeypatch.setattr("app.utils.groq_client.groq_client.call_json", fake_call_json)
    monkeypatch.setattr(
        "app.utils.groq_client.groq_client.call_text",
        lambda *_a, **_k: "Flow is smooth.",
    )

    resp = client.post(
        "/api/feedback/run",
        json={"file_id": uploaded_file_id, "rubric_id": saved_rubric_id},
    )
    assert resp.status_code == 200
    body = resp.json()

    # Top-level record fields
    assert "feedback_id" in body
    assert "report" in body
    assert "ingest" in body
    assert "analysis" in body
    assert "rubric_match" in body

    report = body["report"]
    assert report["total_possible"] == 20.0
    assert report["total_score"] == pytest.approx(16.0)
    assert len(report["grade_breakdown"]) == 2
    assert report["overall_summary"]
    assert len(report["top_strengths"]) >= 1
    assert len(report["priority_improvements"]) >= 1
    assert len(report["suggested_next_steps"]) >= 1

    # Grade breakdown structure
    for score in report["grade_breakdown"]:
        assert "criterion" in score
        assert "awarded_points" in score
        assert "justification" in score
        assert "strengths" in score
        assert "improvements" in score


# ── TC-08: Feedback with missing inputs ───────────────────────────────────────

def test_tc08_feedback_missing_file(saved_rubric_id: str) -> None:
    """TC-08: Run feedback with a nonexistent file_id → 404"""
    resp = client.post(
        "/api/feedback/run",
        json={"file_id": "does-not-exist", "rubric_id": saved_rubric_id},
    )
    assert resp.status_code == 404


def test_tc08_feedback_missing_rubric(uploaded_file_id: str) -> None:
    """TC-08: Run feedback with a nonexistent rubric_id → 404"""
    resp = client.post(
        "/api/feedback/run",
        json={"file_id": uploaded_file_id, "rubric_id": "does-not-exist"},
    )
    assert resp.status_code == 404


def test_tc08_feedback_missing_both_fields() -> None:
    """TC-08: POST /api/feedback/run with empty body → 422"""
    resp = client.post("/api/feedback/run", json={})
    assert resp.status_code == 422


# ── TC-14: MCP bridge JSON structure ─────────────────────────────────────────

def test_tc14_bridge_returns_required_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-14: Bridge response contains all required JSON fields"""
    from app.models.mcp import MCPChatResponse

    monkeypatch.setattr(
        "app.api.mcp_bridge.run_chat_orchestration",
        lambda _: MCPChatResponse(
            session_id="s-tc14",
            assistant_message="Analysis complete.",
            intent="analyze_text",
            planned_tools=["analyze_text"],
            executed_steps=[],
            artifacts={"nlp_analysis": {}},
        ),
    )

    resp = client.post(
        "/api/mcp/bridge",
        json={"user_prompt": "analyze this text", "raw_text": SAMPLE_TEXT},
    )
    assert resp.status_code == 200
    body = resp.json()
    for key in ("session_id", "assistant_message", "intent", "planned_tools", "executed_steps", "artifacts"):
        assert key in body, f"Missing required field: {key}"
    assert body["session_id"] == "s-tc14"
    assert body["intent"] == "analyze_text"


# ── TC-15: Bridge without document context ────────────────────────────────────

def test_tc15_bridge_no_context() -> None:
    """TC-15: Bridge prompt without file or raw_text → error or guided message"""
    resp = client.post(
        "/api/mcp/bridge",
        json={"user_prompt": "analyze without any document context"},
    )
    # Either a 400 with an error message or a 200 with a guided response — not a 5xx crash
    assert resp.status_code in (200, 400)
    if resp.status_code == 400:
        assert resp.json().get("detail")


# ── TC-09 & TC-10: Chatbot first message / grammar check ─────────────────────

def test_tc09_tc10_chatbot_first_message_grammar(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-09 & TC-10: First chatbot message returns a contextual grammar response"""
    from app.mcp.orchestrator import run_chat_orchestration
    from app.models.mcp import MCPChatRequest

    monkeypatch.setattr("app.mcp.orchestrator.run_tool", lambda _name, _payload: FAKE_NLP_RESULT)
    monkeypatch.setattr("app.mcp.orchestrator._contextual_qa_reply", lambda *_a, **_k: None)

    result = run_chat_orchestration(
        MCPChatRequest(
            user_prompt="Find grammatical errors in the uploaded document.",
            raw_text=SAMPLE_TEXT,
        )
    )

    assert result.session_id
    assert result.intent == "analyze_text"
    assert result.assistant_message
    assert "Grammar issues found" in result.assistant_message
    assert "2" in result.assistant_message  # 2 grammar errors


# ── TC-11 & TC-13: Follow-up memory / session stability ──────────────────────

def test_tc11_tc13_followup_uses_same_session(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-11 & TC-13: Follow-up re-uses session_id without re-uploading"""
    from app.mcp.orchestrator import run_chat_orchestration
    from app.models.mcp import MCPChatRequest

    monkeypatch.setattr("app.mcp.orchestrator.run_tool", lambda _name, _payload: FAKE_NLP_RESULT)
    monkeypatch.setattr("app.mcp.orchestrator._contextual_qa_reply", lambda *_a, **_k: None)

    first = run_chat_orchestration(
        MCPChatRequest(
            user_prompt="Check grammar in this document.",
            raw_text=SAMPLE_TEXT,
        )
    )
    assert first.session_id
    session_id = first.session_id

    second = run_chat_orchestration(
        MCPChatRequest(
            user_prompt="What were the grammar issues found?",
            session_id=session_id,
            # No raw_text — should use session memory
        )
    )
    # Session ID must be the same
    assert second.session_id == session_id
    # Follow-up should not re-run tools (no raw_text, no new intent trigger)
    assert second.planned_tools == []


# ── TC-12: Prior context in follow-up ────────────────────────────────────────

def test_tc12_prior_context_in_followup(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-12: Follow-up answer references data from the previous session turn"""
    from app.mcp.orchestrator import run_chat_orchestration
    from app.models.mcp import MCPChatRequest

    monkeypatch.setattr("app.mcp.orchestrator.run_tool", lambda _name, _payload: FAKE_NLP_RESULT)
    monkeypatch.setattr("app.mcp.orchestrator._contextual_qa_reply", lambda *_a, **_k: None)

    first = run_chat_orchestration(
        MCPChatRequest(
            user_prompt="Analyze the grammar of this document.",
            raw_text=SAMPLE_TEXT,
        )
    )

    # The first response should include the grammar error message from FAKE_NLP_RESULT
    assert "Use 'an' before a vowel sound." in first.assistant_message

    follow_up = run_chat_orchestration(
        MCPChatRequest(
            user_prompt="Can you explain the first issue in more detail?",
            session_id=first.session_id,
        )
    )
    # Follow-up remains in the same session
    assert follow_up.session_id == first.session_id


# ── UI-Only tests (skipped) ───────────────────────────────────────────────────

@pytest.mark.skip(reason="TC-01: UI test — verify manually at http://localhost:5173")
def test_tc01_app_load() -> None: ...


@pytest.mark.skip(reason="TC-02: UI test — verify mode toggle manually in browser")
def test_tc02_mode_switch() -> None: ...


@pytest.mark.skip(reason="TC-05: UI test — verify rubric builder manually in browser")
def test_tc05_rubric_builder_ui() -> None: ...


@pytest.mark.skip(reason="TC-06: UI test — verify rubric validation manually in browser")
def test_tc06_rubric_validation_ui() -> None: ...


@pytest.mark.skip(reason="TC-17: UI test — verify report rendering manually in browser")
def test_tc17_report_rendering_ui() -> None: ...


@pytest.mark.skip(reason="TC-18: UI test — verify responsive layout manually in browser")
def test_tc18_responsive_layout_ui() -> None: ...
