from app.models.feedback import IngestInput, IngestOutput
from app.utils.file_parser import parse_file


def ingest_document(payload: IngestInput) -> IngestOutput:
    return parse_file(payload.file_path, payload.file_type)
