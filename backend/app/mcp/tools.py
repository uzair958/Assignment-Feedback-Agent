from langchain_core.tools import StructuredTool

from app.agents.ingestion_agent import ingest_document
from app.agents.nlp_agent import analyze_text
from app.agents.report_agent import generate_feedback_report
from app.agents.rubric_agent import match_rubric
from app.models.feedback import (
    FeedbackReport,
    IngestInput,
    IngestOutput,
    NLPAnalysisOutput,
    RubricMatchOutput,
)
from app.models.rubric import RubricCriterion


def _ingest_document_tool(file_path: str, file_type: str) -> dict:
    payload = IngestInput(file_path=file_path, file_type=file_type)
    return ingest_document(payload).model_dump(mode="json")


def _analyze_text_tool(raw_text: str) -> dict:
    return analyze_text(raw_text).model_dump(mode="json")


def _match_rubric_tool(rubric: list[dict], raw_text: str, nlp_analysis: dict) -> dict:
    rubric_models = [RubricCriterion.model_validate(x) for x in rubric]
    nlp_model = NLPAnalysisOutput.model_validate(nlp_analysis)
    return match_rubric(rubric_models, raw_text, nlp_model).model_dump(mode="json")


def _generate_feedback_report_tool(rubric_result: dict, nlp_analysis: dict) -> dict:
    rubric_result_model = RubricMatchOutput.model_validate(rubric_result)
    nlp_model = NLPAnalysisOutput.model_validate(nlp_analysis)
    return generate_feedback_report(rubric_result_model, nlp_model).model_dump(mode="json")


LANGCHAIN_TOOLS = [
    StructuredTool.from_function(
        func=_ingest_document_tool,
        name="ingest_document",
        description="Extract and normalize text from a student submission file",
        args_schema=IngestInput,
    ),
    StructuredTool.from_function(
        func=_analyze_text_tool,
        name="analyze_text",
        description="Perform NLP analysis on extracted text",
    ),
    StructuredTool.from_function(
        func=_match_rubric_tool,
        name="match_rubric",
        description="Score submission against rubric criteria",
    ),
    StructuredTool.from_function(
        func=_generate_feedback_report_tool,
        name="generate_feedback_report",
        description="Synthesize rubric and NLP analysis into final report",
    ),
]

TOOL_OUTPUT_SCHEMAS = {
    "ingest_document": IngestOutput.model_json_schema(),
    "analyze_text": NLPAnalysisOutput.model_json_schema(),
    "match_rubric": RubricMatchOutput.model_json_schema(),
    "generate_feedback_report": FeedbackReport.model_json_schema(),
}

TOOLS_BY_NAME = {tool.name: tool for tool in LANGCHAIN_TOOLS}

MCP_TOOLS = [
    {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.args_schema.model_json_schema() if tool.args_schema else {"type": "object"},
        "output_schema": TOOL_OUTPUT_SCHEMAS.get(tool.name, {"type": "object"}),
    }
    for tool in LANGCHAIN_TOOLS
]


def run_tool(name: str, payload: dict):
    tool = TOOLS_BY_NAME.get(name)
    if not tool:
        raise ValueError(f"Unknown tool: {name}")
    result = tool.invoke(payload)
    return result if isinstance(result, dict) else {"result": result}
