"""Canonicalization và tập liên kết một–một (Mục 3.3–3.4, Bảng 2).

- Gộp mention trong từng phía khi cùng nhãn và cùng chuỗi đã chuẩn hoá (NFC, casefold, gộp
  khoảng trắng); bộ ba có đầu mút ngoài tập thực thể bị loại (dangling).
- Liên kết LLM đề xuất được ánh xạ sang thực thể canonical rồi lọc tham lam thành tập một–một:
  ưu tiên nhiều cặp câu ủng hộ hơn, rồi độ tin trung bình cao hơn, rồi xuất hiện sớm hơn.
- Ghi entities_{zh,vi}.tsv, triples_{zh,vi}.tsv, relations.tsv, links.tsv (tập một–một) và
  link_candidates.tsv (15,457 cặp ứng viên trước khi lọc, kèm số cặp câu ủng hộ và độ tin trung
  bình); id phía Việt nối tiếp sau id phía Hán.

    python3 -m sino_viet_kg.canonicalization
"""
import argparse
import os
from collections import defaultdict

from sino_viet_kg import paths
from sino_viet_kg.kg import iter_extractions
from sino_viet_kg.labels import SIDES
from sino_viet_kg.text import norm_mention


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default=str(paths.llm_rows_dir()), help="thư mục row_*.json")
    ap.add_argument("--out", default=str(paths.CANON_OUT_DIR), help="thư mục ghi TSV")
    args = ap.parse_args()

    ents = {"zh": {}, "vi": {}}                 # (nhãn, chuỗi chuẩn hoá) -> id canonical, mỗi phía
    raw_mentions = raw_triples = raw_links = 0
    triples = {"zh": set(), "vi": set()}
    dangling = {"zh": 0, "vi": 0}
    link_support, link_conf, first_seen = defaultdict(set), defaultdict(list), {}
    for ex in iter_extractions(args.rows):
        local = {}
        for side in SIDES:
            blk = ex.get(side) or {}
            for e in blk.get("entities", []):
                t = e.get("text", "")
                if not t.strip():
                    continue
                raw_mentions += 1
                key = (e.get("label", "").strip().upper(), norm_mention(t, casefold=True))
                cid = ents[side].setdefault(key, len(ents[side]))
                local[(side, e.get("id"))] = cid
            for tr in blk.get("triples", []):
                raw_triples += 1
                h, tl = local.get((side, tr.get("subject"))), local.get((side, tr.get("object")))
                if h is None or tl is None:
                    dangling[side] += 1
                    continue
                triples[side].add((h, tr.get("predicate", ""), tl))
        for a in ex.get("alignment", []) or []:
            raw_links += 1
            z, v = local.get(("zh", a.get("zh_id"))), local.get(("vi", a.get("vi_id")))
            if z is None or v is None:
                continue
            first_seen.setdefault((z, v), len(first_seen))
            link_support[(z, v)].add(ex.get("pair_id"))
            link_conf[(z, v)].append(float(a.get("confidence") or 0))

    mean = lambda k: sum(link_conf[k]) / len(link_conf[k])
    cand = sorted(link_support, key=lambda k: (-len(link_support[k]), -mean(k), first_seen[k]))
    used_z, used_v, links = set(), set(), []
    for z, v in cand:
        if z in used_z or v in used_v:
            continue
        used_z.add(z); used_v.add(v); links.append((z, v))
    rels = sorted({p for s in triples for _, p, _ in triples[s]})
    print(f"raw mentions={raw_mentions} raw triples={raw_triples} raw links={raw_links}")
    print(f"entities zh={len(ents['zh'])} vi={len(ents['vi'])}")
    print(f"triples zh={len(triples['zh'])} vi={len(triples['vi'])} relation types={len(rels)}")
    print(f"dangling zh={dangling['zh']} vi={dangling['vi']}")
    print(f"link candidates={len(cand)} one-to-one links={len(links)}")

    out = args.out
    os.makedirs(out, exist_ok=True)
    off = len(ents["zh"])                       # id phía Việt nối tiếp sau id phía Hán
    for side, base in (("zh", 0), ("vi", off)):
        with open(os.path.join(out, f"entities_{side}.tsv"), "w", encoding="utf-8") as f:
            for (lab, t), i in sorted(ents[side].items(), key=lambda x: x[1]):
                f.write(f"{base + i}\t{t}\t{lab}\n")
        with open(os.path.join(out, f"triples_{side}.tsv"), "w", encoding="utf-8") as f:
            for h, p, t in sorted(triples[side]):
                f.write(f"{base + h}\t{rels.index(p)}\t{base + t}\n")
    with open(os.path.join(out, "relations.tsv"), "w", encoding="utf-8") as f:
        for i, p in enumerate(rels):
            f.write(f"{i}\t{p}\n")
    with open(os.path.join(out, "links.tsv"), "w", encoding="utf-8") as f:
        for z, v in links:
            f.write(f"{z}\t{off + v}\n")
    with open(os.path.join(out, "link_candidates.tsv"), "w", encoding="utf-8") as f:
        for z, v in cand:
            f.write(f"{z}\t{off + v}\t{len(link_support[(z, v)])}\t{mean((z, v)):.4f}\n")


if __name__ == "__main__":
    main()
