from pathlib import Path

from app.agents.ingestion_agent import ingest_document
from app.agents.nlp_agent import analyze_text
from app.agents.report_agent import generate_feedback_report
from app.agents.rubric_agent import match_rubric
from app.models.feedback import FeedbackRecord, FeedbackRunRequest, IngestInput
from app.models.rubric import RubricRecord
from app.utils.storage import storage


def run_feedback_pipeline(payload: FeedbackRunRequest) -> FeedbackRecord:
    rubric_path = storage.rubric_dir / f"{payload.rubric_id}.json"
    if not rubric_path.exists():
        raise FileNotFoundError("Rubric not found.")
    rubric = RubricRecord.model_validate(storage.read_json(rubric_path))

    upload_meta_path = storage.upload_dir / f"{payload.file_id}.json"
    if not upload_meta_path.exists():
        raise FileNotFoundError("Uploaded file metadata not found.")
    upload_meta = storage.read_json(upload_meta_path)

    ingest = ingest_document(
        IngestInput(file_path=upload_meta["file_path"], file_type=upload_meta["file_type"])
    )
    analysis = analyze_text(ingest.raw_text)
    rubric_match = match_rubric(rubric.criteria, ingest.raw_text, analysis)
    report = generate_feedback_report(rubric_match, analysis)

    feedback_id = storage.new_id()
    record = FeedbackRecord(
        feedback_id=feedback_id,
        rubric_id=payload.rubric_id,
        file_id=payload.file_id,
        report=report,
        ingest=ingest,
        analysis=analysis,
        rubric_match=rubric_match,
    )
    storage.write_json(storage.feedback_dir / f"{feedback_id}.json", record.model_dump(mode="json"))
    return record


def load_feedback(feedback_id: str) -> FeedbackRecord:
    feedback_path = storage.feedback_dir / f"{feedback_id}.json"
    if not Path(feedback_path).exists():
        raise FileNotFoundError("Feedback not found.")
    return FeedbackRecord.model_validate(storage.read_json(feedback_path))
