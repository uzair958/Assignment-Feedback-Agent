from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.mcp.tools import MCP_TOOLS, run_tool

router = APIRouter(tags=["mcp"])


class MCPToolRunRequest(BaseModel):
    tool_name: str
    payload: dict


@router.get("/tools")
def list_tools() -> list[dict]:
    return MCP_TOOLS


@router.post("/tools/run")
def run_mcp_tool(request: MCPToolRunRequest) -> dict:
    try:
        return {"result": run_tool(request.tool_name, request.payload)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
