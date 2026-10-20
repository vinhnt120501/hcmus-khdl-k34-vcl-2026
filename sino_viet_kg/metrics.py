"""Chỉ số dùng chung: P/R/F1 trên tập mention, khoảng tin cậy Wilson."""
import collections
import math


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def score_sets(gold: dict, preds: dict):
    """gold/preds: {unit: tập (chuỗi, nhãn)}. Chỉ chấm unit có trong gold.
    -> (Counter micro tp/fp/fn, {nhãn: Counter})."""
    ex = collections.Counter()
    per = collections.defaultdict(collections.Counter)
    for k, g in gold.items():
        p = preds.get(k, set())
        ex["tp"] += len(g & p); ex["fp"] += len(p - g); ex["fn"] += len(g - p)
        for _, l in (g & p): per[l]["tp"] += 1
        for _, l in (p - g): per[l]["fp"] += 1
        for _, l in (g - p): per[l]["fn"] += 1
    return ex, per


def pair_f1(a: dict, b: dict) -> float:
    """IAA: F1 giữa hai người gán trên các unit chung."""
    c = collections.Counter()
    for k in set(a) & set(b):
        c["tp"] += len(a[k] & b[k]); c["fp"] += len(b[k] - a[k]); c["fn"] += len(a[k] - b[k])
    return prf(c["tp"], c["fp"], c["fn"])[2]


def wilson_ci(p: float, n: int, z: float = 1.96) -> tuple[float, float]:
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h
