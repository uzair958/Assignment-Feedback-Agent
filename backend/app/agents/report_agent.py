from app.models.feedback import FeedbackReport, NLPAnalysisOutput, RubricMatchOutput
from app.utils.groq_client import groq_client


def generate_feedback_report(
    rubric_result: RubricMatchOutput, nlp_analysis: NLPAnalysisOutput
) -> FeedbackReport:
    prompt = (
        "Generate a student feedback report based on the rubric scores and NLP analysis below.\n\n"
        f"Rubric Scores: {rubric_result.model_dump_json()}\n"
        f"NLP Analysis: {nlp_analysis.model_dump_json()}\n"
        f"Total Score: {rubric_result.total_score}/{rubric_result.total_possible}\n\n"
        "Return ONLY a JSON object with EXACTLY these keys:\n"
        "{\n"
        '  "overall_summary": "<2-3 sentence summary of the student\'s performance>",\n'
        '  "top_strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],\n'
        '  "priority_improvements": ["<improvement 1>", "<improvement 2>", "<improvement 3>"],\n'
        '  "suggested_next_steps": ["<action step 1>", "<action step 2>", "<action step 3>"]\n'
        "}"
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
