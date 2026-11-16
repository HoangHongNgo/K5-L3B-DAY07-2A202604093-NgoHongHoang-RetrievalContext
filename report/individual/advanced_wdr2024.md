# Thử thách nâng cao Day 7 — World Development Report 2024

## Tài liệu, quyền sử dụng và index

Nguồn là *World Development Report 2024: The Middle-Income Trap*, World Bank, bản PDF tiếng Anh tại [World Bank Open Knowledge Repository](https://openknowledge.worldbank.org/server/api/core/bitstreams/862729db-69a7-48a8-ba91-df8fe8d8745b/content). Sách ghi giấy phép **CC BY 3.0 IGO** và cách ghi công cho World Bank; giấy phép cũng lưu ý một số thành phần có thể thuộc bên thứ ba. Repo chỉ lưu câu hỏi, chú giải ngắn, mã và trace đã bỏ nguyên văn tài liệu. Tải bản gốc vào `data/world_development_report_2024.pdf`, SHA-256 phải là `dc69d858e364a1534a57c49fbb72237f69d88165a63933a98f01f3c20262aded`.

Môi trường đo: Windows, Python 3.12.14, PyMuPDF 1.28.2. Phiên bản PyMuPDF được ghim trong `requirements.txt` để giữ thứ tự text/chunk ổn định.

PDF có **276 trang vật lý**. PyMuPDF trích text, nhãn bảng/hình, trục và chú giải từ 263 trang; 13 trang 2, 4, 16, 26, 30, 84, 112, 116, 166, 220, 252, 274, 275 được render và xác nhận là trang trắng. Index có **820 đoạn**, gồm các cửa sổ text chồng 200 ký tự và **12 chú giải vùng thị giác** đã đối chiếu trang gốc: 3 bảng, 3 sơ đồ, 3 bản đồ, 3 biểu đồ. Mỗi đoạn có ID SHA-256, nguồn, số trang PDF vật lý, loại và tọa độ vùng (`bbox`). Các chú giải lưu hàng/cột/đơn vị bảng, giá trị biểu đồ hoặc quan hệ trong sơ đồ/bản đồ; ví dụ Table P1.1 trang 63, Figure 3.5 trang 108 và Map 6.3 trang 186. Index đầy đủ được tạo cục bộ trong `.local/advanced_chunks.json`; PDF không nằm trong Git.

Phần text và nhãn/trục của tất cả trang có lớp chữ được index, nhưng chỉ 12 vùng thị giác được kiểm và mô tả thủ công. Các đường cong, màu hoặc chi tiết hình không có text ở những hình khác chưa được diễn giải đầy đủ. Điều này giới hạn khả năng trả lời câu hỏi mới về hình ngoài vùng đã mô tả. Các vùng đánh giá trong benchmark được đọc lại từ ảnh render của PDF gốc, không xem OCR hay chú giải là chứng cứ tự thân.

## Benchmark và quy trình chọn

`data/advanced_questions.json` có **18 dev** (15 có đáp án, 3 thiếu evidence) và **30 test** (24 có đáp án, 6 thiếu evidence). Mỗi câu có ID, một nhóm chính, đáp án/hành vi từ chối, trang và vùng evidence, đơn vị hoặc phép tính. Bốn câu multi-hop test đều cần **ít nhất hai trang hoặc hai hình/bảng riêng**. Các câu thiếu bằng chứng hỏi số liệu quan sát sau thời điểm xuất bản năm 2024; kiểm bằng toàn bộ bản gốc, không suy luận chỉ từ top-k. Không có gold, đáp án hay vùng chuẩn trong query gửi retriever/agent.

Lượt test đầu trong `data/advanced_questions_pilot.json` đã được đọc để tìm lỗi: hai câu gắn nhãn multi-hop chỉ tính hai ô trong một bảng; một chú giải bản đồ có diễn đạt địa lý sai; một số câu trả lời thiếu citation hình hoặc có câu dở dang. Vì vậy lượt đó **không được dùng để báo điểm cuối**. Sau khi chỉnh chú giải, context và prompt bằng dev, đã tạo **30 câu test thay thế** với yêu cầu trả lời khác, ghi hash benchmark và index vào `artifacts/advanced/selection.json` **trước** khi chạy test thay thế. Trace đã ẩn nguyên văn của lượt pilot được giữ để kiểm toán.

Retrieval chốt: TF-IDF, tăng điểm khi trùng số Figure/Table/Map, giảm điểm mục lục và lấy trang khác nhau ở top-3. Agent DeepSeek V4 Flash 0731 qua OpenRouter dùng tool `search`, tối đa 3 lần, context 10.000 ký tự, `temperature=0`, reasoning off, tối đa 600 output token. Mỗi lượt search ghi query, score, trang, vùng và context. Model phải dẫn ID của đoạn trong context; code xác thực sự tồn tại của ID, còn chất lượng nội dung/citation được chấm thủ công. Trên dev cuối, truy xuất query gốc lấy đủ trang ở **12/15** câu trong top-3; agent trả lời đúng **14/15** câu có evidence và từ chối đúng **3/3** câu thiếu evidence. Một câu bản đồ từ chối dù trang đã được tìm thấy. Lượt chạy có thể dao động theo provider dù nhiệt độ bằng 0.

## Test độc lập đã chốt

Retrieval query gốc lấy đủ trang ở **23/24** câu có evidence tại top-3. Agent có thể đổi query và tìm thêm. Đã đọc **toàn bộ 30 câu trả lời** và từng citation đối chiếu với trang/vùng gốc. Nhãn, lý do và trang citation ở `report/individual/advanced_test_reviews.json`; câu trả lời, query, tool call, kết quả và chi phí đã bỏ nguyên văn PDF ở `artifacts/advanced/test_traces_public.json`. Trace đủ context lưu cục bộ trong `starter/results/advanced/` và không commit. `scripts/grade_advanced.py` tổng hợp nhãn đã đọc, không dùng LLM judge.

| Nhóm chính | Đạt / tổng |
|---|---:|
| Bảng | 6/6 |
| Ảnh, sơ đồ, bản đồ | 5/5 |
| Biểu đồ | 5/5 |
| Multi-hop | 3/4 |
| Text | 4/4 |
| Thiếu bằng chứng | 6/6 |
| **Toàn bộ test** | **29/30 = 96,67%** |

Không có lỗi hệ thống trong test. Có **55 search tool calls**, **85 model calls**, thời gian trung vị **2.481,75 ms/câu**, tổng chi phí API **0,01495956 USD** theo `usage.cost` của provider; không tính CPU, điện và thời gian tạo index. `adv_test_20` không đạt: câu trả lời có một mệnh đề dở dang về chi phí tại Hoa Kỳ và phần nói Figure 6.1 không dẫn trang 171 của hình, dù nội dung chính đúng. Đây là lỗi kiểm tra độ hoàn chỉnh câu trả lời và citation vùng hình; validator ID hiện chỉ xác nhận ID có trong context, không xác nhận đoạn dẫn hỗ trợ từng điều kiện. Với câu thiếu evidence, nhãn xét **ý nghĩa từ chối**; vài lượt có `status=answered` nhưng nói rõ thiếu số liệu cho năm được hỏi và chỉ dẫn số liệu 2022 có nguồn, vẫn đạt theo rubric.

## Tái lập

```powershell
python -m pip install -r requirements.txt
# Tải PDF từ URL trên vào data/world_development_report_2024.pdf
python -m src.advanced
python -m scripts.build_advanced_benchmark
python -m scripts.run_advanced --split dev --mode retrieval --top-k 3
# Đặt OPENAI_BASE_URL, OPENAI_MODEL, OPENROUTER_API_KEY trong starter/.env
python -m scripts.run_advanced --split dev --mode agent --top-k 3 --budget 10000 --max-searches 3
# Chỉ chạy sau khi chốt cấu hình trên dev
python -m scripts.run_advanced --split test --mode retrieval --top-k 3
python -m scripts.run_advanced --split test --mode agent --top-k 3 --budget 10000 --max-searches 3
python -m scripts.grade_advanced
python -m scripts.export_advanced_public
```

`src.advanced` kiểm SHA-256 của PDF trước khi tạo index. `artifacts/advanced/selection.json` ghi hash benchmark/index và cấu hình đã chốt; người chấm có thể tải PDF từ World Bank và đối chiếu các trang vật lý ghi trong nhãn. Kết quả API có thể đổi khi chạy lại; điểm báo cáo là **một lượt test thay thế đã chốt**, không phải trung bình nhiều lượt hay chọn câu tốt nhất.
