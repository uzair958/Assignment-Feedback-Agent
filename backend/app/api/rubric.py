from fastapi import APIRouter, HTTPException

from app.models.rubric import RubricCreateRequest, RubricRecord
from app.utils.storage import storage

router = APIRouter(tags=["rubric"])


@router.post("/rubric", response_model=RubricRecord)
def create_rubric(payload: RubricCreateRequest) -> RubricRecord:
    rubric_id = storage.new_id()
    record = RubricRecord(rubric_id=rubric_id, criteria=payload.criteria)
    storage.write_json(storage.rubric_dir / f"{rubric_id}.json", record.model_dump(mode="json"))
    return record


@router.get("/rubric/{rubric_id}", response_model=RubricRecord)
def get_rubric(rubric_id: str) -> RubricRecord:
    path = storage.rubric_dir / f"{rubric_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Rubric not found.")
    return RubricRecord.model_validate(storage.read_json(path))
