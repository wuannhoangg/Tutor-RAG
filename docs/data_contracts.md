# Data Contracts

## 1. Mục tiêu
Tài liệu này định nghĩa data contract chuẩn cho TutorRAG V1 để các module ingestion, indexing, retrieval, reasoning, verification, logging và API trao đổi dữ liệu nhất quán.

Tài liệu này **bám đúng implementation hiện tại** trong `app/schemas/*.py` và `models.py`. Nếu code thay đổi, file này cũng phải được cập nhật theo.

---

## 2. Phạm vi và nguyên tắc chung

### 2.1 Phạm vi
Data contract hiện tại bao phủ các nhóm dữ liệu sau:
- document metadata,
- chunk metadata,
- concept metadata,
- query/request pipeline,
- evidence và citation,
- answer/verification output,
- feedback,
- các filter/phân trang cơ bản.

### 2.2 Nguyên tắc chung
- Mỗi entity có trách nhiệm rõ ràng.
- Mọi ID hiện tại đều là `str`; code **chưa áp regex/prefix bắt buộc**, nên quy ước tên ID là convention ở tầng application, không phải validation cứng ở schema.
- Timestamp dùng `datetime` timezone-aware; các model timestamp nội bộ dùng UTC thông qua `utc_now()`.
- Mọi truy vấn online phải gắn với `user_id`.
- Nếu người dùng chọn môn học, pipeline nên ưu tiên `subject_hint` ở request và `subject` ở metadata filter.
- Mọi answer cuối phải truy ngược được về citation/evidence ở mức `chunk` và `document`.
- Mọi claim quan trọng nên có citation; nếu không có support trực tiếp thì phải được đánh dấu là suy luận hoặc unsupported.
- Các Pydantic schema hiện dùng `extra="forbid"`, nên payload gửi sai field sẽ bị reject.

### 2.3 Chuẩn serialization
- Enum được serialize bằng **value string**, không phải tên enum.
- Chuỗi được strip whitespace ở đầu/cuối.
- Các list/dict mặc định dùng empty collection thay vì `null`, trừ khi field được khai báo optional.

---

## 3. Shared enums và kiểu dùng chung

### 3.1 SourceType
Giá trị hợp lệ:
- `pdf`
- `docx`
- `pptx`
- `txt`
- `markdown`
- `unknown`

### 3.2 DocumentStatus
Giá trị hợp lệ:
- `uploaded`
- `parsed`
- `normalized`
- `chunked`
- `indexed`
- `failed`

### 3.3 ContentType
Giá trị hợp lệ:
- `definition`
- `example`
- `theorem`
- `proof`
- `exercise`
- `solution`
- `summary`
- `explanation`
- `formula`
- `table`
- `bullet_list`
- `paragraph`
- `unknown`

### 3.4 StudyMode
Giá trị hợp lệ:
- `ask`
- `explain`
- `review`
- `summarize`
- `quiz`

### 3.5 QueryType
Giá trị hợp lệ:
- `definition_qa`
- `explanation_qa`
- `comparison_qa`
- `why_reasoning`
- `exercise_support`
- `chapter_summary`
- `quiz_generation`
- `unknown`

### 3.6 ReasoningDepth
Giá trị hợp lệ:
- `low`
- `medium`
- `high`

### 3.7 DifficultyLevel
Giá trị hợp lệ:
- `easy`
- `medium`
- `hard`
- `unknown`

### 3.8 EvidenceRole
Giá trị hợp lệ:
- `primary_definition`
- `supporting_explanation`
- `example`
- `counter_example`
- `solution_rationale`
- `summary_source`
- `prerequisite`
- `unknown`

### 3.9 ClaimSupportStatus
Giá trị hợp lệ:
- `supported`
- `partially_supported`
- `unsupported`

### 3.10 FeedbackRating
Giá trị hợp lệ:
- `thumbs_up`
- `thumbs_down`
- `neutral`

### 3.11 MetadataFilter
Dùng để filter retrieval/query plan.

Field:
- `user_id: str` — bắt buộc.
- `subject: str | None`
- `document_id: str | None`
- `chapter: str | None`
- `section: str | None`
- `content_types: list[ContentType] = []`

