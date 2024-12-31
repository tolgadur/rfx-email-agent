# Note: These tests use SQLite which doesn't support vector operations.
# Vector similarity search won't actually work in these tests,
# we're just testing the basic CRUD operations and API interactions.
import pytest
from unittest.mock import patch
from app.embeddings_dao import EmbeddingsDAO, DocumentMatch
from app.models import Document, Base
from app.db_handler import DatabaseHandler


@pytest.fixture
def db_handler():
    """Create a test database handler."""
    handler = DatabaseHandler("sqlite:///:memory:")
    # Override setup to skip PostgreSQL-specific operations
    handler.setup_database = lambda seed=True: (
        Base.metadata.create_all(bind=handler.engine),
        handler.seed_database() if seed else None,
    )[0]
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
    embeddings_dao.db_handler.setup_database(seed=False)

    with patch("app.embeddings_dao.embedding", return_value=mock_embedding):
        embeddings_dao.add_text("Test document", document_metadata={"type": "test"})

    # Verify document was added
    with embeddings_dao.db_handler.get_session() as session:
        doc = session.query(Document).first()
        assert doc.text == "Test document"
        assert len(doc.embedding) == 1536
        assert doc.document_metadata == {"type": "test"}


@pytest.mark.skip(reason="Vector similarity search not supported in SQLite")
def test_query_embeddings(embeddings_dao, mock_embedding):
    """Test querying similar documents."""
    embeddings_dao.db_handler.setup_database(seed=True)  # Add seed data

    with patch("app.embeddings_dao.embedding", return_value=mock_embedding):
        results = embeddings_dao.query_embeddings("pasta recipe", limit=2)

    assert len(results) > 0
    assert isinstance(results[0], DocumentMatch)
    assert results[0].text == "How to make a delicious pasta carbonara"
    assert isinstance(results[0].similarity, float)
    assert results[0].document_metadata == {
        "type": "recipe",
        "cuisine": "italian",
        "difficulty": "medium",
    }


def test_delete_embedding(embeddings_dao, mock_embedding):
    """Test deleting documents by text."""
    embeddings_dao.db_handler.setup_database(seed=True)

    # Delete the seed document
    embeddings_dao.delete_embedding("How to make a delicious pasta carbonara")

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
            model="text-embedding-ada-002", input=["test text"]
        )
