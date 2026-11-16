# Day 7 — Agentic RAG

## Bài làm hiện tại · Ngô Hồng Hoàng · 2A202604093

Kết quả Day 7 đã công bố dùng 142 chunk từ 35 trang và được giữ riêng trong [báo cáo](report/individual/2A202604093_NgoHongHoang.md). Bản mở rộng hiện nay nạp 48 trang: OCR sáu trang không có lớp chữ (40–44, 47) và bổ sung chữ trong ảnh ở 23 trang hỗn hợp. Index `B_OCR` có 215 chunk. Xem [đánh giá OCR](report/individual/ocr_extension.md). Điểm cũ không áp dụng cho corpus mới.

Trên Windows, từ thư mục gốc:

```powershell
python -m pip install -r requirements.txt
# Đặt PDF theo data/day6_manifest.json và DATABASE_URL/EMBEDDING_MODEL trong starter/.env
powershell -File scripts/setup_local_db.ps1
python -m src.day7 ingest
python -m scripts.run_ocr_benchmark
python -m scripts.run_comparison
python -m scripts.export_public
```

`run_comparison` hiện đo index `B_OCR` trên 48 trang. Các bảng Day 7 trong báo cáo cá nhân và artifact `selection.json` là kết quả lịch sử trên index `B` 35 trang; không so sánh trực tiếp hai lượt chạy.

OCR dùng `rapidocr-onnxruntime` và PyMuPDF. Mỗi trang được OCR; trên trang đã có lớp chữ, các dòng OCR trùng được lọc và phần còn lại lưu thành segment `ocr_overlay`. Kết quả OCR được cache trong `.local/ocr/` theo SHA-256 của PDF, không commit vì chứa nội dung sách. `scripts.run_ocr_benchmark` chạy TF-IDF tại chỗ trên bộ câu hỏi từ cả trang chỉ có ảnh và trang hỗn hợp, so sánh corpus có và không có OCR; không cần PostgreSQL. Muốn chạy agent trên bộ này, thêm `--questions data/day7_ocr_questions.json` vào lệnh `python -m src.day7_agent`. Cần đọc và chấm từng câu trả lời với trang PDF gốc; retrieval hit không phải điểm trả lời.

Trace đầy đủ nằm trong `starter/results/day7/` (bị Git bỏ qua do chứa nguyên văn PDF). Adapter dùng DeepSeek V4 Flash 0731 qua OpenRouter (`https://openrouter.ai/api/v1`); cấu hình mẫu trong `starter/.env.example`. Thêm `OPENROUTER_API_KEY` vào `starter/.env` cục bộ. Cấu hình đã chốt chạy bằng `python -m src.day7_agent --method tfidf --split dev --budget 3000 --reasoning off --output starter/results/day7/agent-dev-tfidf-v4.json`. Chỉ chạy test sau khi chốt cấu hình trên dev. Dùng `python -m scripts.export_agent_public` để tạo trace chia sẻ không chứa nguyên văn PDF. Dùng Python 3.11 trở lên.

**Bài cá nhân · Python 3.11+ · tiếp nối Day 6**

Dùng embedding và vector store từ Day 6 để xây một agent biết tìm bằng chứng, trả lời có nguồn và nhận biết khi không đủ thông tin. Bạn tự chọn kiến trúc, số tool và cách tổ chức retrieval.

> **Tùy chọn:** [Gợi ý dùng AI để lập trình](AGENT_SETUP.md) giúp bạn làm lab; phần này không bắt buộc và không tính điểm.

## Bài cần làm

![Agent tìm tài liệu trong kho Day 6 và trả lời có nguồn](assets/retrieval-pipeline.svg)

1. Kết nối dữ liệu, embedding và vector store Day 6.
2. Xây agent dùng model thật và ít nhất một khả năng truy xuất dữ liệu. Agent có thể dùng nhiều tool và nhiều lượt gọi.
3. Thử **ít nhất 3 phương pháp retrieval khác nhau**, trong đó có dense retrieval dùng vector store Day 6. Tự chọn các phương pháp còn lại; xem [gợi ý](GUIDE.md#2-thử-các-phương-pháp-retrieval).
4. Thử nhiều cấu hình, benchmark, phân tích lỗi và chọn cấu hình tốt trên **dev**; sau đó đánh giá trên **test**.

Benchmark tối thiểu có **24 câu**: dev gồm 15 câu có đáp án và 2 câu thiếu bằng chứng; test gồm 5 câu có đáp án và 2 câu thiếu bằng chứng. Xem [benchmark](BENCHMARK.md) và [rubric](RUBRIC.md).

## Thử thách nâng cao · +15 điểm

Index một tài liệu thực tế từ **100 trang** có bảng, ảnh và biểu đồ; xây agent truy xuất và trả lời các câu hỏi về nội dung đó. Hoàn thành [thử thách nâng cao](ADVANCED.md) và đạt **ít nhất 90% benchmark test** để nhận 15 điểm bonus. Phần cơ bản tối đa 85 điểm; toàn bài tối đa 100 điểm.

## Bắt đầu

1. Đọc [hướng dẫn](GUIDE.md), [rubric](RUBRIC.md) và [quy tắc](RULES.md).
2. Tạo repo cá nhân theo [cách nộp bài](SUBMISSION.md), chuẩn bị đầu ra Day 6 và model hỗ trợ tool calling.
3. Dùng hoặc thay thế [starter](starter/README.md); bạn cần kết nối model và vector store thật.
4. Chạy `python -m unittest discover -s tests -v`. Test mock chỉ kiểm tra code, không phải benchmark agent thật.

![Các bước thử nghiệm trên dev và đánh giá trên test](assets/experiment-loop.svg)

Nộp code, cách chạy, cấu hình, benchmark, trace và [báo cáo](report/individual/MSSV_HoTen.md). Thời gian ở [checkpoints](CHECKPOINTS.md) là gợi ý, có thể điều chỉnh theo lớp và phạm vi thử nghiệm.
