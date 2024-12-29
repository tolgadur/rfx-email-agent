from pinecone import Pinecone
from pinecone_plugins.assistant.models.chat import Message


class PineconeHandler:
    """Handles interactions with Pinecone's AI assistant."""

    def __init__(self, api_key: str):
        """Initialize the Pinecone handler with API key and assistant.

        Args:
            api_key: Pinecone API key for authentication
        """
        self.pc = Pinecone(api_key=api_key, environment="gcp-starter")
        try:
            self.assistant = self.pc.assistant.Assistant(
                assistant_name="email-assistant"
            )
            print(f"Assistant initialized successfully: {self.assistant}")
        except Exception as e:
            print(f"Error initializing assistant: {e}")
            raise

    def send_message(self, message: str) -> str:
        """Send a message to the Pinecone assistant and get the response.

        Args:
            message: The message to send to the assistant.

        Returns:
            The assistant's response as a string. Empty string if there's an error.
        """
        if not message or message.strip() in ["", "\r\n"]:
            return ""

        try:
            msg = Message(role="user", content=message)
            response = self.assistant.chat(messages=[msg])
            return response.message.content

        except Exception as e:
            print(f"Error sending message: {e}")
            return ""
