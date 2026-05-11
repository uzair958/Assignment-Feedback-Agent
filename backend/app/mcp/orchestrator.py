from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel

from app.mcp.session_store import session_store
from app.mcp.tools import run_tool
from app.models.feedback import (
    FeedbackReport,
    IngestInput,
    IngestOutput,
    NLPAnalysisOutput,
    RubricMatchOutput,
)
from app.models.mcp import MCPChatRequest, MCPChatResponse, MCPToolExecution
from app.models.rubric import RubricCriterion, RubricRecord
from app.utils.groq_client import groq_client
from app.utils.storage import storage

Intent = Literal["analyze_text", "score_rubric", "full_feedback"]


class AnalyzeTextInput(BaseModel):
    raw_text: str


class MatchRubricInput(BaseModel):
    rubric: list[RubricCriterion]
    raw_text: str
    nlp_analysis: NLPAnalysisOutput


class GenerateFeedbackInput(BaseModel):
    rubric_result: RubricMatchOutput
    nlp_analysis: NLPAnalysisOutput


ANALYSIS_KEYWORDS = {
    "analyze",
    "analysis",
    "grammar",
    "coherence",
    "flow",
    "nlp",
    "readability",
    "passive",
}
SCORE_KEYWORDS = {
    "score",
    "grade",
    "rubric",
    "marks",
    "evaluate",
    "criterion",
    "criteria",
}
FULL_FEEDBACK_KEYWORDS = {
    "feedback",
    "report",
    "summary",
    "improvements",
    "next steps",
    "complete",
    "full",
}

FOLLOW_UP_KEYWORDS = {
    "what",
    "why",
    "how",
    "where",
    "which",
    "explain",
    "detail",
    "more",
    "based on",
    "from the text",
}


def _detect_intent(prompt: str, has_rubric_context: bool) -> Intent:
    text = prompt.lower()

    if any(word in text for word in FULL_FEEDBACK_KEYWORDS):
        return "full_feedback"
    if any(word in text for word in SCORE_KEYWORDS):
        return "score_rubric"
    if any(word in text for word in ANALYSIS_KEYWORDS):
        return "analyze_text"

    return "full_feedback" if has_rubric_context else "analyze_text"


def _load_upload_from_id(file_id: str) -> dict[str, Any]:
    upload_meta_path = storage.upload_dir / f"{file_id}.json"
    if not Path(upload_meta_path).exists():
        raise FileNotFoundError("Uploaded file metadata not found.")
    return storage.read_json(upload_meta_path)


def _load_rubric_from_id(rubric_id: str) -> list[dict[str, Any]]:
    rubric_path = storage.rubric_dir / f"{rubric_id}.json"
    if not Path(rubric_path).exists():
        raise FileNotFoundError("Rubric not found.")
    rubric = RubricRecord.model_validate(storage.read_json(rubric_path))
    return [item.model_dump(mode="json") for item in rubric.criteria]


def _build_plan(intent: Intent, state: dict[str, Any]) -> list[str]:
    plan: list[str] = []

    if "raw_text" not in state:
        if "file_meta" not in state:
            raise ValueError("Text context is required. Provide raw_text or file_id.")
        plan.append("ingest_document")

    if intent in {"analyze_text", "score_rubric", "full_feedback"} and "nlp_analysis" not in state:
        plan.append("analyze_text")

    if intent in {"score_rubric", "full_feedback"}:
        if "rubric" not in state:
            raise ValueError("Rubric context is required. Provide rubric or rubric_id.")
        if "rubric_result" not in state:
            plan.append("match_rubric")

    if intent == "full_feedback" and "report" not in state:
        plan.append("generate_feedback_report")

    return plan


