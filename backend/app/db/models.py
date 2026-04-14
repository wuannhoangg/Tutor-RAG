from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .base import Base

JSONType = JSON().with_variant(JSONB, "postgresql")


class User(Base):
    __tablename__ = "users"

    id = Column(String(128), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    llm_config = Column(JSONType, nullable=True)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"


class Folder(Base):
    __tablename__ = "folders"

    folder_id = Column(String(128), primary_key=True, index=True)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    is_system = Column(String(5), nullable=False, default="false")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    documents = relationship("Document", back_populates="folder", passive_deletes=True)

    def __repr__(self) -> str:
        return f"Folder(folder_id={self.folder_id!r}, name={self.name!r})"


class Document(Base):
    __tablename__ = "documents"

    document_id = Column(String(128), primary_key=True, index=True)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    folder_id = Column(String(128), ForeignKey("folders.folder_id", ondelete="SET NULL"), index=True, nullable=True)
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

    folder = relationship("Folder", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self) -> str:
        return f"Document(document_id={self.document_id!r}, title={self.title!r})"


class Chunk(Base):
    __tablename__ = "chunks"

    chunk_id = Column(String(128), primary_key=True, index=True)
    document_id = Column(String(128), ForeignKey("documents.document_id", ondelete="CASCADE"), index=True, nullable=False)
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
    __tablename__ = "answers"

    answer_id = Column(Integer, primary_key=True, autoincrement=True)
    query_id = Column(String(128), index=True, nullable=True)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    answer_text = Column(Text, nullable=False)
    reasoning_summary = Column(JSONType, nullable=True)
    confidence = Column(Float, nullable=True)
    extra_metadata = Column(JSONType, nullable=True)

    citations = relationship("Citation", back_populates="answer", cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self) -> str:
        return f"Answer(answer_id={self.answer_id!r}, query_id={self.query_id!r})"


class Citation(Base):
    __tablename__ = "citations"

    citation_id = Column(Integer, primary_key=True, autoincrement=True)
    answer_id = Column(Integer, ForeignKey("answers.answer_id", ondelete="CASCADE"), index=True, nullable=False)
    document_id = Column(String(128), ForeignKey("documents.document_id", ondelete="SET NULL"), index=True, nullable=True)
    chunk_id = Column(String(128), ForeignKey("chunks.chunk_id", ondelete="SET NULL"), index=True, nullable=True)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    extra_metadata = Column(JSONType, nullable=True)

    answer = relationship("Answer", back_populates="citations")


class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    answer_id = Column(Integer, ForeignKey("answers.answer_id", ondelete="SET NULL"), index=True, nullable=True)
    query_id = Column(String(128), index=True, nullable=True)
    rating = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
