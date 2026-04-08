# Use Cases

## 1. User persona chính

### Persona
Người tự học nhiều môn

### Mô tả
Người dùng thường học bằng slide bài giảng, giáo trình, đề thi và các tài liệu học tập khác. Sau khi học xong một môn hoặc một phần kiến thức, họ muốn lưu tài liệu vào hệ thống để sau này có thể hỏi lại khi quên hoặc khi chưa hiểu rõ.

### Nhu cầu chính
- Hỏi lại kiến thức cũ theo ngôn ngữ tự nhiên.
- Được giải thích cặn kẽ như gia sư.
- Được tóm tắt để ôn tập nhanh.
- Được sinh câu hỏi ôn tập từ tài liệu.
- Theo dõi cuộc hội thoại liên tục mà không mất ngữ cảnh.

---

## 2. Use case cốt lõi

## UC-01: Hỏi lại một khái niệm đã học
### Mục tiêu
Người dùng muốn nhớ lại một khái niệm xuất hiện trong tài liệu đã học.

### Input
- Câu hỏi ngôn ngữ tự nhiên từ người dùng.
- Tài liệu đã upload theo môn học.

### Hành vi mong đợi
- Hệ thống truy hồi đúng đoạn định nghĩa hoặc phần liên quan.
- Giải thích rất chi tiết như gia sư.
- Chỉ rõ tài liệu, trang và đoạn đã dùng.
- Có thể nhắc lại bối cảnh hoặc khái niệm nền nếu cần.

### Ví dụ
- “BCNF là gì?”
- “Khái niệm overfitting trong tài liệu này là gì?”

---

## UC-02: Giải thích một đoạn người dùng không hiểu
### Mục tiêu
Người dùng đưa ra một đoạn hoặc hỏi về một phần cụ thể trong tài liệu mà họ thấy khó hiểu.

### Input
- Một câu hỏi hoặc đoạn tham chiếu đến tài liệu.
- Có thể kèm ngữ cảnh từ cuộc hội thoại trước.

### Hành vi mong đợi
- Hệ thống xác định đoạn liên quan trong tài liệu.
- Giải thích lại bằng ngôn ngữ dễ hiểu hơn.
- Mở rộng kiến thức liên quan để người dùng hiểu nền tảng.
- Vẫn bám sát tài liệu gốc.
- Nếu có suy luận, phải nói rõ đó là suy luận.

### Ví dụ
- “Đoạn này nói gì vậy?”
- “Tại sao trong phần này tác giả kết luận như vậy?”

---

## UC-03: Tóm tắt tài liệu hoặc một chương để ôn tập
### Mục tiêu
Người dùng muốn ôn lại nhanh nội dung của một tài liệu, một chương hoặc một chủ đề.

### Input
- Yêu cầu tóm tắt.
- Tài liệu hoặc môn học liên quan.

### Hành vi mong đợi
- Hệ thống truy hồi toàn bộ phần liên quan.
- Tóm tắt theo cấu trúc rõ ràng.
- Nhấn mạnh các ý quan trọng, khái niệm chính, công thức hoặc điểm dễ nhầm.
- Có trích nguồn cho các phần chính nếu cần.

### Ví dụ
- “Tóm tắt chương chuẩn hóa.”
- “Tóm tắt tài liệu này để ôn thi.”

---

## UC-04: Tạo câu hỏi ôn tập từ tài liệu
### Mục tiêu
Người dùng muốn luyện nhớ kiến thức bằng bộ câu hỏi được sinh ra từ tài liệu đã học.

### Input
- Yêu cầu sinh câu hỏi ôn tập.
- Một môn, một tài liệu hoặc một chương cụ thể.

### Hành vi mong đợi
- Hệ thống sinh câu hỏi dựa trên tài liệu thật.
- Câu hỏi bao phủ nội dung trọng tâm.
- Có thể sinh theo nhiều mức độ: nhận biết, hiểu, vận dụng cơ bản.
- Không tạo câu hỏi ngoài phạm vi tài liệu.

### Ví dụ
- “Tạo cho tôi 10 câu hỏi ôn tập chương này.”
- “Sinh câu hỏi tự luận ngắn từ tài liệu này.”

---

## UC-05: Hỗ trợ ôn thi theo tài liệu cá nhân
### Mục tiêu
Người dùng muốn dùng tài liệu đã upload để ôn thi có hệ thống.

### Input
- Tài liệu môn học, slide, giáo trình, đề thi.
- Yêu cầu ôn tập.

### Hành vi mong đợi
- Hệ thống tóm tắt trọng tâm.
- Trả lời câu hỏi ôn tập phát sinh.
- Tạo bộ câu hỏi ôn tập.
- Giải thích các điểm người dùng còn yếu hoặc chưa hiểu.

### Ví dụ
- “Từ toàn bộ tài liệu môn này, tôi nên ôn những gì trước?”
- “Hãy tạo bộ câu hỏi để tôi tự kiểm tra.”

---

## UC-06: Hỏi tiếp trong cùng ngữ cảnh hội thoại
### Mục tiêu
Người dùng hỏi tiếp một câu liên quan tới câu trước mà không lặp lại đầy đủ ngữ cảnh.

### Input
- Câu hỏi follow-up.
- Lịch sử hội thoại gần.

### Hành vi mong đợi
- Hệ thống nhớ ngữ cảnh đang nói về tài liệu, môn học và khái niệm nào.
- Không bắt người dùng lặp lại toàn bộ thông tin.
- Trả lời nhất quán với các lượt trước.

### Ví dụ
- “Vậy cái này khác gì phần trên?”
- “Giải thích kỹ hơn chỗ đó.”

---

## 3. Quy tắc chung cho mọi use case
- Mọi câu trả lời phải grounded trên tài liệu đã upload.
- Mọi claim quan trọng phải có bằng chứng.
- Luôn chỉ ra tài liệu, trang, đoạn hoặc chunk.
- Nếu không đủ bằng chứng, phải nói rõ.
- Mặc định trả lời rất chi tiết, theo phong cách gia sư.
- Hệ thống phải lọc đúng theo user và theo môn học.

---

## 4. Use case chưa nằm trong phạm vi V1
Các use case sau chưa đưa vào phiên bản đầu:
- chấm bài tự luận dài,
- nhận diện ảnh hoặc chữ viết tay phức tạp,
- voice/audio interaction,
- phục vụ số lượng lớn người dùng đồng thời,
- app mobile.