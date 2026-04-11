# Problem Statement

## 1. Tên bài toán
TutorRAG cho người tự học nhiều môn.

## 2. Bối cảnh
Người tự học thường học qua nhiều môn khác nhau và tiếp xúc với khối lượng lớn tài liệu như slide bài giảng, giáo trình, đề thi, ghi chú và tài liệu tham khảo. Sau một thời gian, người học khó có thể nhớ lại đầy đủ kiến thức đã học, đặc biệt là các khái niệm chi tiết, mối liên hệ giữa các phần kiến thức, và bối cảnh xuất hiện của chúng trong tài liệu gốc.

Ngoài ra, trong quá trình học, người dùng cũng thường gặp các đoạn tài liệu khó hiểu. Khi đó họ cần một hệ thống có thể giải thích lại nội dung theo cách dễ hiểu hơn, chi tiết hơn, và bám sát đúng tài liệu đang học.

## 3. Vấn đề cần giải quyết
Hiện tại người học thiếu một “bộ nhớ thứ hai” có khả năng:

- lưu trữ tài liệu học tập đã học theo từng môn,
- truy hồi đúng phần nội dung liên quan khi người dùng hỏi lại,
- giải thích cặn kẽ các khái niệm hoặc đoạn khó hiểu,
- hỗ trợ ôn thi bằng cách tóm tắt và tạo câu hỏi ôn tập,
- trả lời bám sát tài liệu cá nhân thay vì trả lời chung chung.

Vấn đề không chỉ là tìm kiếm đoạn văn bản phù hợp, mà là kết hợp giữa:
- truy hồi đúng tài liệu liên quan,
- giải thích như gia sư,
- giữ được ngữ cảnh hội thoại,
- và luôn chỉ rõ bằng chứng trong tài liệu.

## 4. Mục tiêu sản phẩm
Xây dựng một trợ lý tự học đa môn đóng vai trò như bộ nhớ thứ hai cho người dùng, cho phép người dùng tải lên tài liệu học tập cá nhân và sau đó đặt câu hỏi để:

- nhớ lại kiến thức đã học,
- hiểu rõ hơn các đoạn chưa hiểu,
- được giải thích rất chi tiết như gia sư,
- được tóm tắt nội dung để ôn tập,
- được sinh câu hỏi ôn tập từ tài liệu.

Hệ thống phải ưu tiên trả lời dựa trên tài liệu đã upload. Hệ thống được phép suy luận, nhưng mọi suy luận phải bám sát bằng chứng trong tài liệu; nếu có phần suy luận không nằm trực tiếp trong tài liệu thì phải nói rõ đó là suy luận và giải thích lý do.

## 5. Đối tượng người dùng chính
### Người dùng mục tiêu
Người tự học nhiều môn.

### Đặc điểm
- Học nhiều môn khác nhau, không giới hạn lĩnh vực.
- Thường lưu tài liệu theo môn học.
- Tài liệu chính là PDF, DOCX, PPTX, TXT.
- Hay sử dụng slide bài giảng, giáo trình và đề thi.
- Muốn hệ thống giải thích kỹ, không chỉ trả lời ngắn.
- Có nhu cầu hỏi lại kiến thức đã học sau một thời gian.
- Có nhu cầu ôn thi từ tài liệu cá nhân.

## 6. Phạm vi môn học
Hệ thống không giới hạn môn học. Miễn là người dùng đã upload tài liệu liên quan, hệ thống phải có khả năng phục vụ cho môn đó.

## 7. Giá trị cốt lõi
Hệ thống không phải chatbot chung chung. Hệ thống là một trợ lý học tập grounded trên tài liệu cá nhân, với 4 giá trị cốt lõi:

1. Truy hồi đúng phần tài liệu liên quan.
2. Giải thích chi tiết như gia sư.
3. Hỗ trợ nhớ lại và ôn tập kiến thức đã học.
4. Trích nguồn rõ ràng theo tài liệu, trang, đoạn.

## 8. Nguyên tắc trả lời
- Ưu tiên tuyệt đối tài liệu đã upload.
- Được phép suy luận nhưng phải bám tài liệu.
- Nếu có phần không nằm trực tiếp trong tài liệu, phải đánh dấu rõ là suy luận.
- Không được bịa thêm nội dung như chatbot tự do.
- Khi không đủ bằng chứng, phải nói rõ “không đủ bằng chứng”.
- Luôn chỉ ra tài liệu, trang, đoạn hoặc chunk đã dùng.

## 9. Kết quả mong muốn
Người dùng sau khi dùng hệ thống phải có thể:
- nhớ lại kiến thức nhanh hơn,
- hiểu rõ hơn nội dung khó,
- ôn tập có hệ thống hơn,
- tin tưởng câu trả lời vì có trích nguồn rõ ràng.

## 10. Tóm tắt một câu
TutorRAG là một trợ lý tự học đa môn hoạt động như bộ nhớ thứ hai, giúp người dùng hỏi lại và hiểu lại kiến thức từ chính tài liệu cá nhân của mình bằng các câu trả lời chi tiết, có suy luận bám tài liệu và có trích nguồn rõ ràng.