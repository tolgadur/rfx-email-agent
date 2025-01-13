"""Common test fixtures and configuration."""

import os
import pytest
from dotenv import load_dotenv
from sqlalchemy.sql import text
from app.db_handler import DatabaseHandler

# Load environment variables from .env file
load_dotenv()

# Skip all tests in this directory if TEST_DATABASE_URL is not set
pytestmark = pytest.mark.skipif(
    os.environ.get("TEST_DATABASE_URL") is None, reason="TEST_DATABASE_URL not set"
)


@pytest.fixture
def db_handler():
    """Create a database handler using real PostgreSQL."""
    handler = DatabaseHandler(os.environ["TEST_DATABASE_URL"])

    with handler.get_session() as session:
        session.execute(text("DROP TABLE IF EXISTS embeddings CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS documents CASCADE"))
        session.commit()

    handler.setup_database()
    return handler
