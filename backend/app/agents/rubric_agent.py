from app.models.feedback import CriterionScore, NLPAnalysisOutput, RubricMatchOutput
from app.models.rubric import RubricCriterion
from app.utils.groq_client import groq_client


def _excerpt_for_criterion(raw_text: str, criterion: RubricCriterion) -> str:
    # Simple heuristic extractor; can be replaced with retrieval later.
    snippet = raw_text[:1800]
    return snippet


def match_rubric(
    rubric: list[RubricCriterion], raw_text: str, nlp_analysis: NLPAnalysisOutput
) -> RubricMatchOutput:
    rubric_scores: list[CriterionScore] = []

    for criterion in rubric:
        excerpt = _excerpt_for_criterion(raw_text, criterion)
        prompt = (
            "Evaluate the submission against this rubric criterion and return JSON with:\n"
            "awarded_points (0..max_points), justification, strengths (list), improvements (list), "
            "evidence_quotes (list from student text).\n\n"
            f"Criterion: {criterion.name}\n"
            f"Description: {criterion.description}\n"
            f"Max Points: {criterion.max_points}\n"
            f"Student Text Excerpt:\n{excerpt}\n"
            f"NLP Data Summary: grammar_errors={nlp_analysis.grammar_error_count}, "
            f"ttr={nlp_analysis.ttr}, flow={nlp_analysis.overall_flow_score}"
        )

        result = groq_client.call_json(
            prompt=prompt,
            system=(
                "You are an academic evaluator. Ground scoring in evidence. "
                "Return only valid JSON."
            ),
        )
        awarded = float(result.get("awarded_points", 0.0))
        awarded = max(0.0, min(criterion.max_points, awarded))
        rubric_scores.append(
            CriterionScore(
                criterion=criterion.name,
                max_points=criterion.max_points,
                awarded_points=round(awarded, 2),
                justification=str(result.get("justification", "Insufficient evidence provided.")),
                strengths=[str(x) for x in result.get("strengths", [])][:5],
                improvements=[str(x) for x in result.get("improvements", [])][:5],
                evidence_quotes=[str(x) for x in result.get("evidence_quotes", [])][:5],
            )
        )

    total_score = round(sum(item.awarded_points for item in rubric_scores), 2)
    total_possible = round(sum(item.max_points for item in rubric_scores), 2)
    return RubricMatchOutput(
        rubric_scores=rubric_scores, total_score=total_score, total_possible=total_possible
    )
