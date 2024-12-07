from pinecone import Pinecone
from pinecone_plugins.assistant.models.chat import Message
from config import PINECONE_API_KEY

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY, environment="gcp-starter")

# Initialize assistant globally
try:
    ASSISTANT = pc.assistant.Assistant(assistant_name="email-assistant")
    print(f"Assistant initialized successfully: {ASSISTANT}")
except Exception as e:
    print(f"Error initializing assistant: {e}")
    raise


def send_message_to_assistant(message: str) -> str:
    try:
        msg = Message(role="user", content=message)
        response = ASSISTANT.chat(messages=[msg])

        response_content = response.message.content
        similarity_scores = [citation.position for citation in response.citations]
        citations = [
            citation.references[0].file.name for citation in response.citations
        ]

        formatted_response = (
            f"{response_content}\n"
            f"-----------------------------------\n"
            f"Similarity Scores: {similarity_scores}\n"
            f"Citations: {citations}"
        )
        return formatted_response

    except AttributeError as e:
        print(f"Assistant method not found: {e}")
        raise

    except Exception as e:
        print(f"Error sending message: {e}")
        raise
