"""Baseline có giám sát phía Hán: SikuRoBERTa, BIO mức ký tự (Mục 4.6, Bảng 6).

Huấn luyện trên nhãn LLM (silver) của 700 dòng đầu có cặp câu của ngữ liệu (6,729 câu),
3 epoch, learning rate 3e-5, batch 16, seed 13; đánh giá một lần trên gold đồng thuận phía Hán.

    python3 -m sino_viet_kg.evaluation.baselines.zh_sikubert
"""
from sino_viet_kg.evaluation.baselines.common import (  # noqa: I001  (import trước transformers)
    BIO, L2I, char_bio, decode, load_gold, load_silver, log, write_report)

import argparse
import random

from sino_viet_kg import paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="SIKU-BERT/sikuroberta")
    ap.add_argument("--gold", default=str(paths.GOLD_MAJORITY))
    ap.add_argument("--epochs", type=float, default=3)
    ap.add_argument("--max_silver_rows", type=int, default=700, help="số dòng đầu (có cặp câu) dùng làm silver")
    ap.add_argument("--out", default=str(paths.BASELINE_OUT_DIR / "zh_sikubert"))
    ap.add_argument("--seed", type=int, default=13)
    args = ap.parse_args()

    log(f"START | model={args.model} | epochs={args.epochs} | max_silver_rows={args.max_silver_rows}")

    log("importing torch/transformers ...")
    import torch
    from datasets import Dataset
    from transformers import (AutoTokenizer, AutoModelForTokenClassification,
                              DataCollatorForTokenClassification, TrainingArguments, Trainer)
    from seqeval.metrics import classification_report, f1_score
    log(f"imports OK | torch {torch.__version__} | MPS={torch.backends.mps.is_available()}")

    log("loading gold (zh) ...")
    gold = load_gold(args.gold, "zh", char_bio)
    log(f"gold zh sentences = {len(gold)}")
    if not gold:
        raise SystemExit("gold zh rỗng")

    log("loading silver (LLM labels) ...")
    train, test = load_silver("zh", char_bio, args.max_silver_rows), gold
    random.Random(args.seed).shuffle(train)
    log(f"silver train sentences = {len(train)} | eval = gold {len(test)}")

    log(f"loading tokenizer {args.model} ...")
    tok = AutoTokenizer.from_pretrained(args.model)
    log("tokenizer OK")

    def encode(batch):
        enc = tok(batch["chars"], is_split_into_words=True, truncation=True,
                  max_length=256, padding=False)
        labels = []
        for i, tags in enumerate(batch["tags"]):
            wids = enc.word_ids(i); prev = None; lab = []
            for w in wids:
                if w is None or w == prev:
                    lab.append(-100)
                else:
                    lab.append(L2I[tags[w]])
                prev = w
            labels.append(lab)
        enc["labels"] = labels
        return enc

    mk = lambda d: Dataset.from_dict({"chars": [c for c, _ in d], "tags": [t for _, t in d]})
    log("tokenizing datasets ...")
    dtr = mk(train).map(encode, batched=True, remove_columns=["chars", "tags"])
    dte = mk(test).map(encode, batched=True, remove_columns=["chars", "tags"])
    log("tokenization done")

    log(f"loading model weights {args.model} ...")
    model = AutoModelForTokenClassification.from_pretrained(
        args.model, num_labels=len(BIO),
        id2label={i: t for t, i in L2I.items()}, label2id=L2I)
    log("model weights OK")

    targs = TrainingArguments(
        output_dir=args.out, num_train_epochs=args.epochs,
        per_device_train_batch_size=16, per_device_eval_batch_size=32,
        learning_rate=3e-5, eval_strategy="no", save_strategy="no",
        logging_steps=25, seed=args.seed, report_to=[])
    # Không có tập dev: huấn luyện đủ số epoch rồi đánh giá một lần trên gold.
    tr = Trainer(model=model, args=targs, train_dataset=dtr,
                 data_collator=DataCollatorForTokenClassification(tok))
    log("training START")
    tr.train()
    log("training DONE")

    pr = tr.predict(dte)
    yt, yp = decode(pr.predictions, pr.label_ids)
    rep = classification_report(yt, yp, digits=4)
    micro = f1_score(yt, yp)
    write_report(args.out, {"model": args.model, "train_silver_sentences": len(train),
                            "eval_gold_zh_sentences": len(test)}, rep, micro)
    log("===== SUPERVISED BASELINE (entity-level, seqeval) =====")
    print(rep, flush=True)
    log(f"Micro-F1 (SikuBERT, zh) = {micro:.4f}")


if __name__ == "__main__":
    main()
