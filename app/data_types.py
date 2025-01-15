from dataclasses import dataclass
from typing import Optional
from app.models import Document
from pydantic import BaseModel, HttpUrl


class EmbeddingsError(Exception):
    """Base exception for embeddings operations."""

    pass


@dataclass
class DocumentMatch:
    text: str
    similarity: float
    embedding_metadata: dict
    document: Document


@dataclass
class RAGResponse:
    text: str
    max_similarity: Optional[float]
    document_url: Optional[str] = None


class PDFUrlRequest(BaseModel):
    url: HttpUrl
    password: str
