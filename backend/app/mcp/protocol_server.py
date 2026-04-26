from __future__ import annotations

import argparse
from typing import Any

from app.agents.ingestion_agent import ingest_document
from app.agents.nlp_agent import analyze_text
from app.agents.report_agent import generate_feedback_report
from app.agents.rubric_agent import match_rubric
from app.mcp.orchestrator import run_chat_orchestration
from app.models.feedback import IngestInput, NLPAnalysisOutput, RubricMatchOutput
from app.models.mcp import MCPChatRequest
from app.models.rubric import RubricCriterion


def create_protocol_server(
    host: str = "127.0.0.1",
    port: int = 8001,
    mount_path: str = "/",
    sse_path: str = "/sse",
    message_path: str = "/messages/",
    streamable_http_path: str = "/mcp",
) -> Any:
    """Create an official MCP protocol server (stdio transport).

    The import is intentionally inside this factory so the main API can run
    even if the MCP SDK package is not installed yet.
    """

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - depends on optional package
        raise RuntimeError(
            "The 'mcp' package is required for protocol server mode. "
            "Install dependencies and run again."
        ) from exc

    server = FastMCP(
        "assignment-feedback-mcp",
        host=host,
        port=port,
        mount_path=mount_path,
        sse_path=sse_path,
        message_path=message_path,
        streamable_http_path=streamable_http_path,
    )

    @server.tool(
        name="ingest_document",
        description="Extract and normalize text from a student submission file",
    )
    def ingest_document_tool(file_path: str, file_type: str) -> dict[str, Any]:
        payload = IngestInput(file_path=file_path, file_type=file_type)
        return ingest_document(payload).model_dump(mode="json")

    @server.tool(
        name="analyze_text",
        description="Perform NLP analysis on extracted text",
    )
    def analyze_text_tool(raw_text: str) -> dict[str, Any]:
        return analyze_text(raw_text).model_dump(mode="json")

    @server.tool(
        name="match_rubric",
        description="Score submission against rubric criteria",
    )
    def match_rubric_tool(
        rubric: list[dict[str, Any]], raw_text: str, nlp_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        rubric_models = [RubricCriterion.model_validate(item) for item in rubric]
        nlp_model = NLPAnalysisOutput.model_validate(nlp_analysis)
        return match_rubric(rubric_models, raw_text, nlp_model).model_dump(mode="json")

    @server.tool(
        name="generate_feedback_report",
        description="Synthesize rubric and NLP analysis into final report",
    )
    def generate_feedback_report_tool(
        rubric_result: dict[str, Any], nlp_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        rubric_result_model = RubricMatchOutput.model_validate(rubric_result)
        nlp_model = NLPAnalysisOutput.model_validate(nlp_analysis)
        return generate_feedback_report(rubric_result_model, nlp_model).model_dump(mode="json")

    @server.tool(
        name="run_feedback_chat",
        description=(
            "Run multi-step intent-driven orchestration with session memory. "
            "This can chain ingest/analyze/score/report depending on prompt and context."
        ),
    )
    def run_feedback_chat_tool(
        user_prompt: str,
        session_id: str | None = None,
        file_id: str | None = None,
        rubric_id: str | None = None,
        raw_text: str | None = None,
        rubric: list[dict[str, Any]] | None = None,
        max_steps: int = 8,
    ) -> dict[str, Any]:
        request = MCPChatRequest.model_validate(
            {
                "user_prompt": user_prompt,
                "session_id": session_id,
                "file_id": file_id,
                "rubric_id": rubric_id,
                "raw_text": raw_text,
                "rubric": rubric,
                "max_steps": max_steps,
            }
        )
        return run_chat_orchestration(request).model_dump(mode="json")

    return server


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MCP protocol server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport mode",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP transports")
    parser.add_argument("--port", type=int, default=8001, help="Port for HTTP transports")
    parser.add_argument("--mount-path", default="/", help="Root mount path for HTTP transports")
    parser.add_argument("--sse-path", default="/sse", help="SSE endpoint path")
    parser.add_argument("--message-path", default="/messages/", help="SSE message endpoint path")
    parser.add_argument("--streamable-http-path", default="/mcp", help="Streamable HTTP endpoint path")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    server = create_protocol_server(
        host=args.host,
        port=args.port,
        mount_path=args.mount_path,
        sse_path=args.sse_path,
        message_path=args.message_path,
        streamable_http_path=args.streamable_http_path,
    )
    server.run(transport=args.transport)


if __name__ == "__main__":
    main()
