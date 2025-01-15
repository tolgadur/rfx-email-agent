from typing import List
from litellm import embedding
from app.config import EMBEDDING_MODEL, SIMILARITY_THRESHOLD
from app.db_handler import DatabaseHandler
from app.models import Embedding, Document
from app.data_types import DocumentMatch, EmbeddingsError


class EmbeddingsDAO:
    """Handles vector storage and similarity search using pgvector."""

    def __init__(self, db_handler: DatabaseHandler):
        """Initialize the vector store with a database handler.

        Args:
            db_handler: Database connection handler
        """
        self.db_handler = db_handler

    def add_text(
        self, text: str, document_id: int, embedding_metadata: dict = {}, session=None
    ) -> None:
        """Add text to the vector store.

        Args:
            text: The text to add
            document_id: ID of the associated Document
            embedding_metadata: Optional metadata to store with the text
            session: Optional SQLAlchemy session to use. If not provided, creates a new.

        Raises:
            EmbeddingsError: If adding the text fails
        """
        try:
            embedding_vector = self._generate_embedding(text)
            embedding_obj = Embedding(
                text=text,
                embedding=embedding_vector,
                embedding_metadata=embedding_metadata,
                document_id=document_id,
            )

            if session is None:
                with self.db_handler.get_session() as session:
                    session.add(embedding_obj)
                    session.commit()
            else:
                session.add(embedding_obj)
                # Let caller handle commit
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
                results = (
                    session.query(
                        Embedding.text,
                        Embedding.embedding_metadata,
                        Document,
                        (
                            1 - Embedding.embedding.cosine_distance(query_embedding)
                        ).label("similarity"),
                    )
                    .join(Document, Document.id == Embedding.document_id)
                    .where(
                        (1 - Embedding.embedding.cosine_distance(query_embedding))
                        >= SIMILARITY_THRESHOLD
                    )
                    .limit(limit)
                    .all()
                )

                return [
                    DocumentMatch(
                        text=row[0],
                        embedding_metadata=row[1],
                        document=row[2],
                        similarity=float(row[3]),
                    )
                    for row in results
                ]
        except Exception as e:
            raise EmbeddingsError(f"Failed to query embeddings: {e}")

    def delete_embedding(self, text: str) -> None:
        """Delete an embedding from the vector store.

        Args:
            text: The text of the embedding to delete

        Raises:
            EmbeddingsError: If deleting the embedding fails
        """
        try:
            with self.db_handler.get_session() as session:
                embedding_obj = (
                    session.query(Embedding).filter(Embedding.text == text).first()
                )
                if embedding_obj:
                    session.delete(embedding_obj)
                    session.commit()
        except Exception as e:
            raise EmbeddingsError(f"Failed to delete embedding: {e}")

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
            response = embedding(model=EMBEDDING_MODEL, input=[text])
            # Return as a simple list - pgvector will handle the conversion
            return response["data"][0]["embedding"]
        except Exception as e:
            raise EmbeddingsError(f"Failed to generate embedding: {e}")
