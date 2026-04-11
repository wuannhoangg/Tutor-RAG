from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .base import Base

JSONType = JSON().with_variant(JSONB, "postgresql")


class User(Base):
    """Represents a system or human user authenticated via Supabase."""
    __tablename__ = "users"

    id = Column(String(128), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    llm_config = Column(JSONType, nullable=True)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"


class Document(Base):
    """Metadata for an uploaded document."""
    __tablename__ = "documents"

    document_id = Column(String(128), primary_key=True, index=True)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    subject = Column(String(255), index=True, nullable=True)
    title = Column(String(500), nullable=True)
    source_type = Column(String(50), nullable=True)
    language = Column(String(32), nullable=True)
    file_name = Column(String(500), nullable=True)
    file_path = Column(String(1000), nullable=True)
    mime_type = Column(String(255), nullable=True)
    checksum_sha256 = Column(String(128), nullable=True)
    status = Column(String(50), nullable=True)
    tags = Column(JSONType, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    chunks = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"Document(document_id={self.document_id!r}, title={self.title!r})"


class Chunk(Base):
    """Represents a semantically chunked piece of text from a document."""
    __tablename__ = "chunks"

    chunk_id = Column(String(128), primary_key=True, index=True)
    document_id = Column(
        String(128),
        ForeignKey("documents.document_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    subject = Column(String(255), index=True, nullable=True)
    chapter = Column(String(255), nullable=True)
    section = Column(String(255), nullable=True)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    content_type = Column(String(100), nullable=True)
    text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    keywords = Column(JSONType, nullable=True)

    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"Chunk(chunk_id={self.chunk_id!r}, document_id={self.document_id!r})"


class Answer(Base):
    """Stores the final synthesized answer and optional evidence linkage."""
    __tablename__ = "answers"

    answer_id = Column(Integer, primary_key=True, autoincrement=True)
    query_id = Column(String(128), index=True, nullable=True)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    answer_text = Column(Text, nullable=False)
    reasoning_summary = Column(JSONType, nullable=True)
    confidence = Column(Float, nullable=True)
    extra_metadata = Column(JSONType, nullable=True)

    citations = relationship(
        "Citation",
        back_populates="answer",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"Answer(answer_id={self.answer_id!r}, query_id={self.query_id!r})"


class Citation(Base):
    """Links an answer to supporting evidence chunks."""
    __tablename__ = "citations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    answer_id = Column(
        Integer,
        ForeignKey("answers.answer_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    document_id = Column(String(128), ForeignKey("documents.document_id", ondelete="CASCADE"), index=True, nullable=True)
    chunk_id = Column(String(128), ForeignKey("chunks.chunk_id", ondelete="CASCADE"), index=True, nullable=True)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    snippet = Column(Text, nullable=True)
    extra_metadata = Column(JSONType, nullable=True)

    answer = relationship("Answer", back_populates="citations")

    def __repr__(self) -> str:
        return f"Citation(id={self.id!r}, answer_id={self.answer_id!r})"


class Feedback(Base):
    """Stores user feedback on an answer or query."""
    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    query_id = Column(String(128), index=True, nullable=True)
    feedback_text = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"Feedback(feedback_id={self.feedback_id!r}, query_id={self.query_id!r})"
