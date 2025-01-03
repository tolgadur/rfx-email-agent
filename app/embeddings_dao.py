from dataclasses import dataclass
from typing import List
from litellm import embedding
from app.db_handler import DatabaseHandler
from app.models import Document


@dataclass
class DocumentMatch:
    text: str
    similarity: float
    document_metadata: dict


class EmbeddingsError(Exception):
    """Base exception for embeddings operations."""

    pass


class EmbeddingsDAO:
    """Handles vector storage and similarity search using pgvector."""

    def __init__(self, db_handler: DatabaseHandler):
        """Initialize the vector store with a database handler.

        Args:
            db_handler: Database connection handler
        """
        self.db_handler = db_handler

    def add_text(self, text: str, document_metadata: dict = {}) -> None:
        """Add text to the vector store.

        Args:
            text: The text to add
            metadata: Optional metadata to store with the text

        Raises:
            EmbeddingsError: If adding the text fails
        """
        try:
            if "processed_document_id" not in document_metadata:
                raise ValueError(
                    "processed_document_id is required in document_metadata"
                )

            processed_document_id = document_metadata.pop("processed_document_id")
            embedding_vector = self._generate_embedding(text)
            document = Document(
                text=text,
                embedding=embedding_vector,
                document_metadata=document_metadata,
                processed_document_id=processed_document_id,
            )
            with self.db_handler.get_session() as session:
                session.add(document)
                session.commit()
        except Exception as e:
            raise EmbeddingsError(f"Failed to add text: {e}")

    def query_embeddings(self, query: str, limit: int = 5) -> List[DocumentMatch]:
        """Find similar documents based on vector similarity.

        Args:
            query: The query text to find similar documents for
            limit: Maximum number of results to return

        Returns:
            List of DocumentMatch objects sorted by similarity (highest first)

        Raises:
            EmbeddingsError: If querying embeddings fails
        """
        try:
            query_embedding = self._generate_embedding(query)

            with self.db_handler.get_session() as session:
                # Use cosine distance directly with the <=> operator
                # Lower distance means higher similarity
                results = (
                    session.query(
                        Document.text,
                        Document.document_metadata,
                        Document.embedding.cosine_distance(query_embedding).label(
                            "distance"
                        ),
                    )
                    .order_by(Document.embedding.cosine_distance(query_embedding))
                    .limit(limit)
                    .all()
                )

                return [
                    DocumentMatch(
                        text=row[0],
                        document_metadata=row[1],
                        # Convert distance to similarity score (1 - distance)
                        similarity=float(1 - row[2]),
                    )
                    for row in results
                ]
        except Exception as e:
            raise EmbeddingsError(f"Failed to query embeddings: {e}")

    def delete_embedding(self, text: str) -> None:
        """Delete a document from the vector store.

        Args:
            text: The text of the document to delete

        Raises:
            EmbeddingsError: If deleting the document fails
        """
        try:
            with self.db_handler.get_session() as session:
                doc = session.query(Document).filter(Document.text == text).first()
                if doc:
                    session.delete(doc)
                    session.commit()
        except Exception as e:
            raise EmbeddingsError(f"Failed to delete document: {e}")

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for the given text using OpenAI's API.

        Args:
            text: The text to generate an embedding for

        Returns:
            A list of floats representing the embedding vector

        Raises:
            EmbeddingsError: If generating the embedding fails
        """
        try:
            response = embedding(model="text-embedding-ada-002", input=[text])
            # Return as a simple list - pgvector will handle the conversion
            return response["data"][0]["embedding"]
        except Exception as e:
            raise EmbeddingsError(f"Failed to generate embedding: {e}")
