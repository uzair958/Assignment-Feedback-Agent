from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.rubric import RubricCriterion


class MCPChatRequest(BaseModel):
    user_prompt: str = Field(min_length=1)
    session_id: str | None = None
    file_id: str | None = None
    rubric_id: str | None = None
    raw_text: str | None = None
    rubric: list[RubricCriterion] | None = None
    max_steps: int = Field(default=8, ge=1, le=20)


class MCPToolExecution(BaseModel):
    tool_name: str
    payload: dict[str, Any]
    result: dict[str, Any]


class MCPChatResponse(BaseModel):
    session_id: str
    assistant_message: str
    intent: Literal["analyze_text", "score_rubric", "full_feedback"]
    planned_tools: list[str]
    executed_steps: list[MCPToolExecution]
    artifacts: dict[str, Any]
