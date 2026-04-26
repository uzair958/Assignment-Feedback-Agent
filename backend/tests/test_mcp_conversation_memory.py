from app.mcp.orchestrator import run_chat_orchestration
from app.models.mcp import MCPChatRequest


def _fake_analysis_output() -> dict:
    return {
        "grammar_errors": [
            {"type": "grammar", "message": "Use 'an' before a vowel.", "offset": 4},
            {"type": "style", "message": "Sentence is too long.", "offset": 19},
        ],
        "grammar_error_count": 2,
        "avg_sentence_length": 16.5,
        "passive_voice_ratio": 0.125,
        "ttr": 0.5,
        "paragraph_coherence": [
            {
                "paragraph_index": 0,
                "score": 3,
                "issues": ["Weak transition"],
                "suggestions": ["Add transition phrase"],
            }
        ],
        "overall_flow_score": 3.4,
        "flow_comments": "Flow is fair with minor transition issues.",
    }


def test_follow_up_uses_session_context_without_reupload(monkeypatch) -> None:
    def fake_run_tool(name: str, _payload: dict) -> dict:
        if name == "analyze_text":
            return _fake_analysis_output()
        raise AssertionError(f"Unexpected tool called: {name}")

    monkeypatch.setattr("app.mcp.orchestrator.run_tool", fake_run_tool)
    monkeypatch.setattr("app.mcp.orchestrator._contextual_qa_reply", lambda *_args, **_kwargs: None)

    first = run_chat_orchestration(
        MCPChatRequest(
            user_prompt="Find grammar mistakes in this document",
            raw_text="This are a sample text with grammar issue.",
        )
    )

    assert first.session_id
    assert first.intent == "analyze_text"
    assert first.planned_tools == ["analyze_text"]

    follow_up = run_chat_orchestration(
        MCPChatRequest(
            user_prompt="What are the top grammar issues?",
            session_id=first.session_id,
        )
    )

    assert follow_up.intent == "analyze_text"
    assert follow_up.planned_tools == []
    assert "Grammar issues found" in follow_up.assistant_message
    assert "Use 'an' before a vowel." in follow_up.assistant_message
