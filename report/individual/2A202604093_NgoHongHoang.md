# Day 7 · Ngô Hồng Hoàng · 2A202604093

## Dữ liệu và cách tái lập

- Nguồn: *2020 Taiwan Tourism Guide Book*, 35 trang nội dung; PDF giữ cục bộ vì quyền tái phân phối chưa được xác minh. SHA-256 và số ký tự từng trang được kiểm với `data/day6_manifest.json`.
- Kế thừa [repo Day 6](https://github.com/HoangHongNgo/K5-L3B-DAY06-NgoHongHoang-2A202604093-DataIngestion.git), commit `372dbc94c8dd9fb4c8166b5fc2f88b373074e76e`. Giữ nguyên thuật toán chunk ID SHA-256, document ID, source, trang và metadata. Dùng 142 chunk câu (chiến lược B: tối đa 650 ký tự) từ 35 trang.
- Embedding: `sentence-transformers/all-MiniLM-L6-v2`, 384 chiều, chuẩn hóa vector, document và query dùng cùng model. Máy chạy: `sentence-transformers 5.7.0`, `transformers 5.22.2`, `torch 2.15.0`, `psycopg 3.3.9`. Vector store: PostgreSQL + pgvector, bảng `starter_chunks`, cosine exact search, `strategy=B`, lọc `model_name`.
- Bộ Day 6 đã từng xem cả test, nên 27 câu đó trở thành **dev**. Day 7 thêm 2 dev thiếu bằng chứng, 5 test có evidence mới và 2 test thiếu bằng chứng. Tổng: 29 dev, 7 test. Không đưa gold hoặc đáp án vào retriever hay agent. Các câu thiếu bằng chứng hỏi sự kiện 2024–2026; corpus trích xuất không chứa các năm này.
- Chạy từ project root: `python -m pip install -r requirements.txt`; `powershell -File scripts/setup_local_db.ps1`; `python -m src.day7 ingest`; `python -m scripts.run_comparison`. Đặt PDF đúng tên trong `data/` và cấu hình `DATABASE_URL`, `EMBEDDING_MODEL` ở `starter/.env` trước khi chạy. `starter/results/day7/` chứa trace cục bộ có nguyên văn đoạn PDF, không commit.

Các bảng Day 7 bên dưới ghi lại lượt chạy **index B 35 trang/142 chunk**. Code hiện tại dùng index `B_OCR` 48 trang/215 chunk, nên chạy lại `ingest` và `run_comparison` sẽ tạo số liệu **mới**, không tái tạo đúng các con số lịch sử. Summary và trace đã ẩn trích đoạn của lượt chạy B nằm trong `artifacts/day7/`; PDF cần lấy từ nguồn ghi trong manifest và kiểm SHA-256 trước khi dùng. Phép đo riêng cho code hiện tại nằm trong [báo cáo OCR](ocr_extension.md).

## Retrieval và thí nghiệm

Mọi dòng dùng cùng 142 chunk, cùng 27 câu dev có đáp án, không filter, top-3 cố định cho Hit@1 và Evidence Hit@3. Context budget tính bằng ký tự gồm ID/nguồn/trang. Hit yêu cầu quote gold nằm trọn trong chunk đúng tài liệu và trang. Thời gian là median trên 29 query dev hoặc 7 query test, tính cả query embedding/DB khi dùng dense, không tính khởi tạo index/model. Chi phí API bằng 0 USD; không quy đổi CPU và điện thành tiền.

| Cấu hình | Dev Hit@1 | Dev Hit@3 | Dev context đủ | Median ms | Giả thuyết |
|---|---:|---:|---:|---:|---|
| Dense Day 6, k=3, 1800 ký tự | 23/27 | 25/27 | 25/27 | 118.14 | Baseline |
| TF-IDF, k=3, 1800 ký tự | 24/27 | 27/27 | 27/27 | 0.72 | Từ khóa cụ thể giúp truy xuất chi tiết trong sách tiếng Anh |
| Hybrid RRF, k=3, 1800 ký tự | 24/27 | 25/27 | 25/27 | 131.17 | Kết hợp dense và lexical có thể bù lỗi |

RRF dùng `1/(60+rank)` cho mỗi danh sách, không cộng score cosine và TF-IDF trực tiếp. TF-IDF là cấu hình cải thiện thứ nhất so với dense baseline; hybrid là cấu hình thử cải thiện thứ hai nhưng không tăng Evidence Hit@3. Kết quả và trace từng query ở `starter/results/day7/dev/`.

Hai lỗi dense dev được đọc lại: `q03` trả đúng trang 8 nhưng lấy chunk khác với câu nêu thành phố; TF-IDF đưa chunk có evidence vào top-3. `q16` dense xếp các trang 29/22/18, không có evidence của Eryanping; TF-IDF đưa trang 26 lên top-1. Đây là lỗi ranking/chunk selection, không phải thiếu trang trong index.

Tiêu chí chốt **trước test** trong `selection.json`: context evidence cao nhất, sau đó Hit@3, Hit@1, rồi median latency thấp hơn. Chọn TF-IDF k=3, budget 1800. Test sau chốt:

| Cấu hình | Test Hit@1 | Test Hit@3 | Test context đủ | Median ms |
|---|---:|---:|---:|---:|
| Dense baseline | 3/5 | 4/5 | 3/5 | 113.08 |
| TF-IDF đã chọn | 4/5 | 4/5 | 4/5 | 0.51 |

Đã đọc context của cả 5 câu có đáp án cho cả hai cấu hình và kiểm tra 2 câu thiếu bằng chứng. Nhãn và lý do trong `report/individual/test_context_review.json`: dense có 3 mức 2, 2 mức 0; TF-IDF có 4 mức 2, 1 mức 0. `test_2` là lỗi chung: chunk về Formosa Summer Festival kết thúc trước dòng thời gian “June to September”; dùng nhầm “June to December” của Taiwan Cycling Festival sẽ tạo câu trả lời sai. `test_3` của dense thiếu tên Amis dù có đoạn mochi. Các trường hợp đủ evidence có nguồn/trang trong context.

## Agent và đánh giá câu trả lời

Agent dùng [DeepSeek V4 Flash 0731 trên OpenRouter](https://openrouter.ai/deepseek/deepseek-v4-flash-0731), endpoint `https://openrouter.ai/api/v1`, với một tool `search` nối trực tiếp retriever thật. Model quyết định query và số lượt tìm, tối đa 3 lượt; lượt cuối buộc trả lời hoặc từ chối. Context dedup theo chunk ID, gồm nguyên văn, nguồn, trang; budget tính bằng ký tự. Output tối đa 300 token. Citation dạng `[ID | page]` do model tạo được chuẩn hóa thành `[ID]`, rồi ID phải có trong context. Nội dung PDF được coi là dữ liệu, không phải chỉ dẫn. Lỗi provider được ghi riêng; lỗi kết nối ngắn hạn được thử lại một lần. Trace đầy đủ lưu cục bộ trong `starter/results/day7/`, bản bỏ nguyên văn PDF ở `artifacts/day7/agent_traces_public/`. API key nằm trong `starter/.env`, không được commit.

Ban đầu model `deepseek/deepseek-chat-v3.1` trả `402 (openrouter_credits)` cho một request. Đổi sang bản Flash 0731 được ghim phiên bản, rẻ hơn; giới hạn 300 output token giúp request đi qua. Chi phí trong bảng dưới là `usage.cost` do OpenRouter trả về, không phải ước tính. Dev đã thử thay citation parser, tăng context từ 1800 lên 3000 ký tự, buộc model kết luận ở lượt cuối và tắt suy luận mở rộng. Tất cả cấu hình dùng cùng model và bộ câu hỏi; các thay đổi khác được ghi tách riêng.

| Agent config trên dev | Có đáp án được trả lời | Thiếu evidence từ chối | Lỗi provider | Median ms/câu | Chi phí USD |
|---|---:|---:|---:|---:|---:|
| Dense baseline, 1800 ký tự, suy luận mặc định | 24/27 | 2/2 | 0 | 2,908.84 | 0.00756044 |
| TF-IDF, 3000 ký tự, suy luận mặc định | 26/27 | 2/2 | 0 | 11,104.74 | 0.00790663 |
| **TF-IDF, 3000 ký tự, suy luận tắt** | **27/27** | **2/2** | **0** | **2,263.76** | **0.00660786** |

Đã đọc 27 câu trả lời dev được chọn so với đáp án và trang nguồn; kiểm quote gold trong chunk được dẫn, rồi đọc riêng 3 citation bổ sung không chứa nguyên quote gold. Nhãn trong `report/individual/agent_dev_reviews_tfidf.json`: grounded answer 27 câu mức 2/2, citation hỗ trợ 30/30, tool use 29/29, abstention 2/2. Hai lượt đầu dùng suy luận mặc định của provider (trace có reasoning tokens), lượt cuối yêu cầu tắt suy luận. Một lượt dev trước gặp lỗi TLS ở `q07`; lượt chạy lại thành công. Hai lỗi dev chính: `q03` ban đầu thiếu chunk ghi Taichung trong context 1800 ký tự, sau tăng budget thì trả lời đúng; `q10`/`q24`/`q25` ban đầu bị từ chối vì model dẫn `[ID | page]`, sau chuẩn hóa citation thì trả lời đúng. `q26` từng bị cắt câu do token suy luận; tắt suy luận giúp trả lời đầy đủ. Kết quả thử riêng của `q26` không thay thế số liệu lượt chạy toàn bộ. Cấu hình được chọn đã ghi vào `artifacts/day7/agent_selection.json` **trước khi chạy agent trên test**.

### Test sau khi chốt

Đã đọc toàn bộ 5 câu có đáp án và 2 câu thiếu bằng chứng của mỗi cấu hình, đối chiếu từng citation với nội dung chunk. Nhãn và lý do từng câu trong `report/individual/agent_test_reviews_dense.json` và `report/individual/agent_test_reviews_tfidf.json`; script `starter/agent_metrics.py` tổng hợp thành `artifacts/day7/agent_test_summary_*.json`.

| Cấu hình / test | Tool use | Grounded answer (mức 0/1/2) | Citation hỗ trợ | Câu có citation | Từ chối đúng | Lỗi | Chi phí USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dense baseline | 7/7 | 1 / 0 / 4; trung bình 1.6/2 | 5/5 | 5/5 | 2/2 | 0 | 0.00232036 |
| TF-IDF đã chọn | 7/7 | 1 / 0 / 4; trung bình 1.6/2 | 4/5 | 5/5 | 2/2 | 0 | 0.00224756 |

`test_1` là ví dụ trả lời có bằng chứng: trang 8 nêu dịch tả là nguồn gốc của Yanshui Beehive Rockets Festival. `test_abs_1`/`test_abs_2` là ví dụ từ chối đúng vì sách 2020 không có giá vé 2026 hoặc người thắng marathon 2025. `test_2` là lỗi quan trọng: context chứa mốc “June to December” của Taiwan Cycling Festival nhưng thiếu mốc “June to September” của Formosa Summer Festival. Agent TF-IDF gán nhầm mốc đầu cho Formosa và dẫn một chunk không hỗ trợ; grade 0, citation false. Dense baseline thận trọng nói chưa đủ evidence ở câu này và không đưa ra tháng đúng, nên cũng grade 0 dù citation hỗ trợ phần mô tả nó nêu. Mã tổng hợp chỉ đếm `false_abstention` khi status là `abstain`; câu dense này có status `answered` nhưng về nghĩa là không trả lời, nên đọc nhãn grade 0 cùng lý do thay vì chỉ xem tỷ lệ từ chối nhầm. Như vậy retrieval/context tốt hơn trên dev không làm tăng grounded-answer test trong lần chạy này.

Trace và nhãn phản ánh một lượt chạy trên model có tính ngẫu nhiên và provider routing; kết quả khác có thể đổi khi chạy lại. Agent đã dùng `temperature=0` nhưng vẫn có biến động giữa các lượt thử. Cần kiểm tra lại citation khi đổi model, prompt hoặc context budget.

Thử thách nâng cao 100 trang chưa thực hiện; corpus ban đầu có 35 trang nội dung và bản OCR mở rộng bao phủ 48 trang vật lý. Bản mở rộng mới đo OCR và retrieval, chưa chạy hoặc chấm agent trên bộ câu hỏi OCR.
