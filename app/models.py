from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import JSON, String, DateTime, func, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class Document(Base):
    """Model for tracking documents and their processing status."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filepath: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    embeddings: Mapped[list["Embedding"]] = relationship(
        "Embedding", back_populates="document"
    )

    def __repr__(self) -> str:
        return (
            f"<Document(id={self.id}, filepath={self.filepath}, "
            f"url={self.url}, processed={self.processed}, "
            f"created_at={self.created_at}, updated_at={self.updated_at})>"
        )


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(3072), nullable=False)
    embedding_metadata: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    document: Mapped["Document"] = relationship("Document", back_populates="embeddings")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "embedding": self.embedding,
            "embedding_metadata": self.embedding_metadata,
            "document_id": self.document_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return (
            f"<Embedding(id={self.id}, text={self.text}, "
            f"embedding={self.embedding}, "
            f"embedding_metadata={self.embedding_metadata}, "
            f"document_id={self.document_id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at})>"
        )
