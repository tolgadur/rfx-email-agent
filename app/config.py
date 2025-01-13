import os
from pathlib import Path

# Base paths
ROOT_DIR = Path(__file__).parent.parent
ASSETS_DIR = ROOT_DIR / "assets"

# Email settings
EMAIL = os.environ["EMAIL"]
PASSWORD = os.environ["PASSWORD"]
IMAP_SERVER = os.environ.get("IMAP_SERVER", "imap.gmail.com")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")

# Database settings
DATABASE_URL = os.environ.get("DATABASE_URL")

# RAG settings
# Minimum similarity threshold for both answering questions and including context
SIMILARITY_THRESHOLD = float(os.environ.get("SIMILARITY_THRESHOLD", "0.4"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 300))

# Document processor settings
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", 100))

# Embedding model
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-large")

# Model name
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4-turbo")
