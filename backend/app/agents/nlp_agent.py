import re
from statistics import mean

import language_tool_python
import spacy

from app.models.feedback import GrammarError, NLPAnalysisOutput, ParagraphCoherence
from app.utils.groq_client import groq_client

try:
    _tool = language_tool_python.LanguageTool("en-US")
except Exception:  # pragma: no cover - external binary setup
    _tool = None

try:
    _nlp = spacy.load("en_core_web_sm")
except Exception:  # pragma: no cover - fallback when model unavailable
    _nlp = spacy.blank("en")


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def analyze_text(raw_text: str) -> NLPAnalysisOutput:
    matches = _tool.check(raw_text) if _tool else []
    grammar_errors = [
        GrammarError(type=m.ruleIssueType or "UNKNOWN", message=m.message, offset=m.offset)
        for m in matches[:50]
    ]

    if "sentencizer" not in _nlp.pipe_names:
        _nlp.add_pipe("sentencizer")
    doc = _nlp(raw_text)
    sentence_lengths = [len([t for t in sent if not t.is_punct]) for sent in doc.sents]
    avg_sentence_length = float(mean(sentence_lengths)) if sentence_lengths else 0.0

    total_sentences = max(1, len(sentence_lengths))
    passive_count = sum(1 for sent in doc.sents if any(t.dep_ == "auxpass" for t in sent))
    passive_ratio = passive_count / total_sentences

    tokens = [t.lemma_.lower() for t in doc if t.is_alpha]
    ttr = (len(set(tokens)) / len(tokens)) if tokens else 0.0

    paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
    coherence: list[ParagraphCoherence] = []
    for idx, paragraph in enumerate(paragraphs[:10]):
        prompt = (
            "Analyze this paragraph for coherence and return JSON with "
            "coherence_score (1-5), issues (list), suggestions (list).\n\n"
            f"Paragraph:\n{paragraph}"
        )
        result = groq_client.call_json(
            prompt=prompt,
            system="You are an academic writing evaluator. Return valid JSON only.",
        )
        coherence.append(
            ParagraphCoherence(
                paragraph_index=idx,
                score=int(result.get("coherence_score", 3)),
                issues=[str(x) for x in result.get("issues", [])][:5],
                suggestions=[str(x) for x in result.get("suggestions", [])][:5],
            )
        )

    flow_prompt = (
        "Evaluate logical flow between sections and return JSON with "
        "overall_flow_score (1-5) and flow_comments.\n\n"
        f"Text:\n{raw_text[:6000]}"
    )
    flow_json = groq_client.call_json(
        prompt=flow_prompt,
        system="You are an academic writing evaluator. Return valid JSON only.",
    )

    return NLPAnalysisOutput(
        grammar_errors=grammar_errors,
        grammar_error_count=len(grammar_errors),
        avg_sentence_length=round(avg_sentence_length, 2),
        passive_voice_ratio=round(passive_ratio, 3),
        ttr=round(ttr, 3),
        paragraph_coherence=coherence,
        overall_flow_score=float(flow_json.get("overall_flow_score", 3.0)),
        flow_comments=str(flow_json.get("flow_comments", "Flow appears acceptable.")),
    )
