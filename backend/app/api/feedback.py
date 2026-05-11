from fastapi import APIRouter, HTTPException

from app.agents.coordinator import load_feedback, run_feedback_pipeline
from app.models.feedback import FeedbackRecord, FeedbackRunRequest

router = APIRouter(tags=["feedback"])


@router.post("/feedback/run", response_model=FeedbackRecord)
def run_feedback(payload: FeedbackRunRequest) -> FeedbackRecord:
    try:
        return run_feedback_pipeline(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}") from exc


@router.post("/feedback", response_model=FeedbackRecord)
def run_feedback_alias(payload: FeedbackRunRequest) -> FeedbackRecord:
    return run_feedback(payload)


@router.get("/feedback/{feedback_id}", response_model=FeedbackRecord)
def get_feedback(feedback_id: str) -> FeedbackRecord:
    try:
        return load_feedback(feedback_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
