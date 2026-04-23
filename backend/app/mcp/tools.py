from app.agents.ingestion_agent import ingest_document
from app.agents.nlp_agent import analyze_text
from app.agents.report_agent import generate_feedback_report
from app.agents.rubric_agent import match_rubric
from app.models.feedback import (
    IngestInput,
    IngestOutput,
    NLPAnalysisOutput,
    RubricMatchOutput,
)
from app.models.rubric import RubricCriterion

MCP_TOOLS = [
    {
        "name": "ingest_document",
        "description": "Extract and normalize text from a student submission file",
        "input_schema": IngestInput.model_json_schema(),
        "output_schema": IngestOutput.model_json_schema(),
    },
    {
        "name": "analyze_text",
        "description": "Perform NLP analysis on extracted text",
        "input_schema": {"type": "object", "properties": {"raw_text": {"type": "string"}}},
        "output_schema": NLPAnalysisOutput.model_json_schema(),
    },
    {
        "name": "match_rubric",
        "description": "Score submission against rubric criteria",
        "input_schema": {
            "type": "object",
            "properties": {
                "rubric": {"type": "array", "items": RubricCriterion.model_json_schema()},
                "raw_text": {"type": "string"},
                "nlp_analysis": NLPAnalysisOutput.model_json_schema(),
            },
            "required": ["rubric", "raw_text", "nlp_analysis"],
        },
        "output_schema": RubricMatchOutput.model_json_schema(),
    },
    {
        "name": "generate_feedback_report",
        "description": "Synthesize rubric and NLP analysis into final report",
        "input_schema": {
            "type": "object",
            "properties": {
                "rubric_result": RubricMatchOutput.model_json_schema(),
                "nlp_analysis": NLPAnalysisOutput.model_json_schema(),
            },
            "required": ["rubric_result", "nlp_analysis"],
        },
        "output_schema": {"type": "object"},
    },
]


def run_tool(name: str, payload: dict):
    if name == "ingest_document":
        return ingest_document(IngestInput.model_validate(payload)).model_dump(mode="json")
    if name == "analyze_text":
        return analyze_text(payload["raw_text"]).model_dump(mode="json")
    if name == "match_rubric":
        rubric = [RubricCriterion.model_validate(x) for x in payload["rubric"]]
        nlp = NLPAnalysisOutput.model_validate(payload["nlp_analysis"])
        return match_rubric(rubric, payload["raw_text"], nlp).model_dump(mode="json")
    if name == "generate_feedback_report":
        rubric_result = RubricMatchOutput.model_validate(payload["rubric_result"])
        nlp = NLPAnalysisOutput.model_validate(payload["nlp_analysis"])
        return generate_feedback_report(rubric_result, nlp).model_dump(mode="json")
    raise ValueError(f"Unknown tool: {name}")