### 3.12 Pagination
Field:
- `limit: int = 10` với range `1..100`
- `offset: int = 0` với `offset >= 0`

---

## 4. Document contracts

### 4.1 DocumentCreate
Mục đích: payload tạo document metadata khi user upload file.

Field:
- `user_id: str`
- `subject: str` — bắt buộc, `1..100` ký tự.
- `title: str` — bắt buộc, `1..255` ký tự.
- `source_type: SourceType`
- `language: str = "vi"`
- `file_name: str`
- `file_path: str`
- `mime_type: str | None = None`
- `checksum_sha256: str | None = None`
- `tags: list[str] = []`
- `status: DocumentStatus = "uploaded"`

Ví dụ:
```json
{
  "user_id": "user_001",
  "subject": "database",
  "title": "Normalization Slides",
  "source_type": "pdf",
  "language": "vi",
  "file_name": "norm_slides.pdf",
  "file_path": "storage/user_001/database/norm_slides.pdf",
  "mime_type": "application/pdf",
  "checksum_sha256": "abc123",
  "tags": ["normalization", "slides"],
  "status": "uploaded"
}
```

### 4.2 DocumentUpdate
Mục đích: payload update metadata đã tồn tại.

Tất cả field đều optional:
- `subject: str | None`
- `title: str | None`
- `language: str | None`
- `tags: list[str] | None`
- `status: DocumentStatus | None`

### 4.3 DocumentRecord
Mục đích: record đầy đủ của document sau khi persist.

Field:
- toàn bộ field của `DocumentCreate`
- `document_id: str`
- `uploaded_at: datetime`
- `last_indexed_at: datetime | None = None`
- `page_count: int | None = None`
- `storage_provider: str = "local"`
- `extra_metadata: dict[str, Any] = {}`
- `created_at: datetime`
- `updated_at: datetime`

Ghi chú:
- `uploaded_at` là thời điểm file được nhận vào hệ thống.
- `created_at`/`updated_at` là timestamp ở tầng record/model.
- `page_count` chỉ có khi parser/storage trả được thông tin này.

### 4.4 DocumentSummary
Mục đích: payload tóm tắt nhẹ để list document.

Field:
- `document_id: str`
- `user_id: str`
- `subject: str`
- `title: str`
- `source_type: SourceType`
- `status: DocumentStatus`
- `uploaded_at: datetime`

---

## 5. Chunk contracts

### 5.1 ChunkCreate
Mục đích: payload tạo chunk sau bước parse + normalize + chunking.

Field:
- `document_id: str`
- `user_id: str`
- `subject: str`
- `chapter: str | None = None`
- `section: str | None = None`
- `heading_path: list[str] = []`
- `page_start: int` với `>= 1`
- `page_end: int` với `>= 1`
- `content_type: ContentType = "unknown"`
- `text: str`
- `normalized_text: str | None = None`
- `token_count: int` với `>= 1`
- `keywords: list[str] = []`
- `language: str = "vi"`
- `chunk_index: int` với `>= 0`
- `overlap_from_previous: int = 0`

### 5.2 ChunkRecord
Mục đích: record chunk đầy đủ sau khi persist.

Field:
- toàn bộ field của `ChunkCreate`
- `chunk_id: str`
- `source_block_ids: list[str] = []`
- `parser_name: str | None = None`
- `parser_confidence: float | None = None` với range `0..1`
- `difficulty: str | None = None`
- `parent_chunk_id: str | None = None`
- `created_at: datetime`
- `updated_at: datetime`

Ghi chú quan trọng:
- `difficulty` trong implementation hiện tại là `str | None`, **không phải** `DifficultyLevel` enum.
- Citation hiện truy vết tới `chunk_id`, nên `chunk_id` phải ổn định.
- `source_block_ids` dùng để nối ngược về parse blocks nếu parser có block-level output.

### 5.3 ChunkSummary
Mục đích: payload nhẹ cho retrieval preview hoặc response phụ trợ.

