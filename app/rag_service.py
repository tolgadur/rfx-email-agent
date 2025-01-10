import os
import litellm
from dataclasses import dataclass
from typing import Optional
from app.embeddings_dao import EmbeddingsDAO
from app.config import MAX_TOKENS, SIMILARITY_THRESHOLD


@dataclass
class RAGResponse:
    text: str
    max_similarity: Optional[float] = None


class RAGService:
    """Service for RAG (Retrieval Augmented Generation) operations."""

    def __init__(self, embeddings_dao: EmbeddingsDAO):
        """Initialize the RAG service.

        Args:
            embeddings_dao: DAO for similarity search
        """
        self.embeddings_dao = embeddings_dao

    def send_message(self, message: str) -> RAGResponse:
        """Process a message using RAG.

        Args:
            message: The user's message/query

        Returns:
            RAGResponse containing the response text and similarity score
        """
        # Search for similar documents
        matches = self.embeddings_dao.query_embeddings(message)

        # Get highest similarity score from all matches
        max_similarity = max(match.similarity for match in matches) if matches else None

        # Filter matches by similarity threshold for context
        relevant_docs = [
            match for match in matches if match.similarity >= SIMILARITY_THRESHOLD
        ]

        # If no relevant docs found, return early
        if not relevant_docs:
            return RAGResponse(
                text="I apologize, but I don't have enough relevant information to "
                "provide a reliable answer to your question. Could you please "
                "rephrase your question or provide more context?",
                max_similarity=max_similarity,
            )

        # Construct context from relevant documents
        context = "\n\n".join(match.text for match in relevant_docs)
        prompt = (
            "Please provide a clear and concise response under 300 characters. "
            "Be thorough but avoid unnecessary details.\n\n"
            "Use the following context to help answer the question. "
            "If the context isn't relevant, you can ignore it and answer "
            "based on your general knowledge.\n\n"
            f"Context:\n{context}\n\nQuestion: {message}"
        )

        return RAGResponse(
            text=self._generate_response(prompt),
            max_similarity=max_similarity,
        )

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
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content
