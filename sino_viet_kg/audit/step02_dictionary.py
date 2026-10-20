"""Bước 02 — tra từ điển âm Hán–Việt cho từng liên kết LLM đề xuất (Bảng 3: "Links phonetically
confirmed"). Tỉ lệ = số liên kết khớp ở mức xác nhận / số liên kết có hai đầu hợp lệ.
"""
from collections import Counter

from sino_viet_kg.audit import state as S
from sino_viet_kg.audit.reading_dictionary import dictionary_match
from sino_viet_kg.fileio import jsonl_read, jsonl_write, write_json

STEP = "02_dictionary"


def _run():
    src = S.step_dir("00_load") / "pairs.jsonl"
    align_path = S.step_dir(STEP) / "alignments.jsonl"
    by_type = Counter()
    aligns = []

    for p in jsonl_read(src):
        zmap = {e.get("id"): e.get("text", "") for e in p["zh"]["entities"]}
        vmap = {e.get("id"): e.get("text", "") for e in p["vi"]["entities"]}
        for a in p["alignment"]:
            zt = zmap.get(a.get("zh_id")); vt = vmap.get(a.get("vi_id"))
            if zt is None or vt is None:
                continue  # id không hợp lệ: đã tính ở bước 01
            m = dictionary_match(zt, vt)
            rec = {
                "pair_id": p["pair_id"], "zh_id": a.get("zh_id"), "vi_id": a.get("vi_id"),
                "zh_text": zt, "vi_text": vt,
                "llm_conf": a.get("confidence"), "llm_note": a.get("note"),
                "match_type": m["match_type"], "matched_candidate": m["matched_candidate"],
                "confirmed": m["confirmed"],
            }
            by_type[m["match_type"]] += 1
            aligns.append(rec)

    jsonl_write(align_path, aligns)
    n_total = len(aligns)
    n_confirmed = sum(1 for a in aligns if a["confirmed"])
    counts = {
        "total_alignments": n_total,
        "confirmed": n_confirmed,
        "confirmed_pct": round(100 * n_confirmed / n_total, 2) if n_total else None,
        "by_match_type": dict(by_type),
    }
    write_json(S.step_dir(STEP) / "summary.json", counts)
    S.mark_done(STEP, outputs=[align_path], counts=counts)
    print(f"[{STEP}] confirmed={n_confirmed}/{n_total} ({counts['confirmed_pct']}%) | {dict(by_type)}")


def run():
    S.require_done("00_load")
    S.run_step(STEP, _run, inputs=[S.step_dir("00_load") / "pairs.jsonl"])


if __name__ == "__main__":
    run()
