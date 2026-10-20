[English](README.md) | **Tiếng Việt**

# Triple precision và hard-link precision (Mục 4.6)

Người chấm (chuyên gia Hán–Việt) đọc câu nguồn và điền cột `verdict` (1 = đúng, 0 = sai,
để trống = chưa chấm). Các phiếu chứa câu của ngữ liệu nên cung cấp theo yêu cầu (README.vi.md, mục 2.2). Chạy `python3 -m sino_viet_kg.evaluation.triple_link_precision` để tính
precision kèm khoảng tin cậy Wilson 95%.

## Tệp

| Tệp | Nội dung |
|---|---|
| `triples_human_judged.csv` | 200 bộ ba kèm `evidence` và `sentence`. `verdict = 1` nếu câu nguồn nói đúng (head, predicate, tail) theo đúng chiều. |
| `hard_links_auto_confirmed.csv` | Liên kết không phải phiên âm mà mỗi phía chỉ có một ứng viên cùng loại trong câu, nên gióng hàng xác nhận được. |
| `hard_links_human_judged.csv` | 81 liên kết không phải phiên âm còn lại (nhiều ứng viên cùng loại), do chuyên gia chấm. `verdict = 1` nếu hai thực thể cùng một referent. |
