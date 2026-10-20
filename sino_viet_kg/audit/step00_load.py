"""Bước 00 — gộp `row_*.json` của lượt trích xuất thành pairs.jsonl (một dòng một cặp câu)."""
from sino_viet_kg import paths
from sino_viet_kg.audit import state as S
from sino_viet_kg.fileio import jsonl_write
from sino_viet_kg.kg import iter_extractions

STEP = "00_load"


def _run():
    rows_dir = paths.llm_rows_dir()
    out = S.step_dir(STEP) / "pairs.jsonl"
    n = {"pairs": 0, "entities": 0, "triples": 0, "alignments": 0}

    def gen():
        for e in iter_extractions(rows_dir, skip_errors=False):
            zh = e.get("zh") or {}
            vi = e.get("vi") or {}
            ze, vi_e = zh.get("entities", []) or [], vi.get("entities", []) or []
            zt, vt = zh.get("triples", []) or [], vi.get("triples", []) or []
            al = e.get("alignment", []) or []
            n["pairs"] += 1
            n["entities"] += len(ze) + len(vi_e)
            n["triples"] += len(zt) + len(vt)
            n["alignments"] += len(al)
            yield {
                "pair_id": e.get("pair_id"),
                "source_row": e.get("source_row"),
                "pair_index": e.get("pair_index"),
                "chinese": e.get("chinese", ""),
                "vietnamese": e.get("vietnamese", ""),
                "zh": {"entities": ze, "triples": zt},
                "vi": {"entities": vi_e, "triples": vt},
                "alignment": al,
                "error": e.get("error"),
            }

    jsonl_write(out, gen())
    S.mark_done(STEP, outputs=[out], counts=n, params={"rows_dir": str(rows_dir)})
    print(f"[{STEP}] rows={rows_dir} | {n}")


def run():
    S.run_step(STEP, _run, inputs=[paths.llm_rows_dir()])


if __name__ == "__main__":
    run()