Field:
- `chunk_id: str`
- `document_id: str`
- `subject: str`
- `chapter: str | None`
- `section: str | None`
- `page_start: int`
- `page_end: int`
- `content_type: ContentType`

---

## 6. Concept contracts

### 6.1 ConceptCreate
Mục đích: record khái niệm sinh ra từ offline enrichment.

Field:
- `user_id: str`
- `subject: str`
- `name: str`
- `aliases: list[str] = []`
- `related_keywords: list[str] = []`
- `definition_chunk_ids: list[str] = []`
- `related_concepts: list[str] = []`

### 6.2 ConceptRecord
Mục đích: record khái niệm đầy đủ sau khi persist.

Field:
- toàn bộ field của `ConceptCreate`
- `concept_id: str`
- `prerequisite_concepts: list[str] = []`
- `example_chunk_ids: list[str] = []`
- `created_at: datetime`
- `updated_at: datetime`

Ghi chú:
- Contract hiện tại dùng quan hệ nhẹ bằng list ID/string, chưa có graph edge entity riêng.
- `definition_chunk_ids` và `example_chunk_ids` là cầu nối từ concept sang chunk.

---

## 7. Evidence và citation contracts

### 7.1 Citation
Mục đích: citation gọn để gắn vào answer.

Field:
- `document_id: str`
- `document_title: str`
- `chunk_id: str`
- `page_start: int`
- `page_end: int`
- `quoted_text: str | None = None`

Ghi chú:
- Citation hiện ở mức `document + chunk + page range`.
- Contract hiện tại **chưa có** `paragraph_id`, `section_id` hay offset ký tự.

### 7.2 EvidenceItem
Mục đích: lưu một bằng chứng đã được retrieval/rerank chọn ra cho request cụ thể.

Field:
- `evidence_id: str`
- `request_id: str`
- `chunk_id: str`
- `document_id: str`
- `user_id: str`
- `subject: str`
- `role: EvidenceRole = "unknown"`
- `excerpt: str`
- `page_start: int`
- `page_end: int`
- `retrieved_for: str`
- `dense_score: float | None = None`
- `sparse_score: float | None = None`
- `rerank_score: float | None = None`
- `final_score: float | None = None`
- `is_selected: bool = true`
- `created_at: datetime`
- `updated_at: datetime`

Ghi chú:
- `retrieved_for` mô tả evidence được lấy để phục vụ câu hỏi/sub-question nào.
- Các score là nullable vì một số pipeline có thể chưa chạy đủ dense/sparse/rerank.
- `is_selected` cho phép log cả evidence bị loại hay được giữ lại.

### 7.3 EvidenceSet
Mục đích: group evidence theo một request.

Field:
- `request_id: str`
- `evidence_items: list[EvidenceItem] = []`

---

## 8. Query pipeline contracts

### 8.1 ChatTurn
Mục đích: một lượt hội thoại đầu vào.

Field:
- `role: str` — chỉ nhận `user`, `assistant`, hoặc `system`
- `content: str`
- `timestamp: datetime | None = None`

### 8.2 QueryRequest
Mục đích: payload đầu vào chuẩn cho online pipeline.

Field:
- `request_id: str`
- `session_id: str`
- `user_id: str`
- `question: str`
- `subject_hint: str | None = None`
- `study_mode: StudyMode = "ask"`
- `chat_history: list[ChatTurn] = []`
- `preferred_language: str = "vi"`

Ghi chú:
- `subject_hint` là gợi ý từ UI/user để thu hẹp phạm vi theo môn.
- `session_id` dùng để nối các lượt trong cùng phiên hội thoại.

Ví dụ:
```json
{
  "request_id": "req_001",
  "session_id": "sess_001",
  "user_id": "user_001",
  "question": "BCNF là gì?",
  "subject_hint": "database",
  "study_mode": "explain",
  "chat_history": [
    {
      "role": "user",
      "content": "Tôi đang ôn chuẩn hóa"
    }
  ],
  "preferred_language": "vi"
}
```

### 8.3 QueryAnalysis
Mục đích: output của bước query understanding/classification.

