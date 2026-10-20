"""Đánh giá NER trên gold 3 người gán (Mục 4.4–4.5, Bảng 4–5).

- IAA: F1 exact giữa từng cặp người gán trên 800 đơn vị (cặp câu × phía).
- Gold = mention được ít nhất 2/3 người gán; chấm dự đoán LLM ở mức mention
  (khớp cả chuỗi lẫn nhãn): TP/FP/FN, P/R/F1 vi mô kèm 95% bootstrap CI
  (5,000 lần lấy mẫu lại theo cặp câu, seed 13), F1 theo nhãn, macro-F1, F1 theo phía.

    python3 -m sino_viet_kg.evaluation.eval_ner
"""
import itertools
import random

from sino_viet_kg import paths
from sino_viet_kg.annotation import (annotator_files, annotator_name, load_predictions,
                                     load_worksheet, majority_vote)
from sino_viet_kg.fileio import write_text
from sino_viet_kg.labels import ENTITY_LABELS, SIDES
from sino_viet_kg.metrics import pair_f1, prf, score_sets


def bootstrap_f1_ci(gold, preds, n_boot=5000, seed=13):
    """95% CI của micro-F1, lấy mẫu lại theo cặp câu (gồm cả hai phía)."""
    pids = sorted({pid for pid, _ in gold})
    rng, vals = random.Random(seed), []
    for _ in range(n_boot):
        tp = fp = fn = 0
        for pid in (rng.choice(pids) for _ in pids):
            for side in SIDES:
                g, p = gold.get((pid, side), set()), preds.get((pid, side), set())
                tp += len(g & p); fp += len(p - g); fn += len(g - p)
        vals.append(2 * tp / (2 * tp + fp + fn))
    vals.sort()
    return vals[int(0.025 * n_boot) - 1], vals[int(0.975 * n_boot) - 1]


def main():
    files = annotator_files()
    names = [annotator_name(f) for f in files]
    annots = [load_worksheet(f) for f in files]
    preds = load_predictions()

    L = ["# Đánh giá NER trên gold 3 người gán", ""]
    L.append(f"- Người gán: {', '.join(names)}; số đơn vị (cặp câu × phía) mỗi người: "
             f"{', '.join(str(len(a)) for a in annots)}")

    L += ["", "## Inter-annotator agreement (F1 exact)", "", "| Cặp | F1 |", "|---|---|"]
    iaas = []
    for i, j in itertools.combinations(range(len(annots)), 2):
        f = pair_f1(annots[i], annots[j]); iaas.append(f)
        L.append(f"| {names[i]}–{names[j]} | {f:.4f} |")
    L.append(f"\n- Trung bình: {sum(iaas)/len(iaas):.4f}")

    gold = majority_vote(annots)
    ex, per = score_sets(gold, preds)
    p, r, f = prf(ex["tp"], ex["fp"], ex["fn"])
    lo, hi = bootstrap_f1_ci(gold, preds)
    L += ["", "## Gold đồng thuận (≥ 2/3 người gán) vs LLM", "",
          f"- Mention gold: {ex['tp'] + ex['fn']}; mention dự đoán: {ex['tp'] + ex['fp']}",
          f"- TP={ex['tp']}  FP={ex['fp']}  FN={ex['fn']}",
          f"- Micro: P={p:.4f}  R={r:.4f}  F1={f:.4f}  [95% CI {lo:.3f}–{hi:.3f}]",
          "", "| Nhãn | P | R | F1 | TP | FP | FN |", "|---|---|---|---|---|---|---|"]
    f1s = []
    for lab in ENTITY_LABELS:
        c = per[lab]; pp, rr, ff = prf(c["tp"], c["fp"], c["fn"]); f1s.append(ff)
        L.append(f"| {lab} | {pp:.4f} | {rr:.4f} | {ff:.4f} | {c['tp']} | {c['fp']} | {c['fn']} |")
    L.append(f"\n- Macro-F1: {sum(f1s)/len(f1s):.4f}")
    for side in SIDES:
        g_side = {k: v for k, v in gold.items() if k[1] == side}
        ex2, _ = score_sets(g_side, preds)
        pp, rr, ff = prf(ex2["tp"], ex2["fp"], ex2["fn"])
        L.append(f"- Phía {side}: P={pp:.4f}  R={rr:.4f}  F1={ff:.4f}  ({len(g_side)} câu)")

    report = "\n".join(L) + "\n"
    out = paths.NER_REPORT_DIR / "ner_gold_evaluation.md"
    write_text(out, report)
    print(report)


if __name__ == "__main__":
    main()
