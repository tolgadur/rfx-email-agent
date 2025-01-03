# Note: These tests use SQLite which doesn't support vector operations.
# Vector similarity search won't actually work in these tests,
# we're just testing the basic CRUD operations and API interactions.
import pytest
from unittest.mock import patch
from app.embeddings_dao import EmbeddingsDAO
from app.models import Document, ProcessedDocument, Base
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


@pytest.fixture
def processed_document_id(embeddings_dao):
    """Create a test processed document and return its ID."""
    embeddings_dao.db_handler.setup_database()
    with embeddings_dao.db_handler.get_session() as session:
        doc = ProcessedDocument(filepath="test/file.txt")
        session.add(doc)
        session.commit()
        return doc.id


def test_add_text(embeddings_dao, mock_embedding, processed_document_id):
    """Test adding text to the vector store."""
    with patch("app.embeddings_dao.embedding", return_value=mock_embedding):
        embeddings_dao.add_text(
            "Test document",
            document_metadata={
                "type": "test",
                "processed_document_id": processed_document_id,
            },
        )

    # Verify document was added
    with embeddings_dao.db_handler.get_session() as session:
        doc = session.query(Document).first()
        assert doc.text == "Test document"
        assert len(doc.embedding) == 1536
        assert doc.document_metadata == {
            "type": "test",
        }
        assert doc.processed_document_id == processed_document_id


def test_delete_embedding(embeddings_dao, mock_embedding, processed_document_id):
    """Test deleting documents by text."""
    # Add a test document
    with patch("app.embeddings_dao.embedding", return_value=mock_embedding):
        embeddings_dao.add_text(
            "Test document to delete",
            document_metadata={"processed_document_id": processed_document_id},
        )

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
            model="text-embedding-ada-002", input=["test text"]
        )