Field:
- `request_id: str`
- `query_type: QueryType = "unknown"`
- `requires_multi_hop: bool = false`
- `preferred_content_types: list[ContentType] = []`
- `reasoning_depth: ReasoningDepth = "low"`
- `detected_subject: str | None = None`
- `difficulty_level: DifficultyLevel = "unknown"`
- `intent_notes: str | None = None`
- `created_at: datetime`
- `updated_at: datetime`

### 8.4 SubQuestion
Mục đích: đơn vị decomposition cho planner.

Field:
- `sub_question_id: str`
- `question: str`
- `purpose: str`
- `preferred_content_types: list[ContentType] = []`

### 8.5 QueryPlan
Mục đích: kế hoạch retrieval/reasoning cho một request.

Field:
- `request_id: str`
- `main_question: str`
- `sub_questions: list[SubQuestion] = []`
- `filters: MetadataFilter`
- `retrieval_strategy: str = "hybrid"`
- `stop_conditions: list[str] = ["enough_evidence", "max_rounds_reached"]`
- `planner_notes: str | None = None`
- `max_retrieval_rounds: int = 2` với range `1..5`
- `extra: dict[str, Any] = {}`
- `created_at: datetime`
- `updated_at: datetime`

Ghi chú:
- `filters.user_id` là bắt buộc.
- `retrieval_strategy` hiện là `str`, chưa dùng enum cứng.
- `extra` là chỗ mở rộng an toàn cho planner metadata.

---

## 9. Answer contracts

### 9.1 AnswerClaim
Mục đích: đơn vị claim có thể kiểm chứng trong câu trả lời.

Field:
- `claim_id: str`
- `text: str`
- `support_status: ClaimSupportStatus = "supported"`
- `citation_chunk_ids: list[str] = []`
- `is_inference: bool = false`
- `inference_reason: str | None = None`

Ghi chú:
- `citation_chunk_ids` là liên kết nhẹ từ claim sang chunk.
- Nếu `is_inference = true`, nên có `inference_reason` để giải thích logic suy luận.

### 9.2 AnswerDraft
Mục đích: kết quả nháp trước khi persist answer cuối.

Field:
- `request_id: str`
- `direct_answer: str`
- `reasoning_summary: list[str] = []`
- `claims: list[AnswerClaim] = []`
- `citations: list[Citation] = []`

### 9.3 AnswerRecord
Mục đích: answer cuối đã log/persist.

Field:
- `answer_id: str`
- `request_id: str`
- `session_id: str`
- `user_id: str`
- `final_answer: str`
- `reasoning_summary: list[str] = []`
- `claims: list[AnswerClaim] = []`
- `citations: list[Citation] = []`
- `verified: bool = false`
- `confidence: float = 0.0` với range `0..1`
- `insufficient_evidence: bool = false`
- `verifier_notes: list[str] = []`
- `latency_ms: int | None = None`
- `prompt_version: str | None = None`
- `created_at: datetime`
- `updated_at: datetime`

Ghi chú:
- `verified` là cờ tổng hợp sau bước verification.
- `insufficient_evidence = true` là tín hiệu hệ thống không đủ căn cứ để kết luận chắc.
- `claims` và `citations` đang được lưu dạng nested JSON trong persistence layer.

---

## 10. Feedback contract

### 10.1 FeedbackRecord
Mục đích: log feedback người dùng cho answer.

Field:
- `feedback_id: str`
- `answer_id: str`
- `request_id: str`
- `user_id: str`
- `rating: FeedbackRating = "neutral"`
- `is_helpful: bool | None = None`
- `note: str | None = None`
- `created_at: datetime`
- `updated_at: datetime`

---

## 11. Quan hệ traceability bắt buộc

### 11.1 Chuỗi truy vết chính
Chuỗi truy vết chuẩn của hệ thống là:

`Document -> Chunk -> EvidenceItem/Citation -> AnswerClaim -> AnswerRecord`

Điều này có nghĩa là:
- mọi citation phải chỉ tới `chunk_id` và `document_id`,
- mọi evidence phải chỉ tới `chunk_id`, `document_id`, `request_id`, `user_id`,
- mọi answer cuối phải mang `request_id`, `session_id`, `user_id`,
- claim-level support nên map được về ít nhất một `chunk_id` thông qua `citation_chunk_ids`.

