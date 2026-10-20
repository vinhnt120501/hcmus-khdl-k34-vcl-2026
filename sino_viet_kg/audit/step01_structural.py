"""Bước 01 — kiểm tra cấu trúc (Bảng 3).

- Entity grounding: chuỗi thực thể xuất hiện nguyên văn trong câu nguồn.
- Label / predicate validity: nhãn thuộc 5 nhãn, vị từ thuộc 24 vị từ của schema.
- Label consistency: cùng một chuỗi luôn mang cùng một nhãn trên toàn ngữ liệu.
- Triple-ID integrity: hai đầu của bộ ba trỏ tới thực thể khai trong cùng cặp câu.
"""
from collections import defaultdict

from sino_viet_kg.audit import state as S
from sino_viet_kg.audit.reading_dictionary import normalize_vi
from sino_viet_kg.fileio import jsonl_read, jsonl_write, write_json
from sino_viet_kg.labels import ENTITY_LABELS, PREDICATES, SIDES
from sino_viet_kg.text import nfc

STEP = "01_structural"


def in_sentence(span, sent):
    """Chuỗi xuất hiện nguyên văn (sau NFC) trong câu nguồn."""
    span = nfc(span)
    return bool(span) and span in nfc(sent)


def conf_ok(c):
    return isinstance(c, (int, float)) and 0 <= c <= 1


def _run():
    src = S.step_dir("00_load") / "pairs.jsonl"
    viol_path = S.step_dir(STEP) / "violations.jsonl"
    summary_path = S.step_dir(STEP) / "summary.json"
    N = defaultdict(int)
    label_of = defaultdict(set)
    violations = []

    for p in jsonl_read(src):
        N["pairs"] += 1
        if p.get("error"):
            N["pair_error"] += 1
        sents = {"zh": p.get("chinese", ""), "vi": p.get("vietnamese", "")}
        idmap = {"zh": set(), "vi": set()}
        for side in SIDES:
            sent = sents[side]
            for ent in p[side]["entities"]:
                N["entities"] += 1
                idmap[side].add(ent.get("id"))
                t = ent.get("text", "")
                if t:
                    label_of[normalize_vi(t) if side == "vi" else t.strip()].add(ent.get("label"))
                if ent.get("label") not in ENTITY_LABELS:
                    N["ent_bad_label"] += 1
                    violations.append({"pair_id": p["pair_id"], "side": side,
                                       "kind": "bad_label", "detail": ent.get("label"), "text": t})
                if not conf_ok(ent.get("confidence")):
                    N["ent_bad_conf"] += 1
                if in_sentence(t, sent):
                    N["ent_grounded"] += 1
                else:
                    violations.append({"pair_id": p["pair_id"], "side": side,
                                       "kind": "entity_not_in_sentence", "text": t})
        for side in SIDES:
            sent = sents[side]
            ids = idmap[side]
            for tr in p[side]["triples"]:
                N["triples"] += 1
                if tr.get("predicate") not in PREDICATES:
                    N["tri_bad_pred"] += 1
                    violations.append({"pair_id": p["pair_id"], "side": side,
                                       "kind": "bad_predicate", "detail": tr.get("predicate")})
                if not conf_ok(tr.get("confidence")):
                    N["tri_bad_conf"] += 1
                if tr.get("subject") not in ids or tr.get("object") not in ids:
                    N["tri_bad_ref"] += 1
                    violations.append({"pair_id": p["pair_id"], "side": side,
                                       "kind": "triple_bad_ref",
                                       "detail": [tr.get("subject"), tr.get("object")]})
                ev = tr.get("evidence", "")
                if ev:
                    N["tri_has_ev"] += 1
                    if in_sentence(ev, sent):
                        N["tri_ev_grounded"] += 1
                    else:
                        violations.append({"pair_id": p["pair_id"], "side": side,
                                           "kind": "evidence_not_in_sentence", "text": ev})
        seen_z, seen_v = set(), set()
        for a in p["alignment"]:
            N["alignments"] += 1
            if not conf_ok(a.get("confidence")):
                N["al_bad_conf"] += 1
            if a.get("zh_id") not in idmap["zh"]:
                N["al_bad_zid"] += 1
            if a.get("vi_id") not in idmap["vi"]:
                N["al_bad_vid"] += 1
            if a.get("zh_id") in seen_z or a.get("vi_id") in seen_v:
                N["al_not_1to1"] += 1
            seen_z.add(a.get("zh_id")); seen_v.add(a.get("vi_id"))

    N["label_inconsistent"] = sum(1 for v in label_of.values() if len(v) > 1)
    N["unique_entity_texts"] = len(label_of)
    jsonl_write(viol_path, violations)

    def rate(a, b):
        return round(100 * N[a] / N[b], 2) if N[b] else None

    def valid(bad, total):
        return round(100 * (1 - N[bad] / N[total]), 2) if N[total] else None

    summary = {
        "counts": dict(N),
        "rates_pct": {
            "entity_grounding": rate("ent_grounded", "entities"),
            "evidence_grounding": rate("tri_ev_grounded", "tri_has_ev"),
            "label_valid": valid("ent_bad_label", "entities"),
            "predicate_valid": valid("tri_bad_pred", "triples"),
            "triple_id_integrity": valid("tri_bad_ref", "triples"),
            "label_consistency": valid("label_inconsistent", "unique_entity_texts"),
        },
        "n_violations": len(violations),
    }
    write_json(summary_path, summary)
    S.mark_done(STEP, outputs=[viol_path, summary_path], counts=summary["rates_pct"])
    print(f"[{STEP}] {summary['rates_pct']} | violations={len(violations)}")


def run():
    S.require_done("00_load")
    S.run_step(STEP, _run, inputs=[S.step_dir("00_load") / "pairs.jsonl"])


if __name__ == "__main__":
    run()
