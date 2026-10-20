"""Gọi Gemini 2.5 Flash cho một lô cặp câu và đọc kết quả JSON (Mục 3.2, Phụ lục).

Chế độ JSON (`response_mime_type = application/json`) gắn với `RESPONSE_SCHEMA`, temperature
0.1. JSON lỗi được sửa một lần (bỏ rào ```, cắt phần chữ thừa) rồi parse lại; vẫn lỗi thì
gọi lại mô hình.
"""
from __future__ import annotations

import json
import re
import time

from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

PROMPT_INPUT_PLACEHOLDER = "{INPUT}"

_ENTITY_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "text": {"type": "string"},
        "label": {"type": "string"},
        "confidence": {
            "type": "number",
            "description": (
                "Độ tin cậy của LLM cho việc trích entity này (0.0-1.0). "
                "1.0 = rất chắc chắn (nhân vật/địa danh nổi bật, không nhập "
                "nhằng); 0.5 = mơ hồ (vd ranh giới span không rõ)."
            ),
        },
    },
    "required": ["id", "text", "label"],
}
_TRIPLE_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "subject": {"type": "string"},
        "predicate": {"type": "string"},
        "object": {"type": "string"},
        "confidence": {"type": "number"},
        "evidence": {"type": "string"},
    },
    "required": ["subject", "predicate", "object"],
}
_SIDE_SCHEMA = {
    "type": "object",
    "properties": {
        "entities": {"type": "array", "items": _ENTITY_ITEM_SCHEMA},
        "triples": {"type": "array", "items": _TRIPLE_ITEM_SCHEMA},
    },
    "required": ["entities", "triples"],
}
_ALIGNMENT_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "zh_id": {"type": "string"},
        "vi_id": {"type": "string"},
        "confidence": {"type": "number"},
        "note": {"type": "string"},
    },
    "required": ["zh_id", "vi_id", "confidence"],
}
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pair_id": {"type": "string", "description": "Exact pair_id from the input."},
                    "zh": _SIDE_SCHEMA,
                    "vi": _SIDE_SCHEMA,
                    "alignment": {"type": "array", "items": _ALIGNMENT_ITEM_SCHEMA},
                },
                "required": ["pair_id", "zh", "vi", "alignment"],
            },
        }
    },
    "required": ["results"],
}


class InvalidJSONError(ValueError):
    """Mô hình trả về chuỗi không parse được kể cả sau khi sửa."""


class QuotaExhaustedError(RuntimeError):
    """Hết hạn mức theo ngày: dừng lượt chạy (phần đã xong nằm trong đệm)."""


def render_batch_prompt(template: str, items: list[tuple[str, str, str]]) -> str:
    """Chèn lô (pair_id, Hán, Việt) vào chỗ `{INPUT}` của prompt."""
    block = "\n\n".join(f"[pair_id={pid}]\n[Hán]: {zh}\n[Việt]: {vi}" for pid, zh, vi in items)
    if PROMPT_INPUT_PLACEHOLDER in template:
        return template.replace(PROMPT_INPUT_PLACEHOLDER, block)
    return f"{template.rstrip()}\n\n--- BATCH INPUT ---\n{block}\n"


def _repair_json(raw: str) -> str:
    """Bỏ rào ```...``` và phần chữ đứng trước dấu { hoặc [ đầu tiên."""
    s = raw.strip()
    if s.startswith("```"):
        nl = s.find("\n")
        if nl > 0:
            s = s[nl + 1:]
        s = s.removesuffix("```").strip()
    if s and s[0] not in "{[":
        starts = [i for i in (s.find("{"), s.find("[")) if i >= 0]
        if starts:
            s = s[min(starts):]
    return s


def parse_results(raw: str) -> dict[str, dict]:
    """JSON của mô hình -> {pair_id: {zh: {entities, triples}, vi: {...}, alignment}}."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        try:
            data = json.loads(_repair_json(raw))
        except json.JSONDecodeError as exc:
            raise InvalidJSONError(str(exc)) from exc
    out = {}
    for r in data.get("results", []) or []:
        pid = r.get("pair_id")
        if not pid:
            continue
        sides = {}
        for side in ("zh", "vi"):
            blk = r.get(side) or {}
            sides[side] = {"entities": blk.get("entities", []) or [],
                           "triples": blk.get("triples", []) or []}
        out[str(pid)] = {**sides, "alignment": r.get("alignment", []) or []}
    return out


def _retry_delay(exc: Exception) -> float | None:
    """Thời gian chờ mà API gợi ý trong lỗi 429, nếu có."""
    m = re.search(r"retry in ([\d.]+)\s*s", str(exc), re.IGNORECASE) \
        or re.search(r"'retryDelay':\s*'([\d.]+)s'", str(exc))
    return float(m.group(1)) if m else None


class GeminiClient:
    def __init__(self, api_key: str, model: str, temperature: float = 0.1) -> None:
        from google import genai
        from google.genai import types

        self._client = genai.Client(api_key=api_key)
        self._config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
            max_output_tokens=65536,
        )
        self.model = model
        self.calls = 0

    @retry(stop=stop_after_attempt(8), wait=wait_exponential(multiplier=2, min=2, max=60),
           retry=retry_if_exception(lambda e: not isinstance(e, QuotaExhaustedError)), reraise=True)
    def _generate(self, prompt: str) -> dict[str, dict]:
        self.calls += 1
        try:
            resp = self._client.models.generate_content(
                model=self.model, contents=prompt, config=self._config)
        except Exception as exc:
            if "RESOURCE_EXHAUSTED" in str(exc) or getattr(exc, "code", None) == 429:
                if "PerDay" in str(exc):
                    raise QuotaExhaustedError(str(exc)) from exc
                delay = _retry_delay(exc)
                if delay:
                    time.sleep(delay)
            raise
        if not getattr(resp, "text", None):
            raise RuntimeError("Gemini trả về rỗng")
        return parse_results(resp.text)

    def call_batch(self, prompt_template: str, items: list[tuple[str, str, str]]) -> dict[str, dict]:
        """items: [(pair_id, câu Hán, câu Việt)] -> kết quả theo pair_id."""
        if not items:
            return {}
        return self._generate(render_batch_prompt(prompt_template, items))
