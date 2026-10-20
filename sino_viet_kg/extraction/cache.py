"""Đệm kết quả trích xuất theo nội dung (content-addressed): chạy lại chỉ gọi mô hình cho cặp chưa có.

Khoá = hash prompt + hash cặp câu; tệp đệm nằm ở
`<VCL_CORPUS_DIR>/2_llm_output/<mô hình>/_cache/joint/<prompt_hash>/<content_hash>.json`.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sino_viet_kg import paths


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prompt_hash(template: str) -> str:
    return _sha256(template)


def content_hash(zh_text: str, vi_text: str) -> str:
    return _sha256(f"{zh_text}|||ZH-VI|||{vi_text}")


class Cache:
    def __init__(self, model: str, prompt_template: str) -> None:
        self.prompt_hash = prompt_hash(prompt_template)
        self.root = paths.llm_dir(model) / "_cache" / "joint" / self.prompt_hash[:12]

    def _path(self, c_hash: str) -> Path:
        return self.root / f"{c_hash[:16]}.json"

    def load(self, c_hash: str) -> dict | None:
        try:
            return json.loads(self._path(c_hash).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def save(self, c_hash: str, payload: dict) -> None:
        path = self._path(c_hash)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
