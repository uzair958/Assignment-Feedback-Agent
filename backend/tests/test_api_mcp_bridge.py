from fastapi.testclient import TestClient

from app.main import app
from app.models.mcp import MCPChatResponse


def test_mcp_bridge_success(monkeypatch) -> None:
    def fake_run_chat(_: object) -> object:
        return MCPChatResponse(
            session_id="s-1",
            assistant_message="ok",
            intent="analyze_text",
            planned_tools=["analyze_text"],
            executed_steps=[],
            artifacts={"nlp_analysis": {}},
        )

    monkeypatch.setattr("app.api.mcp_bridge.run_chat_orchestration", fake_run_chat)

    client = TestClient(app)
    response = client.post("/api/mcp/bridge", json={"user_prompt": "analyze this", "raw_text": "text"})

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "s-1"
    assert body["intent"] == "analyze_text"


def test_mcp_bridge_validation_error(monkeypatch) -> None:
    def fake_run_chat(_: object) -> object:
        raise ValueError("invalid request")

    monkeypatch.setattr("app.api.mcp_bridge.run_chat_orchestration", fake_run_chat)

    client = TestClient(app)
    response = client.post("/api/mcp/bridge", json={"user_prompt": "score"})

    assert response.status_code == 400
    assert "invalid request" in response.json()["detail"]
