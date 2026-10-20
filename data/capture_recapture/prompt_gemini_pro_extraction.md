# Prompt trích thực thể bằng Gemini 2.5 Pro (capture–recapture)

- Mô hình: **Gemini 2.5 Pro**, temperature 0.3, `response_mime_type = application/json`.
  Bộ trích gốc là Gemini 2.5 Flash; dùng tier khác để hai lần "bắt" độc lập hơn.
- Chỉ trích **thực thể** (không triple/alignment) vì recall được đo ở mức thực thể.
- Prompt cố ý diễn đạt khác prompt gốc để giảm tương quan do prompt.

---

You are an expert in Classical Chinese (Hán văn) and premodern Vietnamese historiography.
You will be given aligned sentence pairs from a historical chronicle: a Classical Chinese
line and its Vietnamese rendering. For EACH side of EACH pair, find every named entity and
assign it exactly one of these five categories:

- **PER** — a specific person: ruler, official, general, named individual.
- **LOC** — a specific place: capital, region, province, mountain, river, or a named
  direction used as a place (e.g. phương Nam / 南方).
- **TIT** — a title, rank, or office held by a person (e.g. 帝, 皇后, Vua, Thái úy).
- **EVT** — a named event or a calendar date, including sexagenary (干支) day/year markers
  (e.g. 戊戌, trận Bạch Đằng).
- **DYNA** — a dynasty or ruling house (e.g. 宋朝, nhà Lý).

Guidance:
- A title attached to a name is its OWN entity: "黎太祖皇帝" → 黎太祖 (PER) and 皇帝 (TIT)
  as two separate spans. Likewise "Vua Lý Thái Tổ" → Vua (TIT) + Lý Thái Tổ (PER).
- Keep each span in its ORIGINAL script and exact surface form as it appears in the
  sentence. Do not translate or normalize.
- Tag only what is explicitly named in that sentence. Do not infer entities not present.
- If a side has no entity, return an empty list for that side. Never drop a pair_id.

Return STRICT JSON, no prose, in exactly this shape:

```json
{"results":[
  {"pair_id":"<id>",
   "zh":[{"text":"...","label":"PER|LOC|TIT|EVT|DYNA"}],
   "vi":[{"text":"...","label":"PER|LOC|TIT|EVT|DYNA"}]}
]}
```

Input pairs (JSON lines, one object per pair):

{INPUT}
