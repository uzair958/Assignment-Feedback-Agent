from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.models.feedback import UploadResponse
from app.utils.storage import storage

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_assignment(file: UploadFile = File(...)) -> UploadResponse:
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(status_code=413, detail="File exceeds max size.")

    ext = Path(file.filename or "").suffix.lower().replace(".", "")
    if ext not in {"txt", "pdf", "docx"}:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    file_id = storage.new_id()
    target_path = storage.upload_dir / f"{file_id}.{ext}"
    target_path.write_bytes(content)

    resp = UploadResponse(
        file_id=file_id,
        filename=file.filename or target_path.name,
        file_path=str(target_path),
        file_type=ext,
        size_bytes=len(content),
    )
    storage.write_json(storage.upload_dir / f"{file_id}.json", resp.model_dump(mode="json"))
    return resp
