from app.agents.nlp_agent import analyze_text
from app.agents.report_agent import generate_feedback_report
from app.agents.rubric_agent import match_rubric
from app.models.rubric import RubricCriterion


def test_rubric_and_report_shapes() -> None:
    text = "Introduction.\n\nThis assignment presents a clear thesis and evidence."
    analysis = analyze_text(text)
    rubric = [
        RubricCriterion(
            name="Thesis Clarity",
            max_points=20,
            description="Is the thesis clearly stated?",
        )
    ]
    rubric_result = match_rubric(rubric, text, analysis)
    report = generate_feedback_report(rubric_result, analysis)

    assert rubric_result.total_possible == 20
    assert len(report.grade_breakdown) == 1