def _payload_for_tool(tool_name: str, state: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "ingest_document":
        return {
            "file_path": state["file_meta"]["file_path"],
            "file_type": state["file_meta"]["file_type"],
        }
    if tool_name == "analyze_text":
        return {"raw_text": state["raw_text"]}
    if tool_name == "match_rubric":
        return {
            "rubric": state["rubric"],
            "raw_text": state["raw_text"],
            "nlp_analysis": state["nlp_analysis"],
        }
    if tool_name == "generate_feedback_report":
        return {
            "rubric_result": state["rubric_result"],
            "nlp_analysis": state["nlp_analysis"],
        }
    raise ValueError(f"Unsupported tool in plan: {tool_name}")


def _validate_input(tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "ingest_document":
        return IngestInput.model_validate(payload).model_dump(mode="json")
    if tool_name == "analyze_text":
        return AnalyzeTextInput.model_validate(payload).model_dump(mode="json")
    if tool_name == "match_rubric":
        return MatchRubricInput.model_validate(payload).model_dump(mode="json")
    if tool_name == "generate_feedback_report":
        return GenerateFeedbackInput.model_validate(payload).model_dump(mode="json")
    raise ValueError(f"Unknown tool for input validation: {tool_name}")


def _validate_output(tool_name: str, result: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "ingest_document":
        return IngestOutput.model_validate(result).model_dump(mode="json")
    if tool_name == "analyze_text":
        return NLPAnalysisOutput.model_validate(result).model_dump(mode="json")
    if tool_name == "match_rubric":
        return RubricMatchOutput.model_validate(result).model_dump(mode="json")
    if tool_name == "generate_feedback_report":
        return FeedbackReport.model_validate(result).model_dump(mode="json")
    raise ValueError(f"Unknown tool for output validation: {tool_name}")


def _apply_result(tool_name: str, result: dict[str, Any], state: dict[str, Any]) -> None:
    if tool_name == "ingest_document":
        state["raw_text"] = result["raw_text"]
    elif tool_name == "analyze_text":
        state["nlp_analysis"] = result
    elif tool_name == "match_rubric":
        state["rubric_result"] = result
    elif tool_name == "generate_feedback_report":
        state["report"] = result


def _assistant_message(state: dict[str, Any]) -> str:
    if "report" in state:
        report = FeedbackReport.model_validate(state["report"])
        strengths = ", ".join(report.top_strengths[:2]) or "No key strengths identified yet"
        improvements = (
            ", ".join(report.priority_improvements[:2]) or "No priority improvements identified yet"
        )
        return (
            "Feedback report generated.\n"
            f"Total score: {report.total_score:.1f}/{report.total_possible:.1f}.\n"
            f"Summary: {report.overall_summary}\n"
            f"Top strengths: {strengths}\n"
            f"Priority improvements: {improvements}"
        )

    if "rubric_result" in state:
        rubric = RubricMatchOutput.model_validate(state["rubric_result"])
        top_items = rubric.rubric_scores[:3]
        if top_items:
            lines = [
                f"- {item.criterion}: {item.awarded_points:.1f}/{item.max_points:.1f}"
                for item in top_items
            ]
            top_scores = "\n".join(lines)
        else:
            top_scores = "- No rubric criteria were scored"

        return (
            "Rubric scoring complete.\n"
            f"Total score: {rubric.total_score:.1f}/{rubric.total_possible:.1f}.\n"
            "Top criterion results:\n"
            f"{top_scores}"
        )

    if "nlp_analysis" in state:
        analysis = NLPAnalysisOutput.model_validate(state["nlp_analysis"])
        grammar_examples = [item.message for item in analysis.grammar_errors[:3]]
        grammar_preview = (
            "\n".join(f"- {message}" for message in grammar_examples)
            if grammar_examples
            else "- No grammar issues detected in this pass"
        )

        coherence_issues = [
            f"Paragraph {item.paragraph_index + 1}: {', '.join(item.issues[:2])}"
            for item in analysis.paragraph_coherence
            if item.issues
        ]
        coherence_preview = (
            "\n".join(f"- {issue}" for issue in coherence_issues[:2])
            if coherence_issues
            else "- No major coherence issues flagged"
        )

        return (
            "Writing analysis complete.\n"
            f"Grammar issues found: {analysis.grammar_error_count}.\n"
            f"Avg sentence length: {analysis.avg_sentence_length:.1f} words.\n"
            f"Passive voice ratio: {analysis.passive_voice_ratio:.3f}.\n"
            f"Flow score: {analysis.overall_flow_score:.1f}/5.\n"
            f"Flow comments: {analysis.flow_comments}\n"
            "Grammar highlights:\n"
            f"{grammar_preview}\n"
            "Coherence highlights:\n"
            f"{coherence_preview}"
        )

    return "Request completed, but no analysis artifacts were produced."


def _is_follow_up_question(prompt: str) -> bool:
    text = prompt.lower().strip()
    return "?" in text or any(word in text for word in FOLLOW_UP_KEYWORDS)


def _format_history_for_prompt(state: dict[str, Any], max_turns: int = 6) -> str:
    history = state.get("chat_history", [])[-max_turns:]
    if not history:
        return "No prior conversation."

    lines: list[str] = []
    for item in history:
        role = item.get("role", "assistant")
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        lines.append(f"{role}: {content}")
    return "\n".join(lines) if lines else "No prior conversation."


def _contextual_qa_reply(state: dict[str, Any], user_prompt: str) -> str | None:
    if not groq_client.enabled:
        return None

    has_context = any(
        key in state
        for key in (
            "raw_text",
            "nlp_analysis",
            "rubric_result",
            "report",
        )
    )
    if not has_context:
        return None

    raw_text = str(state.get("raw_text", ""))
    nlp_analysis = state.get("nlp_analysis", {})
    rubric_result = state.get("rubric_result", {})
    report = state.get("report", {})
    conversation_history = _format_history_for_prompt(state)

    prompt = (
        "Answer the user's question using ONLY the provided context from the uploaded document, "
        "analysis artifacts, and chat history. If the answer is not in context, say that clearly.\n\n"
        f"User question:\n{user_prompt}\n\n"
        f"Conversation history:\n{conversation_history}\n\n"
        f"Document excerpt (truncated):\n{raw_text[:6000]}\n\n"
        f"NLP analysis:\n{nlp_analysis}\n\n"
        f"Rubric result:\n{rubric_result}\n\n"
        f"Feedback report:\n{report}\n"
    )

    system = (
        "You are an academic writing assistant for follow-up Q/A. "
        "Be concise, factual, and grounded only in provided context. "
        "When useful, return a short bullet list of findings."
    )

    try:
        response = groq_client.call_text(prompt=prompt, system=system)
        return response or None
    except Exception:
        return None


def _append_chat_history(state: dict[str, Any], user_prompt: str, assistant_message: str) -> None:
    history = list(state.get("chat_history", []))
    history.append({"role": "user", "content": user_prompt})
    history.append({"role": "assistant", "content": assistant_message})
    state["chat_history"] = history[-20:]


def _session_id_for_request(request: MCPChatRequest) -> str:
    return request.session_id or uuid4().hex


def _merge_request_context(request: MCPChatRequest, state: dict[str, Any]) -> None:
    if request.raw_text:
        state["raw_text"] = request.raw_text

    if request.file_id:
        state["file_id"] = request.file_id
        state["file_meta"] = _load_upload_from_id(request.file_id)

    if request.rubric:
        state["rubric"] = [item.model_dump(mode="json") for item in request.rubric]
    elif request.rubric_id:
        state["rubric_id"] = request.rubric_id
        state["rubric"] = _load_rubric_from_id(request.rubric_id)


def _build_tool_step(tool_name: str) -> RunnableLambda:
    def _run_step(state: dict[str, Any]) -> dict[str, Any]:
        payload = _payload_for_tool(tool_name, state)
        validated_payload = _validate_input(tool_name, payload)
        result = run_tool(tool_name, validated_payload)
        validated_result = _validate_output(tool_name, result)

        next_state = dict(state)
        _apply_result(tool_name, validated_result, next_state)

        executed = list(next_state.get("executed_steps", []))
        executed.append(
            MCPToolExecution(
                tool_name=tool_name,
                payload=validated_payload,
                result=validated_result,
            )
        )
        next_state["executed_steps"] = executed
        return next_state

    return RunnableLambda(_run_step)


def _run_plan_with_langchain(plan: list[str], state: dict[str, Any]) -> tuple[dict[str, Any], list[MCPToolExecution]]:
    if not plan:
        return state, []

    chain = _build_tool_step(plan[0])
    for tool_name in plan[1:]:
        chain = chain | _build_tool_step(tool_name)

    final_state = chain.invoke(state)
    return final_state, final_state.get("executed_steps", [])


def run_chat_orchestration(request: MCPChatRequest) -> MCPChatResponse:
    session_id = _session_id_for_request(request)
    state = session_store.get(session_id)

    _merge_request_context(request, state)

    intent = _detect_intent(request.user_prompt, has_rubric_context="rubric" in state)
    plan = _build_plan(intent, state)

    if len(plan) > request.max_steps:
        raise ValueError("Planned tool chain exceeds max_steps.")

    state, executed_steps = _run_plan_with_langchain(plan, state)
    if "executed_steps" in state:
        del state["executed_steps"]

    contextual_reply = None
    if _is_follow_up_question(request.user_prompt) or "chat_history" in state:
        contextual_reply = _contextual_qa_reply(state, request.user_prompt)

    assistant_message = contextual_reply or _assistant_message(state)
    _append_chat_history(state, request.user_prompt, assistant_message)

    session_store.upsert(session_id, state)

    artifacts: dict[str, Any] = {}
    if "raw_text" in state:
        artifacts["raw_text"] = state["raw_text"]
    if "nlp_analysis" in state:
        artifacts["nlp_analysis"] = state["nlp_analysis"]
    if "rubric_result" in state:
        artifacts["rubric_result"] = state["rubric_result"]
    if "report" in state:
        artifacts["report"] = state["report"]

    return MCPChatResponse(
        session_id=session_id,
        assistant_message=assistant_message,
        intent=intent,
        planned_tools=plan,
        executed_steps=executed_steps,
        artifacts=artifacts,
    )
