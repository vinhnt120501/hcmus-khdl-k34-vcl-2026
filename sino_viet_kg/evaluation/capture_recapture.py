"""Ước lượng recall bằng capture–recapture (Mục 4.5): Gemini 2.5 Flash (A) và Gemini 2.5 Pro (B).

Khớp mention theo (phía, chuỗi đã chuẩn hoá, nhãn). N̂ = N_A·N_B / N_AB, recall_A = N_AB / N_B.

    python3 -m sino_viet_kg.evaluation.capture_recapture gold
        400 cặp gold; so recall ước lượng với recall thật trên gold đồng thuận.
    python3 -m sino_viet_kg.evaluation.capture_recapture corpus
        Mẫu ngẫu nhiên 1,200 cặp; kèm 95% CI bootstrap (5,000 lần, theo cặp câu).
"""
import argparse
import json
import random

from sino_viet_kg import paths
from sino_viet_kg.annotation import annotator_files, load_predictions, load_worksheet, majority_vote
from sino_viet_kg.kg import entities, iter_extractions
from sino_viet_kg.labels import ENTITY_LABELS, SIDES
from sino_viet_kg.text import norm_mention

D = paths.CAPTURE_RECAPTURE_DIR


def _entity_set(ents) -> set:
    out = set()
    for e in ents:
        l = e.get("label", "").strip().upper()
        if l in ENTITY_LABELS:
            out.add((norm_mention(e["text"]), l))
    return out


def load_ext1_from_rows(rows_dir, pair_ids) -> dict:
    """Thực thể Flash cho các pair_id cần, lấy từ row_*.json."""
    want, out = set(pair_ids), {}
    for ex in iter_extractions(rows_dir, skip_errors=False):
        if ex.get("pair_id") in want:
            for side in SIDES:
                out[(ex["pair_id"], side)] = _entity_set(entities(ex, side))
    return out


def load_ext2(fname) -> tuple[dict, list]:
    d = json.loads(paths.require(D / fname, "đầu ra Gemini 2.5 Pro").read_text(encoding="utf-8"))
    rows = d["results"] if isinstance(d, dict) and "results" in d else d
    out = {}
    for r in rows:
        for side in SIDES:
            out[(r["pair_id"], side)] = _entity_set(r.get(side, []))
    return out, [r["pair_id"] for r in rows]


def cr(e1, e2) -> dict:
    NA = NB = NAB = 0
    for k in set(e1) | set(e2):
        a, b = e1.get(k, set()), e2.get(k, set())
        NA += len(a); NB += len(b); NAB += len(a & b)
    return dict(NA=NA, NB=NB, NAB=NAB,
                Nhat=(NA * NB / NAB if NAB else float("nan")),
                Nchap=(NA + 1) * (NB + 1) / (NAB + 1) - 1,
                recall_A=(NAB / NB if NB else float("nan")),
                recall_B=(NAB / NA if NA else float("nan")))


def report(r, label):
    print(f"=== Capture-recapture: {label} ===")
    print(f"  N_A (Flash) = {r['NA']}   N_B (Pro) = {r['NB']}   N_AB (both) = {r['NAB']}")
    print(f"  N_hat (Lincoln-Petersen) = {r['Nhat']:.1f}   (Chapman = {r['Nchap']:.1f})")
    print(f"  recall_A (Flash) = N_AB/N_B = {r['recall_A']:.4f}  (UPPER bound)")
    print(f"  recall_B (Pro)   = N_AB/N_A = {r['recall_B']:.4f}")


def bootstrap_recall_ci(e1, e2, pids, n_boot=5000, seed=13):
    keys, rng, vals = sorted(set(pids)), random.Random(seed), []
    for _ in range(n_boot):
        nb = nab = 0
        for k in (rng.choice(keys) for _ in keys):
            for side in SIDES:
                a, b = e1.get((k, side), set()), e2.get((k, side), set())
                nb += len(b); nab += len(a & b)
        vals.append(nab / nb)
    vals.sort()
    return vals[int(0.025 * n_boot) - 1], vals[int(0.975 * n_boot) - 1]


def run_gold():
    e2, _ = load_ext2("gemini_pro_output_gold_400_pairs.json")
    e1 = load_predictions()
    r = cr(e1, e2)
    report(r, "400 gold pairs")
    gold = majority_vote([load_worksheet(f) for f in annotator_files()])
    TP = FN = 0
    for k in gold:
        TP += len(gold[k] & e1.get(k, set()))
        FN += len(gold[k] - e1.get(k, set()))
    true_recall = TP / (TP + FN) if TP + FN else float("nan")
    print()
    print("=== Validation vs human majority-gold (same 400 pairs) ===")
    print(f"  TRUE recall_A (vs gold) = {true_recall:.4f}")
    print(f"  Estimator gap = {r['recall_A'] - true_recall:+.4f}")


def run_corpus(rows_dir):
    e2, pids = load_ext2("gemini_pro_output_corpus_sample_1200_pairs.json")
    e1 = load_ext1_from_rows(rows_dir, pids)
    report(cr(e1, e2), f"corpus sample ({len(set(pids))} pairs)")
    lo, hi = bootstrap_recall_ci(e1, e2, pids)
    print(f"  95% bootstrap CI = [{lo:.3f}, {hi:.3f}]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", choices=["gold", "corpus"], default="gold")
    ap.add_argument("--rows", default=str(paths.llm_rows_dir()), help="row_*.json của lượt Flash")
    args = ap.parse_args()
    if args.mode == "corpus":
        run_corpus(args.rows)
    else:
        run_gold()


if __name__ == "__main__":
    main()
