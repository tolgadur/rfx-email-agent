from dataclasses import dataclass
from typing import List
from litellm import embedding
from app.db_handler import DatabaseHandler


@dataclass
class DocumentMatch:
    text: str
    similarity: float
    metadata: dict


class VectorStore:
    """Handles vector storage and similarity search using pgvector."""

    def __init__(self, db_handler: DatabaseHandler):
        """Initialize the vector store with a database handler.

        Args:
            db_handler: Database connection handler
        """
        self.db_handler = db_handler

    def add_text(self, text: str, metadata: dict = None) -> None:
        """Add text to the vector store.

        Args:
            text: The text to add
            metadata: Optional metadata to store with the text
        """
        if metadata is None:
            metadata = {}

        embedding_vector = self._generate_embedding(text)

        self.db_handler.execute_write(
            """
            INSERT INTO documents (text, embedding, metadata)
            VALUES (%s, %s, %s)
            """,
            (text, embedding_vector, metadata),
        )

    def query_embeddings(self, query: str, limit: int = 5) -> List[DocumentMatch]:
        """Find similar documents based on vector similarity.

        Args:
            query: The query text to find similar documents for
            limit: Maximum number of results to return

        Returns:
            List of DocumentMatch objects sorted by similarity (highest first)
        """
        query_embedding = self._generate_embedding(query)

        results = self.db_handler.select_all(
            """
            SELECT text, metadata, 1 - (embedding <=> %s::vector) as similarity
            FROM documents
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, limit),
        )

        return [
            DocumentMatch(text=row[0], metadata=row[1], similarity=row[2])
            for row in results
        ]

    def delete_embedding(self, text: str) -> None:
        """Delete a document from the vector store.

        Args:
            text: The text of the document to delete
        """
        self.db_handler.execute_write(
            "DELETE FROM documents WHERE text = %s",
            (text,),
        )

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for the given text using OpenAI's API.

        Args:
            text: The text to generate an embedding for

        Returns:
            A list of floats representing the embedding
        """
        response = embedding(model="text-embedding-ada-002", input=[text])
        # Response format is a dict with 'data' list containing embedding objects
        return response["data"][0]["embedding"]
