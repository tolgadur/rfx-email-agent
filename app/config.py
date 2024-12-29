import os
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    email: str
    password: str
    database_url: str
    pinecone_api_key: str
    imap_server: str
    smtp_server: str

    @classmethod
    def from_env(self) -> "Config":
        """Create config from environment variables."""
        return self(
            email=os.environ["EMAIL"],
            password=os.environ["PASSWORD"],
            database_url=os.environ["DATABASE_URL"],
            pinecone_api_key=os.environ["PINECONE_API_KEY"],
            imap_server=os.environ.get("IMAP_SERVER", "imap.gmail.com"),
            smtp_server=os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
        )
