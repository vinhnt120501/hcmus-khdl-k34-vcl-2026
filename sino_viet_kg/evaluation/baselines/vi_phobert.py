"""Baseline có giám sát phía Việt: PhoBERT-base, BIO mức từ (Mục 4.6, Bảng 6).

Huấn luyện trên nhãn LLM (silver) của 700 dòng đầu có cặp câu của ngữ liệu (6,728 câu),
3 epoch, learning rate 3e-5, batch 8, seed 13; đánh giá một lần trên gold đồng thuận phía Việt.
Nhãn của từ gán cho subword đầu tiên (căn subword thủ công vì tokenizer của PhoBERT không có
word_ids).

    python3 -m sino_viet_kg.evaluation.baselines.vi_phobert [--cpu]
"""
from sino_viet_kg.evaluation.baselines.common import (  # noqa: I001  (import trước transformers)
    BIO, L2I, decode, load_gold, load_silver, log, word_bio, write_report)

import argparse
import random

from sino_viet_kg import paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="vinai/phobert-base")
    ap.add_argument("--gold", default=str(paths.GOLD_MAJORITY))
    ap.add_argument("--epochs", type=float, default=3)
    ap.add_argument("--max_silver_rows", type=int, default=700, help="số dòng đầu (có cặp câu) dùng làm silver")
    ap.add_argument("--out", default=str(paths.BASELINE_OUT_DIR / "vi_phobert"))
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--cpu", action="store_true", help="ép chạy CPU (tránh MPS OOM)")
    args = ap.parse_args()

    log(f"START | model={args.model} | epochs={args.epochs} | max_silver_rows={args.max_silver_rows}")
    import torch
    from transformers import (AutoTokenizer, AutoModelForTokenClassification,
                              TrainingArguments, Trainer)
    from torch.utils.data import Dataset as TorchDS
    from seqeval.metrics import classification_report, f1_score
    log(f"imports OK | torch {torch.__version__} | MPS={torch.backends.mps.is_available()}")

    gold = load_gold(args.gold, "vi", word_bio)
    log(f"gold vi sentences = {len(gold)}")
    train = load_silver("vi", word_bio, args.max_silver_rows)
    random.Random(args.seed).shuffle(train)
    log(f"silver train sentences = {len(train)}")

    log(f"loading tokenizer {args.model} ...")
    tok = AutoTokenizer.from_pretrained(args.model, use_fast=False)
    log(f"tokenizer OK (fast={tok.is_fast})")

    cls_id = tok.cls_token_id if tok.cls_token_id is not None else tok.bos_token_id
    sep_id = tok.sep_token_id if tok.sep_token_id is not None else tok.eos_token_id
    unk_id = tok.unk_token_id

    def featurize(words, tags, max_len=192):
        ids, labs = [cls_id], [-100]
        for w, t in zip(words, tags):
            sub = tok.encode(w, add_special_tokens=False) or [unk_id]
            ids.extend(sub)
            labs.extend([L2I[t]] + [-100] * (len(sub) - 1))
        ids = ids[:max_len - 1] + [sep_id]
        labs = labs[:max_len - 1] + [-100]
        return ids, labs

    class DS(TorchDS):
        def __init__(self, data): self.f = [featurize(w, t) for w, t in data]
        def __len__(self): return len(self.f)
        def __getitem__(self, i):
            ids, labs = self.f[i]
            return {"input_ids": ids, "attention_mask": [1] * len(ids), "labels": labs}

    log("featurizing ...")
    dtr, dte = DS(train), DS(gold)
    log("featurize done")

    def collate(batch):
        maxlen = max(len(b["input_ids"]) for b in batch)
        pad = tok.pad_token_id or 0

        def padlist(key, fill):
            return torch.tensor([b[key] + [fill] * (maxlen - len(b[key])) for b in batch])
        return {"input_ids": padlist("input_ids", pad),
                "attention_mask": padlist("attention_mask", 0),
                "labels": padlist("labels", -100)}

    log(f"loading model weights {args.model} ...")
    model = AutoModelForTokenClassification.from_pretrained(
        args.model, num_labels=len(BIO),
        id2label={i: t for t, i in L2I.items()}, label2id=L2I)
    log("model weights OK")

    targs = TrainingArguments(
        output_dir=args.out, num_train_epochs=args.epochs,
        per_device_train_batch_size=8, per_device_eval_batch_size=16,
        learning_rate=3e-5, eval_strategy="no", save_strategy="no",
        logging_steps=50, seed=args.seed, report_to=[], use_cpu=args.cpu)
    # Không có tập dev: huấn luyện đủ số epoch rồi đánh giá một lần trên gold.
    tr = Trainer(model=model, args=targs, train_dataset=dtr, data_collator=collate)
    log("training START")
    tr.train()
    log("training DONE")

    pr = tr.predict(dte)
    yt, yp = decode(pr.predictions, pr.label_ids)
    rep = classification_report(yt, yp, digits=4)
    micro = f1_score(yt, yp)
    write_report(args.out, {"model": args.model, "train_silver": len(train),
                            "eval_gold_vi": len(gold)}, rep, micro)
    log("===== SUPERVISED BASELINE vi (entity-level, seqeval) =====")
    print(rep, flush=True)
    log(f"Micro-F1 (PhoBERT, vi) = {micro:.4f}")


if __name__ == "__main__":
    main()
