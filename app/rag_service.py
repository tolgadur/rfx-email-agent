import litellm
from app.config import MAX_TOKENS, MODEL_NAME
from app.embeddings_dao import EmbeddingsDAO
from app.data_types import RAGResponse


class RAGService:
    """Service for retrieving answers using RAG (Retrieval Augmented Generation)."""

    def __init__(self, embeddings_dao: EmbeddingsDAO):
        """Initialize the RAG service.

        Args:
            embeddings_dao: Data access object for embeddings
        """
        self.embeddings_dao = embeddings_dao

    def send_message(self, message: str) -> RAGResponse:
        """Send a message and get a response using RAG.

        Args:
            message: The message to process

        Returns:
            RAGResponse containing the response text and metadata
        """
        matches = self.embeddings_dao.query_embeddings(message)

        if not matches:
            no_match_msg = (
                "I don't have enough relevant information to answer your question. "
                "Could you please rephrase your question or ask about something else?"
            )
            return RAGResponse(text=no_match_msg, max_similarity=None)

        # Get the best match in a single pass
        best_match = max(matches, key=lambda x: x.similarity)

        # Build context from relevant documents
        context = "\n\n".join(match.text for match in matches)

        # Generate response using LLM
        messages = [
            {
                "role": "system",
                "content": (
                    "Please provide a clear and concise response based on the "
                    "following context under 300 characters."
                    "If the context isn't relevant, you can ignore it and answer "
                    "based on your general knowledge."
                ),
            },
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {message}"},
        ]

        return RAGResponse(
            text=self._generate_response(messages),
            max_similarity=best_match.similarity,
            document_url=best_match.document.url,
        )

    def _generate_response(self, messages: list) -> str:
        """Generate a response using the language model.

        Args:
            messages: The messages to send to the model

        Returns:
            The generated response
        """
        response = litellm.completion(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content
