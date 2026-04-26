from fastapi import APIRouter, HTTPException

from app.mcp.orchestrator import run_chat_orchestration
from app.models.mcp import MCPChatRequest, MCPChatResponse

router = APIRouter(tags=["mcp-bridge"])


@router.post("/mcp/bridge", response_model=MCPChatResponse)
def run_mcp_bridge(payload: MCPChatRequest) -> MCPChatResponse:
    try:
        return run_chat_orchestration(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"MCP bridge error: {exc}") from exc
