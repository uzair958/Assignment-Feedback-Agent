import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.config import settings


class JsonStorage:
    def __init__(self) -> None:
        self.base_dir = Path(settings.data_dir)
        self.upload_dir = self.base_dir / "uploads"
        self.rubric_dir = self.base_dir / "rubrics"
        self.feedback_dir = self.base_dir / "feedback"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.rubric_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)

    def new_id(self) -> str:
        return uuid4().hex

    def write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def read_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))


storage = JsonStorage()
