"""Phần chung của hai baseline: dựng nhãn BIO từ nhãn LLM (silver) và từ gold, giải mã dự đoán.

Module đặt biến môi trường để transformers chỉ dùng PyTorch, nên phải import trước transformers.
"""
import os
import re
import time

for _k, _v in {
    "USE_TF": "0", "USE_TORCH": "1", "TRANSFORMERS_NO_TF": "1",
    "TOKENIZERS_PARALLELISM": "false", "HF_HUB_DISABLE_TELEMETRY": "1",
    "HF_HUB_DISABLE_PROGRESS_BARS": "1", "GRPC_ENABLE_FORK_SUPPORT": "0",
    "PYTORCH_ENABLE_MPS_FALLBACK": "1",
}.items():
    os.environ.setdefault(_k, _v)

from sino_viet_kg import annotation  # noqa: E402
from sino_viet_kg.kg import entities, iter_extractions  # noqa: E402
from sino_viet_kg.labels import ENTITY_LABELS  # noqa: E402
from sino_viet_kg.text import nfc  # noqa: E402

BIO = ["O"] + [f"{p}-{l}" for l in ENTITY_LABELS for p in ("B", "I")]
L2I = {t: i for i, t in enumerate(BIO)}
SENTENCE_KEY = {"zh": "chinese", "vi": "vietnamese"}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _occupy(s, mentions, mark):
    """Tô mọi lần xuất hiện không chồng lấn của mỗi mention (mention dài ưu tiên trước).
    `mark(i, j, label)` ghi nhãn cho đoạn s[i:j]; trả mảng ô đã chiếm."""
    occupied = [None] * len(s)
    for text, label in sorted(mentions, key=lambda m: -len(m[0])):
        t = nfc(text)
        if not t:
            continue
        start = 0
        while True:
            i = s.find(t, start)
            if i < 0:
                break
            if all(occupied[j] is None for j in range(i, i + len(t))):
                for j in range(i, i + len(t)):
                    occupied[j] = label
                mark(i, i + len(t), label)
            start = i + len(t)
    return occupied


def char_bio(sentence, mentions):
    """BIO mức KÝ TỰ (Hán cổ, encoder char-based) -> (chars, tags)."""
    s = nfc(sentence)
    tags = ["O"] * len(s)

    def mark(i, j, label):
        tags[i] = f"B-{label}"
        for k in range(i + 1, j):
            tags[k] = f"I-{label}"

    _occupy(s, mentions, mark)
    return list(s), tags


def word_bio(sentence, mentions):
    """BIO mức TỪ (tách whitespace). 1 từ được gán nếu ký tự của nó nằm trong span 1 mention."""
    s = nfc(sentence)
    occupied = _occupy(s, mentions, lambda i, j, label: None)
    words, wspans = [], []
    for m in re.finditer(r"\S+", s):
        words.append(m.group()); wspans.append((m.start(), m.end()))
    tags = ["O"] * len(words)
    for wi, (a, b) in enumerate(wspans):
        labs = [occupied[j] for j in range(a, b) if occupied[j] is not None]
        if labs:
            lab = max(set(labs), key=labs.count)
            prev_in = wi > 0 and tags[wi - 1] in (f"B-{lab}", f"I-{lab}")
            tags[wi] = (f"I-{lab}" if prev_in else f"B-{lab}")
    return words, tags


def load_silver(side, to_bio, max_rows=None):
    """Nhãn LLM -> [(tokens, tags)] cho một phía."""
    data = []
    for ex in iter_extractions(max_rows=max_rows):
        sent = ex.get(SENTENCE_KEY[side]) or ""
        ments = [(e["text"], e["label"]) for e in entities(ex, side)
                 if e.get("text", "").strip() and e.get("label") in ENTITY_LABELS]
        if sent.strip():
            data.append(to_bio(sent, ments))
    return data


def load_gold(path, side, to_bio):
    """Phiếu gold -> [(tokens, tags)] cho một phía (bỏ dòng chưa gán)."""
    return [to_bio(sent, ments) for sent, ments in annotation.load_sentences(path, side)]


def decode(predictions, label_ids):
    """logits + nhãn (-100 = bỏ qua) -> (y_true, y_pred) dạng chuỗi BIO cho seqeval."""
    import numpy as np
    preds = np.argmax(predictions, axis=2)
    yt, yp = [], []
    for pr, la in zip(preds, label_ids):
        yt.append([BIO[l] for l in la if l != -100])
        yp.append([BIO[p] for p, l in zip(pr, la) if l != -100])
    return yt, yp


def write_report(out_dir, header: dict, rep: str, micro: float):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "report.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(f"{k}={v}\n" for k, v in header.items()))
        f.write(f"\n{rep}\nMicro-F1={micro:.4f}\n")
    return path
