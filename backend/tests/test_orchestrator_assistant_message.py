from app.mcp.orchestrator import _assistant_message


def test_assistant_message_for_analysis_contains_details() -> None:
    state = {
        "nlp_analysis": {
            "grammar_errors": [
                {"type": "grammar", "message": "Use 'an' before a vowel.", "offset": 4},
                {"type": "style", "message": "Sentence is too long.", "offset": 19},
            ],
            "grammar_error_count": 2,
            "avg_sentence_length": 18.2,
            "passive_voice_ratio": 0.225,
            "ttr": 0.51,
            "paragraph_coherence": [
                {
                    "paragraph_index": 0,
                    "score": 3,
                    "issues": ["Weak transition", "Abrupt ending"],
                    "suggestions": ["Add transition sentence"],
                }
            ],
            "overall_flow_score": 3.7,
            "flow_comments": "Flow is mostly clear with minor transitions missing.",
        }
    }

    message = _assistant_message(state)

    assert "Writing analysis complete" in message
    assert "Grammar issues found: 2" in message
    assert "Use 'an' before a vowel." in message
    assert "Flow score: 3.7/5" in message
    assert "Paragraph 1" in message


def test_assistant_message_for_rubric_contains_scores() -> None:
    state = {
        "rubric_result": {
            "rubric_scores": [
                {
                    "criterion": "Thesis",
                    "max_points": 20,
                    "awarded_points": 16,
                    "justification": "Mostly clear.",
                    "strengths": ["Specific claim"],
                    "improvements": ["Clarify scope"],
                    "evidence_quotes": [],
                }
            ],
            "total_score": 16,
            "total_possible": 20,
        }
    }

    message = _assistant_message(state)

    assert "Rubric scoring complete" in message
    assert "Total score: 16.0/20.0" in message
    assert "Thesis: 16.0/20.0" in message
