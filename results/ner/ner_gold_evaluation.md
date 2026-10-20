# Đánh giá NER trên gold 3 người gán

- Người gán: a, b, c; số đơn vị (cặp câu × phía) mỗi người: 800, 800, 800

## Inter-annotator agreement (F1 exact)

| Cặp | F1 |
|---|---|
| a–b | 0.9695 |
| a–c | 0.7950 |
| b–c | 0.8197 |

- Trung bình: 0.8614

## Gold đồng thuận (≥ 2/3 người gán) vs LLM

- Mention gold: 1343; mention dự đoán: 1460
- TP=1313  FP=147  FN=30
- Micro: P=0.8993  R=0.9777  F1=0.9369  [95% CI 0.919–0.953]

| Nhãn | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| PER | 0.8986 | 0.9984 | 0.9459 | 629 | 71 | 1 |
| LOC | 0.9331 | 0.9612 | 0.9469 | 223 | 16 | 9 |
| TIT | 0.8806 | 0.9478 | 0.9130 | 236 | 32 | 13 |
| EVT | 0.9634 | 0.9875 | 0.9753 | 158 | 6 | 2 |
| DYNA | 0.9853 | 0.9306 | 0.9571 | 67 | 1 | 5 |

- Macro-F1: 0.9476
- Phía zh: P=0.9461  R=0.9870  F1=0.9661  (400 câu)
- Phía vi: P=0.8533  R=0.9676  F1=0.9069  (400 câu)
