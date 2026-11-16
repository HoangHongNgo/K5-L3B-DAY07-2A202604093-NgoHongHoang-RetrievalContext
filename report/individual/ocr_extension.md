# Mở rộng OCR cho sách du lịch Đài Loan 2020

## Phạm vi và cách chạy

PDF gốc có 48 trang vật lý. `pypdf` trả về chuỗi rỗng ở các trang 40–44 và 47 dù các trang này có chữ in trong ảnh. Các trang khác cũng có thể có chữ trong ảnh bên cạnh lớp text PDF, ví dụ sơ đồ metro trang 6 và thông tin khách sạn trang 45–46. Pipeline mới dùng RapidOCR trên ảnh render 2× của **mọi trang**; trên trang hỗn hợp, lọc các dòng OCR trùng lớp text và lưu phần mới thành `ocr_overlay`. OCR được cache theo SHA-256 của PDF, số trang và phiên bản engine. Manifest bao phủ cả 48 trang; index `B_OCR` gồm 215 chunk từ 71 segment: 42 text PDF, 6 OCR toàn trang và 23 OCR bổ sung. Index `B` và số liệu Day 7 cũ vẫn tách riêng.

Lệnh chạy: `python -m src.day7 ingest` để nạp pgvector và `python -m scripts.run_ocr_benchmark` để chạy phép đo TF-IDF cục bộ. Kết quả chi tiết chứa trích đoạn PDF ở `starter/results/day7/ocr/` (không commit); summary công khai ở `artifacts/day7/ocr/`.

## Benchmark riêng cho trang chỉ có ảnh

Bộ `data/day7_ocr_questions.json` có 6 câu dev, 6 câu test có đáp án và mỗi split một câu thiếu bằng chứng. Mỗi split gồm 4 câu từ trang không có lớp chữ và 2 câu từ ảnh trên trang hỗn hợp. Câu hỏi và gold được kiểm tra thủ công với trang PDF gốc. Đây là bộ chẩn đoán nhỏ; câu hỏi test được tạo trong cùng đợt phát triển nên không nên xem là một đánh giá độc lập hoặc chứng cứ cho ngưỡng 90% nâng cao.

So sánh giữ nguyên corpus 48 trang, TF-IDF, top-3 và context 3000 ký tự; chỉ thay đổi việc có đưa chunk OCR vào index hay không.

| Corpus | Dev Hit@1 | Dev Hit@3 | Dev context đủ | Test Hit@1 | Test Hit@3 | Test context đủ |
|---|---:|---:|---:|---:|---:|---:|
| Chỉ lớp chữ PDF | 0/6 | 0/6 | 0/6 | 0/6 | 0/6 | 0/6 |
| Có OCR | 4/6 | 5/6 | 5/6 | 1/6 | 4/6 | 4/6 |

Theo nhóm, OCR trên trang hỗn hợp đạt Hit@3 **2/2 dev và 2/2 test**; OCR trên trang không có lớp chữ đạt **3/4 dev và 2/4 test**. Các câu thiếu bằng chứng không nằm trong mẫu số retrieval. Lỗi dev còn lại là câu về Cosmos Hotel Taipei: top-1 lấy đúng trang 41 nhưng sai chunk, không chứa mốc một phút đi bộ. Trên test, `ocr_test_40` và `ocr_test_47` không lấy được evidence trong top-3. OCR đã đưa chữ vào corpus nhưng ranking và cách chia chunk vẫn cần cải thiện. Các tỷ lệ trên **không phải** tỷ lệ câu trả lời đúng của agent.

## Giới hạn

RapidOCR có thể đọc sai con số hoặc trộn các vùng bố cục; bộ lọc dòng trùng có thể giữ nhiễu hoặc bỏ sót chữ gần giống lớp PDF. Với giá phòng và thông tin thay đổi theo thời gian, cần kiểm trực tiếp hình gốc. Bốn chunk vượt giới hạn 256 token của embedding model và bị cắt khi tạo dense embedding; TF-IDF không bị giới hạn này. Benchmark này đo khả năng đọc **chữ trong ảnh**, chưa đo hiểu ảnh, sơ đồ hay biểu đồ không có chữ.

Agent thật chưa được chạy trên bộ mới. Tác vụ gửi đoạn trích từ PDF cục bộ sang OpenRouter bị cơ chế phê duyệt tự động từ chối vì quyền chuyển nội dung tài liệu này ra dịch vụ ngoài chưa được xác minh. Khi được phép, chạy `python -m src.day7_agent --method tfidf --split dev --questions data/day7_ocr_questions.json --budget 3000 --reasoning off --output starter/results/day7/ocr_agent_dev.json`, chốt cấu hình trên dev rồi mới chạy test và chấm từng câu/citation với bản gốc.
