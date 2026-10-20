"""Trạng thái từng bước của audit (pending | running | done | error), lưu ở results/audit/."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from sino_viet_kg.paths import AUDIT_OUT_DIR

# Thứ tự các bước; tên trùng module `step<tên>.py`.
STEPS = [
    ("00_load", "Nạp kết quả trích xuất"),
    ("01_structural", "Grounding và tính hợp lệ theo schema"),
    ("02_dictionary", "Kiểm tra liên kết bằng từ điển âm Hán–Việt"),
    ("03_recall", "Từ điển làm bộ gióng độc lập: proxy precision, recall miss"),
    ("04_consistency", "Nhất quán song ngữ: đối xứng liên kết, song song bộ ba"),
    ("05_summary", "Tổng hợp Bảng 3"),
]
TITLES = dict(STEPS)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def step_dir(step: str) -> Path:
    d = AUDIT_OUT_DIR / step
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_state(step: str) -> dict:
    p = step_dir(step) / "state.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"step": step, "status": "pending"}


def write_state(step: str, **fields) -> dict:
    p = step_dir(step) / "state.json"
    st = read_state(step)
    st.update(fields)
    st["step"] = step
    p.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
    update_pipeline_state()
    return st


def mark_running(step: str, inputs=None) -> None:
    write_state(step, title=TITLES[step], status="running", started_at=now_iso(),
                finished_at=None, inputs=[str(i) for i in inputs or []],
                outputs=[], counts={}, error=None)


def mark_done(step: str, outputs=None, counts=None, params=None) -> None:
    write_state(step, status="done", finished_at=now_iso(),
                outputs=[str(o) for o in outputs or []], counts=counts or {}, params=params or {})


def mark_error(step: str, msg: str) -> None:
    write_state(step, status="error", finished_at=now_iso(), error=msg)


def update_pipeline_state() -> None:
    AUDIT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    steps = []
    for s, title in STEPS:
        sp = AUDIT_OUT_DIR / s / "state.json"
        if sp.exists():
            st = json.loads(sp.read_text(encoding="utf-8"))
            steps.append({
                "step": s, "title": title, "status": st.get("status", "pending"),
                "finished_at": st.get("finished_at"), "counts": st.get("counts", {}),
            })
        else:
            steps.append({"step": s, "title": title, "status": "pending"})
    (AUDIT_OUT_DIR / "pipeline_state.json").write_text(
        json.dumps({"updated_at": now_iso(), "steps": steps}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def require_done(step: str) -> None:
    st = read_state(step)
    if st.get("status") != "done":
        raise SystemExit(f"[!] Bước phụ thuộc '{step}' chưa 'done' (status={st.get('status')}). "
                         f"Hãy chạy bước đó trước.")


def load_summary(step: str) -> dict:
    p = step_dir(step) / "summary.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def run_step(step: str, body, inputs=None) -> None:
    """Chạy `body()` giữa mark_running và (mark_done do body tự gọi) / mark_error."""
    mark_running(step, inputs)
    try:
        body()
    except Exception as e:  # noqa: BLE001
        mark_error(step, repr(e))
        raise
