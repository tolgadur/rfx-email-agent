# Note: These tests use SQLite which doesn't support vector operations.
# Vector similarity search won't actually work in these tests,
# we're just testing the basic CRUD operations and API interactions.
import pytest
from unittest.mock import patch
from app.embeddings_dao import EmbeddingsDAO
from app.models import Document, Base, Embedding
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
    # Create a mock embedding vector with 3072 dimensions
    embedding_vector = [0.1] * 3072
    return {"data": [{"embedding": embedding_vector}]}


def test_add_text(embeddings_dao, mock_embedding):
    """Test adding text to the vector store."""
    embeddings_dao.db_handler.setup_database()

    # Create a test document
    with embeddings_dao.db_handler.get_session() as session:
        doc = Document(filepath="test.txt", processed=True)
        session.add(doc)
        session.commit()
        doc_id = doc.id

    with patch("app.embeddings_dao.embedding", return_value=mock_embedding):
        embeddings_dao.add_text(
            "Test document", document_id=doc_id, embedding_metadata={"type": "test"}
        )

    # Verify embedding was added
    with embeddings_dao.db_handler.get_session() as session:
        embedding = session.query(Embedding).first()
        assert embedding.text == "Test document"
        assert len(embedding.embedding) == 3072
        assert embedding.embedding_metadata == {"type": "test"}
        assert embedding.document_id == doc_id


def test_delete_embedding(embeddings_dao, mock_embedding):
    """Test deleting documents by text."""
    embeddings_dao.db_handler.setup_database()

    # Create a test document
    with embeddings_dao.db_handler.get_session() as session:
        doc = Document(filepath="test.txt", processed=True)
        session.add(doc)
        session.commit()
        doc_id = doc.id

    # Add a test document
    with patch("app.embeddings_dao.embedding", return_value=mock_embedding):
        embeddings_dao.add_text(
            "Test document to delete", document_id=doc_id, embedding_metadata={}
        )

    # Delete the document
    embeddings_dao.delete_embedding("Test document to delete")

    # Verify document was deleted
    with embeddings_dao.db_handler.get_session() as session:
        assert session.query(Embedding).count() == 0


def test_generate_embedding(embeddings_dao, mock_embedding):
    """Test embedding generation."""
    with patch("app.embeddings_dao.embedding", return_value=mock_embedding) as mock:
        embedding = embeddings_dao._generate_embedding("test text")

        assert len(embedding) == 3072
        mock.assert_called_once_with(
            model="text-embedding-3-large", input=["test text"]
        )
