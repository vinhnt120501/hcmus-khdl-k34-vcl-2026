"""Đọc kết quả trích xuất LLM (`row_*.json`, mỗi tệp một đoạn, mỗi extraction một cặp câu)."""
import json
from pathlib import Path

from sino_viet_kg import paths


def row_files(rows_dir: Path = None, max_rows: int = None) -> list[Path]:
    rows_dir = paths.require(Path(rows_dir or paths.llm_rows_dir()), "kết quả trích xuất (row_*.json)")
    files = sorted(rows_dir.glob("row_*.json"))
    return files[:max_rows] if max_rows else files


def iter_extractions(rows_dir: Path = None, max_rows: int = None, skip_errors: bool = True):
    """Yield từng extraction (một cặp câu) theo thứ tự tệp."""
    for f in row_files(rows_dir, max_rows):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for ex in rec.get("extractions", []):
            if skip_errors and ex.get("error"):
                continue
            yield ex


def entities(ex: dict, side: str) -> list[dict]:
    return (ex.get(side) or {}).get("entities", []) or []
