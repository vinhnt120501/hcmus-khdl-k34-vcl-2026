[English](README.md) | **Tiếng Việt**

# Capture–recapture: ước lượng recall ở quy mô corpus (Mục 4.5)

Hai bộ trích độc lập cùng "bắt" thực thể trên một tập câu:
Gemini 2.5 Flash (A, lượt trích của bài) và Gemini 2.5 Pro (B). Khớp theo (phía, chuỗi đã
chuẩn hoá, nhãn).

- Ước lượng Lincoln–Petersen: N̂ = N_A · N_B / N_AB
- Recall của A: recall_A ≈ N_AB / N_B

Vì hai bộ trích cùng họ Gemini nên lỗi có tương quan: N̂ là cận dưới và recall_A là cận trên.

## Tệp

Trừ prompt, các tệp chứa câu của ngữ liệu nên cung cấp theo yêu cầu (README.vi.md, mục 2.2).

| Tệp | Nội dung |
|---|---|
| `prompt_gemini_pro_extraction.md` | Prompt cho Gemini 2.5 Pro |
| `input_gold_400_pairs.jsonl` | 400 cặp câu của tập gold (`pair_id`, `chinese`, `vietnamese`) |
| `gemini_pro_output_gold_400_pairs.json` | Kết quả Gemini 2.5 Pro trên 400 cặp gold |
| `input_corpus_sample_1200_pairs.jsonl` | Mẫu ngẫu nhiên 1,200 cặp từ 20,867 cặp |
| `gemini_pro_output_corpus_sample_1200_pairs.json` | Kết quả Gemini 2.5 Pro trên mẫu 1,200 cặp |

## Chạy

```bash
python3 -m sino_viet_kg.evaluation.capture_recapture gold     # đối chiếu ước lượng với recall thật trên gold
python3 -m sino_viet_kg.evaluation.capture_recapture corpus   # mẫu 1,200 cặp, kèm 95% bootstrap CI
```

Trên 400 cặp gold, ước lượng cho recall_A = 0.9783 so với recall thật 0.9777 (chênh +0.0006).
Trên mẫu 1,200 cặp: N_A = 4,149, N_B = 3,899, N_AB = 3,830, N̂ = 4,223.7, recall_A = 0.982
[95% CI 0.978–0.986] — các số ghi trong Mục 4.5 của bài.
