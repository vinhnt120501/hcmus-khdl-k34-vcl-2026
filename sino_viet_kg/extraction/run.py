"""Trích thực thể, quan hệ và liên kết song ngữ cho toàn bộ cặp câu (Mục 3.2).

Gemini 2.5 Flash, temperature 0.1, chế độ JSON, lô tối đa 20 cặp/lời gọi (configs/).
Kết quả đệm theo nội dung nên dừng giữa chừng chạy lại sẽ tiếp phần còn thiếu.

    python3 -m sino_viet_kg.extraction.run --dry-run
    python3 -m sino_viet_kg.extraction.run --limit 40
    python3 -m sino_viet_kg.extraction.run

Ra: `<VCL_CORPUS_DIR>/2_llm_output/<mô hình>/rows/row_*.json` + `manifest.json` +
`unprocessed.tsv` (các cặp lỗi).
"""
from __future__ import annotations

import argparse
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from sino_viet_kg import paths
from sino_viet_kg.extraction.cache import Cache, content_hash
from sino_viet_kg.extraction.gemini_client import GeminiClient, InvalidJSONError


class RateLimiter:
    """Trần request/phút và token/phút theo cửa sổ trượt 60 giây."""

    def __init__(self, rpm: int, tpm: int) -> None:
        self.rpm, self.tpm = rpm, tpm
        self._log: list[tuple[float, int]] = []
        self._lock = threading.Lock()

    def acquire(self, tokens: int) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                self._log = [(t, n) for t, n in self._log if now - t < 60]
                if not self._log or (len(self._log) < self.rpm
                                     and sum(n for _, n in self._log) + tokens <= self.tpm):
                    self._log.append((now, tokens))
                    return
                wait = max(0.05, 60 - (now - self._log[0][0]))
            time.sleep(wait)


def est_tokens(text: str) -> int:
    """Ước lượng token: chữ Hán ~1 token/chữ, phần còn lại ~1 token/3,5 ký tự."""
    han = sum(1 for c in text if "一" <= c <= "鿿" or "㐀" <= c <= "䶿")
    return int(han + (len(text) - han) / 3.5)


def load_pairs(limit: int | None = None) -> list[dict]:
    pairs = []
    files = sorted(paths.SENTENCE_ROWS_DIR.glob("row_*.json"))
    if not files:
        raise SystemExit(f"Chưa có cặp câu ở {paths.SENTENCE_ROWS_DIR}; "
                         "chạy python3 -m sino_viet_kg.extraction.sentence_pairs trước.")
    for f in files:
        pairs.extend(json.loads(f.read_text(encoding="utf-8")).get("pairs", []))
        if limit and len(pairs) >= limit:
            return pairs[:limit]
    return pairs


def _record(pair: dict, payload: dict | None, error: str | None = None) -> dict:
    payload = payload or {}
    empty = {"entities": [], "triples": []}
    return {
        "pair_id": pair.get("pair_id"), "source_row": pair.get("source_row"),
        "pair_index": pair.get("pair_index"), "raw": pair.get("raw", ""),
        "chinese": pair.get("chinese", ""), "vietnamese": pair.get("vietnamese", ""),
        "zh": payload.get("zh") or empty, "vi": payload.get("vi") or empty,
        "alignment": payload.get("alignment") or [], "error": error,
    }


