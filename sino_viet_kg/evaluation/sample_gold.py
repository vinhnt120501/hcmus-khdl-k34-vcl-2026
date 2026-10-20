"""Lấy mẫu 400 cặp câu cho gold (Mục 4.5), phân tầng theo kỷ (cột Period) tỉ lệ với cỡ mỗi kỷ.

Ghi vào data/gold/:
  annotation_worksheet_blank.tsv  phiếu gán trống (mỗi cặp hai dòng: side=zh, side=vi)
  llm_predictions.json            thực thể LLM trích cho các cặp được chọn
  sample_manifest.json            seed, số cặp, hạn ngạch từng kỷ

    python3 -m sino_viet_kg.evaluation.sample_gold --n 400 --seed 13
"""
import argparse
import collections
import glob
import json
import os
import random
import sys

from sino_viet_kg import paths
from sino_viet_kg.kg import entities, iter_extractions
from sino_viet_kg.labels import ENTITY_LABELS, SIDES


def load_pairs(sent_dir):
    """pair_id -> {chinese, vietnamese, period}. Bỏ cặp rỗng."""
    pairs = {}
    for f in glob.glob(os.path.join(sent_dir, "row_*.json")):
        try:
            rec = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for p in rec.get("pairs", []):
            zh = (p.get("chinese") or "").strip()
            vi = (p.get("vietnamese") or "").strip()
            if zh and vi:
                pairs[p["pair_id"]] = {"chinese": zh, "vietnamese": vi,
                                       "period": p.get("Period", "?")}
    return pairs


def load_predictions(rows_dir):
    """pair_id -> {zh:[[text,label]...], vi:[[text,label]...]}."""
    return {ex["pair_id"]: {side: [[e["text"].strip(), e["label"]] for e in entities(ex, side)
                                   if e.get("text", "").strip()]
                            for side in SIDES}
            for ex in iter_extractions(rows_dir)}


def stratified_sample(pair_ids, pairs, n, rng):
    """Phân tầng theo Period, phân bổ tỉ lệ; bù phần dư cho đủ n."""
    by_period = collections.defaultdict(list)
    for pid in pair_ids:
        by_period[pairs[pid]["period"]].append(pid)
    total = len(pair_ids)
    chosen, quotas = [], {}
    for period, ids in by_period.items():
        q = round(n * len(ids) / total)
        quotas[period] = min(q, len(ids))
    # điều chỉnh cho khớp n
    diff = n - sum(quotas.values())
    order = sorted(by_period, key=lambda p: -len(by_period[p]))
    i = 0
    while diff != 0 and order:
        p = order[i % len(order)]
        if diff > 0 and quotas[p] < len(by_period[p]):
            quotas[p] += 1; diff -= 1
        elif diff < 0 and quotas[p] > 0:
            quotas[p] -= 1; diff += 1
        i += 1
        if i > 10000:
            break
    for period, ids in by_period.items():
        chosen += rng.sample(ids, quotas[period])
    rng.shuffle(chosen)
    return chosen, quotas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400, help="số cặp câu lấy mẫu")
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--sentences", default=str(paths.SENTENCE_ROWS_DIR))
    ap.add_argument("--rows", default=str(paths.llm_rows_dir()))
    ap.add_argument("--out", default=str(paths.GOLD_DIR))
    args = ap.parse_args()

    if not os.path.isdir(args.sentences) or not os.path.isdir(args.rows):
        sys.exit(f"Không thấy {args.sentences} hoặc {args.rows}")
    pairs = load_pairs(args.sentences)
    preds = load_predictions(args.rows)
    usable = [pid for pid in pairs if pid in preds]
    print(f"Tổng cặp dùng được (có câu + có dự đoán): {len(usable)}")

    rng = random.Random(args.seed)
    n = min(args.n, len(usable))
    chosen, quotas = stratified_sample(usable, pairs, n, rng)

    os.makedirs(args.out, exist_ok=True)
    sample_preds = {pid: preds[pid] for pid in chosen}
    pred_path = os.path.join(args.out, "llm_predictions.json")
    json.dump(sample_preds, open(pred_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # phiếu gán nhãn TSV: pair_id, side, period, sentence, gold_entities
    rows = ["\t".join(["pair_id", "side", "period", "sentence", "gold_entities"])]
    for pid in chosen:
        for side, key in (("zh", "chinese"), ("vi", "vietnamese")):
            rows.append("\t".join([pid, side, pairs[pid]["period"],
                                   pairs[pid][key].replace("\t", " "), ""]))
    wpath = os.path.join(args.out, "annotation_worksheet_blank.tsv")
    open(wpath, "w", encoding="utf-8").write("\n".join(rows) + "\n")

    manifest_path = os.path.join(args.out, "sample_manifest.json")
    json.dump({"seed": args.seed, "n_pairs": n, "mode": "blank",
               "sent_dir": os.path.relpath(args.sentences, paths.CORPUS_DIR),
               "kg_dir": os.path.relpath(args.rows, paths.CORPUS_DIR),
               "labels": ENTITY_LABELS, "period_quota": quotas,
               "n_worksheet_rows": len(rows) - 1},
              open(manifest_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"Phiếu gán nhãn : {wpath}  ({len(rows)-1} dòng = {n} cặp × 2 phía)")
    print(f"Dự đoán LLM    : {pred_path}")
    print(f"Manifest       : {manifest_path}")
    print("\nBước tiếp: đọc data/gold/ANNOTATION_GUIDE.md, gán cột gold_entities,")
    print("lưu thành data/gold/annotator_<tên>.tsv, rồi chạy sino_viet_kg.evaluation.eval_ner.")


if __name__ == "__main__":
    main()
