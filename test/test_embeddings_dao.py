# Note: These tests use SQLite which doesn't support vector operations.
# Vector similarity search won't actually work in these tests,
# we're just testing the basic CRUD operations and API interactions.
import pytest
from unittest.mock import patch
from app.embeddings_dao import EmbeddingsDAO
from app.models import Document, Base
from app.db_handler import DatabaseHandler


@pytest.fixture
def db_handler():
    """Create a test database handler."""
    handler = DatabaseHandler("sqlite:///:memory:")
    # Override setup to skip PostgreSQL-specific operations
    handler.setup_database = lambda: Base.metadata.create_all(bind=handler.engine)
    return handler


@pytest.fixture
def embeddings_dao(db_handler):
    """Create a test embeddings DAO."""
    return EmbeddingsDAO(db_handler=db_handler)


@pytest.fixture
def mock_embedding():
    """Create a mock embedding response."""
    return {"data": [{"embedding": [0.1] * 1536}]}


def test_add_text(embeddings_dao, mock_embedding):
    """Test adding text to the vector store."""
    embeddings_dao.db_handler.setup_database()

    with patch("app.embeddings_dao.embedding", return_value=mock_embedding):
        embeddings_dao.add_text("Test document", document_metadata={"type": "test"})

    # Verify document was added
    with embeddings_dao.db_handler.get_session() as session:
        doc = session.query(Document).first()
        assert doc.text == "Test document"
        assert len(doc.embedding) == 1536
        assert doc.document_metadata == {"type": "test"}


def test_delete_embedding(embeddings_dao, mock_embedding):
    """Test deleting documents by text."""
    embeddings_dao.db_handler.setup_database()

    # Add a test document
    with patch("app.embeddings_dao.embedding", return_value=mock_embedding):
        embeddings_dao.add_text("Test document to delete")

    # Delete the document
    embeddings_dao.delete_embedding("Test document to delete")

    # Verify deletion
    with embeddings_dao.db_handler.get_session() as session:
        doc = session.query(Document).first()
        assert doc is None


def test_generate_embedding(embeddings_dao, mock_embedding):
    """Test embedding generation."""
    with patch("app.embeddings_dao.embedding", return_value=mock_embedding) as mock:
        embedding = embeddings_dao._generate_embedding("test text")

        assert len(embedding) == 1536
        mock.assert_called_once_with(
            model="text-embedding-3-small", input=["test text"]
        )
