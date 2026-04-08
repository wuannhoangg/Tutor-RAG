# Requirements

## 1. Product goal
Xây dựng một trợ lý tự học đa môn hoạt động như bộ nhớ thứ hai cho người dùng, cho phép lưu tài liệu học tập cá nhân và hỏi lại kiến thức sau này bằng các câu trả lời chi tiết, dễ hiểu, grounded trên tài liệu và có trích nguồn rõ ràng.

---

## 2. Functional requirements

## FR-01. Upload tài liệu học tập
Hệ thống phải cho phép người dùng tải lên các loại tài liệu:
- PDF
- DOCX
- PPTX
- TXT

## FR-02. Tổ chức tài liệu theo môn học
Hệ thống phải cho phép quản lý tài liệu theo môn học để người dùng có thể truy vấn đúng phạm vi.

## FR-03. Hỏi đáp dựa trên tài liệu đã upload
Hệ thống phải cho phép người dùng đặt câu hỏi bằng ngôn ngữ tự nhiên và trả lời dựa trên tài liệu cá nhân đã upload.

## FR-04. Giải thích khái niệm rất chi tiết
Hệ thống phải có khả năng giải thích khái niệm theo phong cách gia sư, ưu tiên dễ hiểu và chi tiết.

## FR-05. Giải thích đoạn khó hiểu trong tài liệu
Hệ thống phải có khả năng giải thích lại một đoạn nội dung mà người dùng không hiểu, dựa trên đúng tài liệu liên quan.

## FR-06. Tóm tắt nội dung để ôn tập
Hệ thống phải hỗ trợ tóm tắt tài liệu, chương hoặc chủ đề để người dùng ôn lại kiến thức.

## FR-07. Tạo câu hỏi ôn tập
Hệ thống phải có khả năng sinh câu hỏi ôn tập từ tài liệu đã upload.

## FR-08. Hỗ trợ hội thoại nhiều lượt
Hệ thống phải nhớ ngữ cảnh hội thoại gần để trả lời các câu follow-up nhất quán.

## FR-09. Luôn trích nguồn
Hệ thống phải luôn chỉ ra:
- tài liệu đã dùng,
- trang liên quan,
- đoạn hoặc chunk liên quan.

## FR-10. Xử lý khi bằng chứng không đủ
Khi tài liệu không đủ để kết luận chắc chắn, hệ thống phải trả lời rõ “không đủ bằng chứng”.

## FR-11. Hỗ trợ suy luận có kiểm soát
Hệ thống được phép suy luận trên cơ sở tài liệu, nhưng phải:
- bám sát evidence,
- nói rõ phần nào là suy luận,
- giải thích vì sao suy luận như vậy.

## FR-12. Giới hạn phạm vi truy hồi
Hệ thống phải chỉ truy hồi trong tài liệu mà người dùng đã upload cho đúng tài khoản và đúng môn học đang xét.

---

## 3. Non-functional requirements

## NFR-01. Faithfulness cao
Câu trả lời phải bám sát tài liệu, không được bịa thêm nội dung không có căn cứ.

## NFR-02. Explainability cao
Hệ thống phải dễ giải thích: người dùng phải nhìn được nguồn nào đã được dùng để tạo ra câu trả lời.

## NFR-03. Chi tiết và dễ hiểu
Mặc định câu trả lời phải đủ chi tiết để đóng vai trò gia sư hỗ trợ người học nhớ lại và hiểu sâu hơn.

## NFR-04. Context continuity
Hệ thống phải giữ được ngữ cảnh hội thoại gần để hỗ trợ hỏi tiếp.

## NFR-05. Subject-based organization
Hệ thống phải hoạt động tốt với mô hình tổ chức tài liệu theo môn học.

## NFR-06. Traceability
Mỗi claim quan trọng trong câu trả lời nên truy ngược được về tài liệu, trang và đoạn.

## NFR-07. An toàn về phạm vi trả lời
Khi evidence không đủ hoặc mâu thuẫn, hệ thống phải thể hiện sự không chắc chắn thay vì kết luận chắc chắn.

---

## 4. Grounding rules

### GR-01
Grounded first, reasoning second.

### GR-02
Hệ thống không được trả lời như chatbot tự do ngoài tài liệu.

### GR-03
Mọi claim quan trọng phải có support.

### GR-04
Nếu có phần suy luận không xuất hiện trực tiếp trong tài liệu, phải đánh dấu rõ đó là suy luận.

### GR-05
Nếu không đủ bằng chứng, phải nói rõ “không đủ bằng chứng”.

### GR-06
Citation phải chỉ đúng tài liệu, trang và đoạn/chunk hỗ trợ.

---

## 5. In-scope cho V1
Phiên bản đầu phải hỗ trợ tốt các nhu cầu sau:
- hỏi lại kiến thức đã học,
- giải thích chi tiết khái niệm,
- giải thích đoạn khó hiểu,
- tóm tắt nội dung để ôn tập,
- tạo câu hỏi ôn tập,
- hỗ trợ ôn thi từ tài liệu cá nhân.

---

## 6. Out-of-scope cho V1
Phiên bản đầu chưa hỗ trợ:
- chấm bài tự luận dài,
- nhận diện ảnh hoặc chữ viết tay phức tạp,
- voice/audio interaction,
- phục vụ quy mô lớn nhiều người dùng đồng thời,
- app mobile.

---

## 7. Quality rules
- Không bịa.
- Đúng tài liệu.
- Giải thích dễ hiểu.
- Giải thích chi tiết.
- Nhớ ngữ cảnh câu hỏi trước.
- Luôn có trích nguồn.
- Nói rõ khi không đủ bằng chứng.

---

## 8. Success criteria cho bước khởi tạo sản phẩm
Bước khởi tạo bài toán được xem là hoàn thành khi:
1. Đã xác định rõ người dùng mục tiêu.
2. Đã xác định rõ nhóm use case cốt lõi.
3. Đã xác định rõ những gì chưa làm ở V1.
4. Đã xác định rõ các quy tắc grounding và citation.
5. Đã xác định rõ các tiêu chí chất lượng chính.

---

## 9. Tóm tắt yêu cầu hệ thống
Hệ thống là một trợ lý học tập grounded trên tài liệu cá nhân, phục vụ người tự học nhiều môn, ưu tiên khả năng truy hồi đúng, giải thích sâu, nhớ ngữ cảnh, và luôn chỉ ra nguồn bằng chứng.