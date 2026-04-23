from pydantic import BaseModel, Field

from app.models.rubric import RubricCriterion


class IngestInput(BaseModel):
    file_path: str
    file_type: str


class IngestOutput(BaseModel):
    raw_text: str
    word_count: int
    paragraph_count: int
    detected_sections: list[str]
    language: str = "en"


class GrammarError(BaseModel):
    type: str
    message: str
    offset: int


class ParagraphCoherence(BaseModel):
    paragraph_index: int
    score: int = Field(ge=1, le=5)
    issues: list[str]
    suggestions: list[str]


class NLPAnalysisOutput(BaseModel):
    grammar_errors: list[GrammarError]
    grammar_error_count: int
    avg_sentence_length: float
    passive_voice_ratio: float
    ttr: float
    paragraph_coherence: list[ParagraphCoherence]
    overall_flow_score: float
    flow_comments: str


class CriterionScore(BaseModel):
    criterion: str
    max_points: float
    awarded_points: float
    justification: str
    strengths: list[str]
    improvements: list[str]
    evidence_quotes: list[str] = Field(default_factory=list)


class RubricMatchOutput(BaseModel):
    rubric_scores: list[CriterionScore]
    total_score: float
    total_possible: float


class FeedbackReport(BaseModel):
    overall_summary: str
    total_score: float
    total_possible: float
    grade_breakdown: list[CriterionScore]
    top_strengths: list[str]
    priority_improvements: list[str]
    suggested_next_steps: list[str]


class FeedbackRunRequest(BaseModel):
    file_id: str
    rubric_id: str


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    file_path: str
    file_type: str
    size_bytes: int


class FeedbackRecord(BaseModel):
    feedback_id: str
    rubric_id: str
    file_id: str
    report: FeedbackReport
    ingest: IngestOutput
    analysis: NLPAnalysisOutput
    rubric_match: RubricMatchOutput


class ErrorEnvelope(BaseModel):
    error: str
    detail: str | None = None
