from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import JSON, String, DateTime, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)
    document_metadata: Mapped[dict] = mapped_column(JSON, default={})
    processed_document_id: Mapped[int] = mapped_column(
        ForeignKey("processed_documents.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship to ProcessedDocument
    processed_document: Mapped["ProcessedDocument"] = relationship(
        "ProcessedDocument", back_populates="documents"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "embedding": self.embedding,
            "document_metadata": self.document_metadata,
            "processed_document_id": self.processed_document_id,
            "filepath": self.processed_document.filepath,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return (
            f"<Document(id={self.id}, text={self.text}, "
            f"embedding={self.embedding}, document_metadata={self.document_metadata}, "
            f"processed_document_id={self.processed_document_id}, "
            f"created_at={self.created_at}, updated_at={self.updated_at})>"
        )


class ProcessedDocument(Base):
    """Model for tracking which documents have been processed."""

    __tablename__ = "processed_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    filepath: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    link: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationship to Document
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="processed_document"
    )
