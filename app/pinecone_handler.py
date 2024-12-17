from pinecone import Pinecone
from pinecone_plugins.assistant.models.chat import Message
from config import PINECONE_API_KEY

pc = Pinecone(api_key=PINECONE_API_KEY, environment="gcp-starter")

try:
    ASSISTANT = pc.assistant.Assistant(assistant_name="email-assistant")
    print(f"Assistant initialized successfully: {ASSISTANT}")
except Exception as e:
    print(f"Error initializing assistant: {e}")
    raise


def send_message_to_assistant(message: str):
    if not message or message.strip() in ["", "\r\n"]:
        return ""

    try:
        msg = Message(role="user", content=message)
        response = ASSISTANT.chat(messages=[msg])
        return response.message.content

    except Exception as e:
        print(f"Error sending message: {e}")
        return ""
