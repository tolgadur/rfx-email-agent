import os
import litellm
from app.embeddings_dao import EmbeddingsDAO


class RAGService:
    """Service for RAG (Retrieval Augmented Generation) operations."""

    def __init__(
        self, embeddings_dao: EmbeddingsDAO, similarity_threshold: float = 0.8
    ):
        """Initialize the RAG service.

        Args:
            embeddings_dao: DAO for similarity search
            similarity_threshold: Minimum similarity score (0-1) for relevant documents
        """
        self.embeddings_dao = embeddings_dao
        self.similarity_threshold = similarity_threshold

    def send_message(self, message: str) -> str:
        """Process a message using RAG.

        Args:
            message: The user's message/query

        Returns:
            The generated response
        """
        # Search for similar documents
        matches = self.embeddings_dao.query_embeddings(message)

        # Filter matches by similarity threshold
        relevant_docs = [
            match for match in matches if match.similarity >= self.similarity_threshold
        ]

        if not relevant_docs:
            # No relevant context found, use base prompt
            return self._generate_response(message)

        # Construct context from relevant documents
        context = "\n\n".join(match.text for match in relevant_docs)

        # Construct prompt with context
        prompt = (
            "Use the following context to help answer the question. "
            "If the context isn't relevant, you can ignore it and answer "
            "based on your general knowledge.\n\n"
            f"Context:\n{context}\n\nQuestion: {message}"
        )

        return self._generate_response(prompt)

    def _generate_response(self, prompt: str) -> str:
        """Generate a response using the language model.

        Args:
            prompt: The prompt to send to the model

        Returns:
            The generated response
        """
        response = litellm.completion(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        return response.choices[0].message.content