### 11.2 Subject scoping
- `subject` tồn tại ở `Document`, `Chunk`, `Concept`, `EvidenceItem`.
- `subject_hint` tồn tại ở `QueryRequest`.
- `detected_subject` tồn tại ở `QueryAnalysis`.
- `filters.subject` tồn tại ở `QueryPlan`.

Pipeline nên dùng các field này để giới hạn truy hồi đúng môn học.

### 11.3 User scoping
Ít nhất các entity sau phải gắn `user_id`:
- `Document*`
- `Chunk*`
- `Concept*`
- `QueryRequest`
- `EvidenceItem`
- `AnswerRecord`
- `FeedbackRecord`

`Citation` hiện không có `user_id` riêng vì nó là nested object phụ thuộc context của answer/evidence.

---

## 12. Persistence mapping hiện tại

Các entity đang có bảng SQLAlchemy tương ứng:
- `documents`
- `chunks`
- `concepts`
- `query_requests`
- `query_analyses`
- `query_plans`
- `evidence_items`
- `answer_records`
- `feedback_records`

Các entity **chưa có bảng riêng**, đang tồn tại như nested structure hoặc DTO:
- `Citation`
- `EvidenceSet`
- `AnswerDraft`
- `AnswerClaim` (được nested trong `AnswerRecord.claims`)
- `SubQuestion` (được nested trong `QueryPlan.sub_questions`)
- `ChatTurn` (được nested trong `QueryRequest.chat_history`)
- các summary model như `DocumentSummary`, `ChunkSummary`

---

## 13. Invariants và validation rules nên giữ

### 13.1 Bắt buộc ở online pipeline
- `QueryRequest.user_id`, `request_id`, `session_id`, `question` không được thiếu.
- `QueryPlan.filters.user_id` không được thiếu.
- `AnswerRecord.request_id`, `session_id`, `user_id` không được thiếu.

### 13.2 Bắt buộc ở evidence/citation
- `Citation.page_start` và `page_end` phải >= 1.
- `EvidenceItem.page_start` và `page_end` phải >= 1.
- `EvidenceItem.excerpt` không được rỗng.

### 13.3 Bắt buộc ở chunk/document
- `ChunkRecord.token_count >= 1`
- `ChunkRecord.chunk_index >= 0`
- `Document.subject` không được rỗng.
- `Document.title` không được rỗng.

### 13.4 Cờ suy luận và thiếu bằng chứng
- Nếu claim không có support trực tiếp, nên dùng `support_status = "partially_supported"` hoặc `"unsupported"`.
- Nếu answer tổng thể không đủ căn cứ, nên đặt `insufficient_evidence = true`.
- Nếu answer có suy luận vượt ra ngoài phát biểu trực tiếp của tài liệu, claim tương ứng nên có `is_inference = true` và ghi `inference_reason`.

---

## 14. Những gì contract hiện tại CHƯA có

Để tránh hiểu nhầm, implementation hiện tại **chưa định nghĩa riêng**:
- parse block entity,
- parser output entity,
- embedding vector contract,
- sparse index posting contract,
- reranker result contract tách riêng,
- verifier report entity tách riêng,
- evaluation sample / benchmark / metric entity,
- relation-edge entity cho concept graph,
- citation offset ở mức sentence/character.

Nếu bước sau của dự án cần các thành phần trên, nên thêm schema mới thay vì nhồi vào `extra_metadata` hoặc `extra` quá nhiều.

---

## 15. Tóm tắt ngắn
Data contract hiện tại của TutorRAG V1 xoay quanh 9 nhóm schema chính: document, chunk, concept, query request, query analysis, query plan, evidence, answer và feedback. Hệ thống được thiết kế để đảm bảo traceability theo chuỗi document -> chunk -> evidence/citation -> answer, đồng thời luôn gắn `user_id`, ưu tiên `subject`, và giữ khả năng mở rộng bằng nested JSON cho các thành phần planner/claim/citation.
