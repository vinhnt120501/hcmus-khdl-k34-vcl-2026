"""Bước 03 — từ điển làm bộ gióng độc lập (Bảng 3: proxy precision, proxy recall miss).

Trong mỗi cặp câu, từ điển tự ghép thực thể Hán với thực thể Việt (tập D) và so với liên kết
LLM đề xuất (tập L): proxy precision = |D ∩ L| / |D|, recall miss = |D \\ L| / |D|.
"""
from sino_viet_kg.audit import state as S
from sino_viet_kg.audit.reading_dictionary import dictionary_match
from sino_viet_kg.fileio import jsonl_read, jsonl_write, write_json

STEP = "03_recall"
DICT_ALIGN_LEVELS = ("EXACT", "NO_DIACRITIC", "REORDERED")


def _run():
    src = S.step_dir("00_load") / "pairs.jsonl"
    n_L = n_D = n_agree = 0
    misses = []
    for p in jsonl_read(src):
        zents = p["zh"]["entities"]; vents = p["vi"]["entities"]
        L = set((a.get("zh_id"), a.get("vi_id")) for a in p["alignment"])
        n_L += len(L)
        D = set()
        for ze in zents:
            for ve in vents:
                if dictionary_match(ze.get("text", ""), ve.get("text", ""))["match_type"] in DICT_ALIGN_LEVELS:
                    D.add((ze.get("id"), ve.get("id")))
                    break  # mỗi thực thể Hán lấy thực thể Việt khớp đầu tiên
        n_D += len(D)
        n_agree += len(D & L)
        for k in (D - L):
            zt = next((e.get("text") for e in zents if e.get("id") == k[0]), "")
            vt = next((e.get("text") for e in vents if e.get("id") == k[1]), "")
            misses.append({"pair_id": p["pair_id"], "zh_id": k[0], "vi_id": k[1],
                           "zh_text": zt, "vi_text": vt})

    out_path = S.step_dir(STEP) / "recall_miss.jsonl"
    jsonl_write(out_path, misses)
    n_miss = len(misses)
    counts = {
        "llm_alignments": n_L, "dict_alignments": n_D, "agree": n_agree,
        "recall_miss": n_miss,
        "proxy_precision_pct": round(100 * n_agree / n_D, 2) if n_D else None,
        "proxy_recall_miss_pct": round(100 * n_miss / n_D, 2) if n_D else None,
    }
    write_json(S.step_dir(STEP) / "summary.json", counts)
    S.mark_done(STEP, outputs=[out_path], counts=counts)
    print(f"[{STEP}] {counts}")


def run():
    S.require_done("00_load")
    S.run_step(STEP, _run, inputs=[S.step_dir("00_load") / "pairs.jsonl"])


if __name__ == "__main__":
    run()
