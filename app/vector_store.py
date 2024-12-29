from typing import List, Dict
from psycopg2.extras import Json
from app.db_handler import DatabaseHandler


class VectorStore:
    """Vector store for document embeddings."""

    def __init__(self, db_handler: DatabaseHandler):
        """Initialize the vector store with database handler.

        Args:
            db_handler (DatabaseHandler): Database connection handler
        """
        self.db = db_handler

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for the given text.

        This is a placeholder for your embedding model implementation.
        """
        raise NotImplementedError(
            "Embedding generation not implemented. "
            "Please implement with your chosen model."
        )

    def add_text(self, text: str, metadata: Dict) -> int:
        """
        Adds a document to the database by generating its embedding and storing it.

        Args:
            text (str): The raw document text to be stored.
            metadata (dict): Additional metadata (e.g., title, tags).

        Returns:
            int: The ID of the inserted document.

        Raises:
            Exception: If embedding generation or insertion fails.
        """
        embedding = self._generate_embedding(text)
        return self.db.insert_returning_id(
            """
            INSERT INTO documents (text, embedding, metadata)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (text, embedding, Json(metadata)),
        )

    def query_embeddings(
        self, query: str, similarity_threshold: float, top_k: int = 5
    ) -> List[Dict]:
        """
        Finds documents similar to the given query string.

        Args:
            query (str): The plain English query to search for.
            similarity_threshold (float): Minimum similarity score (0-1).
            top_k (int): Number of top results to return.

        Returns:
            list[dict]: A list of documents with metadata and similarity scores.

        Raises:
            Exception: If the query or database interaction fails.
        """
        query_embedding = self._generate_embedding(query)
        rows = self.db.select_all(
            """
            SELECT 
                id,
                text,
                metadata,
                1 - (embedding <=> %s) as similarity
            FROM documents
            WHERE 1 - (embedding <=> %s) > %s
            ORDER BY similarity DESC
            LIMIT %s
            """,
            (query_embedding, query_embedding, similarity_threshold, top_k),
        )

        return [
            {
                "id": row[0],
                "text": row[1],
                "metadata": row[2],
                "similarity": row[3],
            }
            for row in rows
        ]

    def delete_embedding(self, doc_id: int) -> None:
        """
        Deletes an embedding and its metadata from the database.

        Args:
            doc_id (int): The ID of the document to delete.

        Raises:
            Exception: If deletion fails.
        """
        self.db.execute_write("DELETE FROM documents WHERE id = %s", (doc_id,))
