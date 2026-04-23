from pathlib import Path

from app.utils.file_parser import parse_file


def test_parse_txt_file(tmp_path: Path) -> None:
    p = tmp_path / "sample.txt"
    p.write_text("INTRODUCTION\n\nThis is a sample paragraph.", encoding="utf-8")

    result = parse_file(str(p), "txt")
    assert result.word_count > 0
    assert result.paragraph_count == 2
