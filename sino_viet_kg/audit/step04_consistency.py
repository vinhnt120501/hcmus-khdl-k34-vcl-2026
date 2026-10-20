"""Bước 04 — nhất quán song ngữ (Bảng 3).

- Alignment symmetry: tỉ lệ thực thể Hán / Việt có liên kết.
- Triple parallelism: bộ ba có hai đầu đều được liên kết thì có bộ ba cùng vị từ ở phía kia.
"""
from sino_viet_kg.audit import state as S
from sino_viet_kg.fileio import jsonl_read, jsonl_write, write_json

STEP = "04_consistency"


def _spo(t):
    return t.get("subject"), t.get("predicate"), t.get("object")


def _run():
    src = S.step_dir("00_load") / "pairs.jsonl"
    zh_ent = zh_al = vi_ent = vi_al = 0
    tri_zh = tri_zh_par = tri_vi = tri_vi_par = 0
    no_parallel = []
    for p in jsonl_read(src):
        zents = p["zh"]["entities"]; vents = p["vi"]["entities"]
        L = set((a.get("zh_id"), a.get("vi_id")) for a in p["alignment"])
        zal = set(z for z, _ in L); val = set(v for _, v in L)
        zh_ent += len(zents); vi_ent += len(vents)
        zh_al += sum(1 for e in zents if e.get("id") in zal)
        vi_al += sum(1 for e in vents if e.get("id") in val)
        z2v = dict(sorted(L, key=str)); v2z = {v: z for z, v in sorted(L, key=str)}  # cố định thứ tự duyệt set
        ztr = p["zh"]["triples"]; vtr = p["vi"]["triples"]
        vset = set(_spo(t) for t in vtr)
        zset = set(_spo(t) for t in ztr)
        for t in ztr:
            s, pr, o = _spo(t)
            if s in z2v and o in z2v:
                tri_zh += 1
                if (z2v[s], pr, z2v[o]) in vset:
                    tri_zh_par += 1
                else:
                    no_parallel.append({"pair_id": p["pair_id"], "side": "zh",
                                        "triple": [s, pr, o]})
        for t in vtr:
            s, pr, o = _spo(t)
            if s in v2z and o in v2z:
                tri_vi += 1
                if (v2z[s], pr, v2z[o]) in zset:
                    tri_vi_par += 1

    jsonl_write(S.step_dir(STEP) / "no_parallel.jsonl", no_parallel)

    def pct(a, b):
        return round(100 * a / b, 2) if b else None

    counts = {
        "zh_align_symmetry_pct": pct(zh_al, zh_ent),
        "vi_align_symmetry_pct": pct(vi_al, vi_ent),
        "triple_parallel_zh_pct": pct(tri_zh_par, tri_zh),
        "triple_parallel_vi_pct": pct(tri_vi_par, tri_vi),
        "tri_zh_checked": tri_zh, "tri_vi_checked": tri_vi,
    }
    summary_path = S.step_dir(STEP) / "summary.json"
    write_json(summary_path, counts)
    S.mark_done(STEP, outputs=[summary_path], counts=counts)
    print(f"[{STEP}] {counts}")


def run():
    S.require_done("00_load")
    S.run_step(STEP, _run, inputs=[S.step_dir("00_load") / "pairs.jsonl"])


if __name__ == "__main__":
    run()