def extract(pairs, prompt, client, cache, limiter, batch_size, workers):
    """-> (bản ghi theo đúng thứ tự `pairs`, số cặp lấy từ đệm)."""
    records: list[dict | None] = [None] * len(pairs)
    pending, hits = [], 0
    for i, p in enumerate(pairs):
        zh, vi = str(p.get("chinese") or ""), str(p.get("vietnamese") or "")
        if not zh.strip() and not vi.strip():
            records[i] = _record(p, None, "empty_text")
            continue
        h = content_hash(zh, vi)
        cached = cache.load(h)
        if cached is not None:
            records[i] = _record(p, cached)
            hits += 1
        else:
            pending.append((i, p, h))

    def run_batch(batch):
        items = [(str(p["pair_id"]), str(p.get("chinese") or ""), str(p.get("vietnamese") or ""))
                 for _, p, _ in batch]
        limiter.acquire(est_tokens(prompt) + sum(est_tokens(zh + vi) for _, zh, vi in items))
        try:
            return batch, client.call_batch(prompt, items), None
        except InvalidJSONError:
            return batch, {}, "invalid_json"

    batches = [pending[i:i + batch_size] for i in range(0, len(pending), batch_size)]
    done = hits
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for fut in as_completed([pool.submit(run_batch, b) for b in batches]):
            batch, mapped, batch_error = fut.result()
            for i, p, h in batch:
                hit = mapped.get(str(p["pair_id"]))
                if hit is None:
                    records[i] = _record(p, None, batch_error or "missing_in_response")
                else:
                    records[i] = _record(p, hit)
                    cache.save(h, {"zh": records[i]["zh"], "vi": records[i]["vi"],
                                   "alignment": records[i]["alignment"]})
            done += len(batch)
            print(f"    {done:,}/{len(pairs):,} cặp · đệm {hits:,} · gọi {client.calls:,}", flush=True)
    return records, hits


def write_output(out_dir, records, meta) -> None:
    rows_dir = out_dir / "rows"
    rows_dir.mkdir(parents=True, exist_ok=True)
    by_row: dict[int, list[dict]] = {}
    for r in records:
        by_row.setdefault(int(r.get("source_row") or 0), []).append(r)
    for src, items in sorted(by_row.items()):
        (rows_dir / f"row_{src:04d}.json").write_text(
            json.dumps({"source_row": src, "extractions": items}, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8")
    lines = ["pair_id\terror\tchinese\tvietnamese"]
    for r in records:
        if r["error"]:
            zh = r["chinese"].replace("\t", " ").replace("\n", " ")
            vi = r["vietnamese"].replace("\t", " ").replace("\n", " ")
            lines.append(f"{r['pair_id']}\t{r['error']}\t{zh}\t{vi}")
    (out_dir / "unprocessed.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / "manifest.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
                                           encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="chỉ xử lý N cặp đầu (chạy thử)")
    ap.add_argument("--dry-run", action="store_true", help="in cấu hình, không gọi API")
    args = ap.parse_args()

    cfg = json.loads(paths.MODEL_CONFIG.read_text(encoding="utf-8"))
    prompt = paths.EXTRACTION_PROMPT.read_text(encoding="utf-8")
    pairs = load_pairs(args.limit)
    cache = Cache(cfg["model_id"], prompt)
    out_dir = paths.llm_dir(cfg["model_id"])
    print(f"  mô hình : {cfg['model_id']} · temperature {cfg['temperature']} · lô {cfg['batch_size']}")
    print(f"  prompt  : {paths.EXTRACTION_PROMPT.name} · hash {cache.prompt_hash[:8]}")
    print(f"  cặp câu : {len(pairs):,} -> {out_dir}")
    if args.dry_run:
        return

    try:
        from dotenv import load_dotenv
        load_dotenv(paths.ENV_FILE)
    except ImportError:
        pass
    api_key = os.getenv(cfg["api_key_env"], "")
    if not api_key:
        raise SystemExit(f"Thiếu {cfg['api_key_env']} trong môi trường hoặc code/.env")

    client = GeminiClient(api_key, cfg["model_id"], cfg["temperature"])
    started = datetime.now(timezone.utc).isoformat()
    records, hits = extract(pairs, prompt, client, cache, RateLimiter(cfg["rpm"], cfg["tpm"]),
                            cfg["batch_size"], cfg["workers"])
    meta = {
        "model": cfg["model_id"], "temperature": cfg["temperature"],
        "batch_size": cfg["batch_size"], "prompt_hash": cache.prompt_hash,
        "num_pairs": len(pairs), "num_errors": sum(1 for r in records if r["error"]),
        "num_cache_hits": hits, "num_llm_calls": client.calls,
        "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
        "prompt_template": prompt,
    }
    write_output(out_dir, records, meta)
    print(f"  xong: {len(records):,} cặp · lỗi {meta['num_errors']:,} · đệm {hits:,} · gọi {client.calls:,}")


if __name__ == "__main__":
    main()
