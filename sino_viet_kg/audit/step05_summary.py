"""Bước 05 — tổng hợp các chỉ số gold-free của Bảng 3 vào results/audit/05_summary/.

Dòng "Entity recall (capture–recapture)" của Bảng 3 tính riêng bằng
`python3 -m sino_viet_kg.evaluation.capture_recapture corpus`.
"""
from sino_viet_kg.audit import state as S
from sino_viet_kg.fileio import write_json, write_text

STEP = "05_summary"
DEPENDS = ("00_load", "01_structural", "02_dictionary", "03_recall", "04_consistency")


def _run():
    structural = S.load_summary("01_structural").get("rates_pct", {})
    dictionary = S.load_summary("02_dictionary")
    recall = S.load_summary("03_recall")
    consistency = S.load_summary("04_consistency")
    table = [
        ("Entity grounding", f"{structural['entity_grounding']}%"),
        ("Label validity", f"{structural['label_valid']}%"),
        ("Label consistency", f"{structural['label_consistency']}%"),
        ("Predicate validity", f"{structural['predicate_valid']}%"),
        ("Triple-ID integrity", f"{structural['triple_id_integrity']}%"),
        ("Links phonetically confirmed (dict.)", f"{dictionary['confirmed_pct']}%"),
        ("Proxy precision (dict. oracle)", f"{recall['proxy_precision_pct']}%"),
        ("Proxy recall miss", f"{recall['proxy_recall_miss_pct']}%"),
        ("Alignment symmetry (zh / vi)",
         f"{consistency['zh_align_symmetry_pct']} / {consistency['vi_align_symmetry_pct']}%"),
        ("Triple parallelism (zh / vi)",
         f"{consistency['triple_parallel_zh_pct']} / {consistency['triple_parallel_vi_pct']}%"),
    ]
    totals = S.read_state("00_load").get("counts", {})
    out_dir = S.step_dir(STEP)
    write_json(out_dir / "table3.json", {"totals": totals, "checks": dict(table)})
    md = ["# Bảng 3 — Gold-free verification", "",
          f"{totals.get('pairs', 0):,} cặp câu; {totals.get('entities', 0):,} thực thể, "
          f"{totals.get('triples', 0):,} bộ ba, {totals.get('alignments', 0):,} liên kết.", "",
          "| Verification check | Result |", "|---|---|"]
    md += [f"| {k} | {v} |" for k, v in table]
    write_text(out_dir / "table3.md", "\n".join(md) + "\n")
    S.mark_done(STEP, outputs=[out_dir / "table3.json", out_dir / "table3.md"], counts=dict(table))
    print("\n".join(md))


def run():
    for dep in DEPENDS:
        S.require_done(dep)
    S.run_step(STEP, _run)


if __name__ == "__main__":
    run()
