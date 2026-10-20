<task>
For each <pair_id, Hán sentence, Vietnamese translation> from Đại Việt Sử Ký 
Toàn Thư: extract entities + triples on each side, then propose Hán↔Việt 
entity alignment. Output strict JSON.
</task>

<entities>
5 labels (apply to both sides):
  PER  — rulers, officials, persons (Lê Lợi / 黎利)
  LOC  — capitals, regions, rivers, directions (Thăng Long / 升龍 / phương Nam)
  TIT  — feudal titles, offices (Vua, Đế, 帝, 皇后)
  EVT  — events + dates incl. 干支 cycles (trận Bạch Đằng, 戊戌)
  DYNA — dynasties (nhà Lý, 宋朝)
Split titles from names: "Vua Lý Thái Tổ" → Vua[TIT] + Lý Thái Tổ[PER], 
linked by holds_title. Same for "黎太祖皇帝" → 黎太祖[PER] + 皇帝[TIT].
</entities>

<predicates>
Closed vocabulary, snake_case. Use exactly one per triple:
  descendant_of, father_of, mother_of, spouse_of, sibling_of,
  appointed_to, bestowed_title, holds_title, ascended_throne, succeeded_by,
  ruled, moved_capital_to, conquered, quelled_rebellion, led_uprising,
  issued_edict, dispatched_to, part_of, located_at, borders_with,
  occurred_on, reign_era, alias_of,
  other_relation   ← fallback, use only when nothing above fits
</predicates>

<rules>
- Extract only what is explicitly stated. No inference.
- Keep entity text in its ORIGINAL script (Hán → Chinese chars, Việt → Vietnamese).
- IDs: Z1,Z2,… for Hán; V1,V2,… for Việt. Reset per pair. 
  subject/object MUST be IDs, never raw text. Triples reference same-side IDs only.
- evidence: short verbatim phrase from the SAME-SIDE sentence.
- Empty side → still emit entities:[], triples:[]. Never drop a pair_id.
</rules>

<alignment>
Pair Z*↔V* only if both refer to the same real-world referent. 1-to-1 only.
confidence:
  1.00       exact (黎利 ↔ Lê Lợi)
  0.90–0.99  full Sino-Vietnamese phonetic match, possibly reordered
  0.70–0.89  one side adds prefix (Vua, ngài…) or omits part
  0.50–0.69  semantic translation, not phonetic (南方 ↔ phương Nam)
  <0.50      omit
note: exact | reordered | expanded | translated | other
Entities without counterpart: omit from alignment.
</alignment>

<output_schema>
{"results":[{
  "pair_id":"...",
  "zh":{"entities":[{"id":"Z1","text":"...","label":"...","confidence":0.0}],
        "triples":[{"subject":"Z1","predicate":"...","object":"Z2",
                    "confidence":0.0,"evidence":"..."}]},
  "vi":{"entities":[...],"triples":[...]},
  "alignment":[{"zh_id":"Z1","vi_id":"V1","confidence":0.0,"note":"..."}]
}]}

Entity `confidence` ∈ [0,1]: how sure the LLM is that this span is the
labelled entity (1.0 = unambiguous, e.g. famous figure / well-known place;
≤0.5 = ambiguous span boundary or rare label).
</output_schema>

<example>
Input pair_id "demo":
  Hán: 黎利起兵于藍山。
  Việt: Lê Lợi khởi binh ở Lam Sơn.

Output:
{"results":[{
  "pair_id":"demo",
  "zh":{
    "entities":[
      {"id":"Z1","text":"黎利","label":"PER","confidence":1.0},
      {"id":"Z2","text":"藍山","label":"LOC","confidence":0.95}
    ],
    "triples":[
      {"subject":"Z1","predicate":"led_uprising","object":"Z2",
       "confidence":0.9,"evidence":"起兵于藍山"}
    ]
  },
  "vi":{
    "entities":[
      {"id":"V1","text":"Lê Lợi","label":"PER","confidence":1.0},
      {"id":"V2","text":"Lam Sơn","label":"LOC","confidence":0.95}
    ],
    "triples":[
      {"subject":"V1","predicate":"led_uprising","object":"V2",
       "confidence":0.9,"evidence":"khởi binh ở Lam Sơn"}
    ]
  },
  "alignment":[
    {"zh_id":"Z1","vi_id":"V1","confidence":1.0,"note":"exact"},
    {"zh_id":"Z2","vi_id":"V2","confidence":0.95,"note":"reordered"}
  ]
}]}
</example>

<input_text>
{INPUT}
</input_text>