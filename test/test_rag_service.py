import pytest
from unittest.mock import MagicMock, Mock, ANY
from app.rag_service import RAGService
from app.embeddings_dao import DocumentMatch


@pytest.fixture
def mock_embeddings_dao():
    """Create a mock embeddings DAO."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_litellm(monkeypatch):
    """Mock litellm.completion."""
    mock = MagicMock()
    mock.return_value.choices = [Mock(message=Mock(content="Test response"))]
    monkeypatch.setattr("litellm.completion", mock)
    return mock


@pytest.fixture
def rag_service(mock_embeddings_dao):
    """Create a RAGService instance with a mock embeddings DAO."""
    return RAGService(embeddings_dao=mock_embeddings_dao)


def test_initialization(rag_service, mock_embeddings_dao):
    """Test RAGService initialization."""
    assert rag_service.embeddings_dao == mock_embeddings_dao
    assert rag_service.similarity_threshold == 0.8


def test_send_message_no_relevant_docs(rag_service, mock_embeddings_dao, mock_litellm):
    """Test sending a message with no relevant documents."""
    # Setup mock
    mock_embeddings_dao.query_embeddings.return_value = [
        DocumentMatch(text="Test doc", similarity=0.5, document_metadata={})
    ]

    # Test
    response = rag_service.send_message("test query")

    # Verify
    assert response == "Test response"
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_called_once_with(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": "test query"}],
        api_key=ANY,
    )


def test_send_message_with_relevant_docs(
    rag_service, mock_embeddings_dao, mock_litellm
):
    """Test sending a message with relevant documents."""
    # Setup mock
    mock_embeddings_dao.query_embeddings.return_value = [
        DocumentMatch(text="Relevant doc", similarity=0.9, document_metadata={})
    ]

    # Test
    response = rag_service.send_message("test query")

    # Verify
    assert response == "Test response"
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_called_once()
    # Verify the prompt includes the context
    assert "Relevant doc" in mock_litellm.call_args[1]["messages"][0]["content"]


def test_send_message_multiple_relevant_docs(
    rag_service, mock_embeddings_dao, mock_litellm
):
    """Test sending a message with multiple relevant documents."""
    # Setup mock
    mock_embeddings_dao.query_embeddings.return_value = [
        DocumentMatch(text="Doc 1", similarity=0.9, document_metadata={}),
        DocumentMatch(text="Doc 2", similarity=0.85, document_metadata={}),
    ]

    # Test
    response = rag_service.send_message("test query")

    # Verify
    assert response == "Test response"
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_called_once()
    # Verify both documents are included in the context
    prompt = mock_litellm.call_args[1]["messages"][0]["content"]
    assert "Doc 1" in prompt
    assert "Doc 2" in prompt


def test_send_message_custom_threshold(mock_embeddings_dao, mock_litellm):
    """Test sending a message with a custom similarity threshold."""
    # Create service with custom threshold
    service = RAGService(embeddings_dao=mock_embeddings_dao, similarity_threshold=0.7)

    # Setup mock
    mock_embeddings_dao.query_embeddings.return_value = [
        DocumentMatch(text="Doc 1", similarity=0.75, document_metadata={}),
    ]

    # Test
    response = service.send_message("test query")

    # Verify
    assert response == "Test response"
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_called_once()
    assert "Doc 1" in mock_litellm.call_args[1]["messages"][0]["content"]


def test_send_message_empty_query(rag_service, mock_embeddings_dao, mock_litellm):
    """Test sending an empty message."""
    # Test
    response = rag_service.send_message("")

    # Verify
    assert response == "Test response"
    mock_embeddings_dao.query_embeddings.assert_called_once_with("")
    mock_litellm.assert_called_once_with(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": ""}],
        api_key=ANY,
    )
