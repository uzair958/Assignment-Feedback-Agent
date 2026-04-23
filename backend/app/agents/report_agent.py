from app.models.feedback import FeedbackReport, NLPAnalysisOutput, RubricMatchOutput
from app.utils.groq_client import groq_client


def generate_feedback_report(
    rubric_result: RubricMatchOutput, nlp_analysis: NLPAnalysisOutput
) -> FeedbackReport:
    prompt = (
        "Generate student feedback report JSON with keys: overall_summary, top_strengths, "
        "priority_improvements, suggested_next_steps.\n\n"
        f"Rubric Scores: {rubric_result.model_dump_json()}\n"
        f"NLP Analysis: {nlp_analysis.model_dump_json()}\n"
        f"Total Score: {rubric_result.total_score}/{rubric_result.total_possible}"
    )
    result = groq_client.call_json(
        prompt=prompt,
        system=(
            "You are a compassionate academic writing coach. "
            "Return valid JSON only."
        ),
    )

    return FeedbackReport(
        overall_summary=str(result.get("overall_summary", "Feedback generated.")),
        total_score=rubric_result.total_score,
        total_possible=rubric_result.total_possible,
        grade_breakdown=rubric_result.rubric_scores,
        top_strengths=[str(x) for x in result.get("top_strengths", [])][:3],
        priority_improvements=[str(x) for x in result.get("priority_improvements", [])][:5],
        suggested_next_steps=[str(x) for x in result.get("suggested_next_steps", [])][:5],
    )
