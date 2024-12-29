import pytest
from unittest.mock import MagicMock, Mock, ANY
from app.rag_service import RAGService
from app.vector_store import DocumentMatch


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
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
def rag_service(mock_vector_store):
    """Create a RAGService instance with a mock vector store."""
    return RAGService(vector_store=mock_vector_store)


def test_initialization(rag_service, mock_vector_store):
    """Test RAGService initialization."""
    assert rag_service.vector_store == mock_vector_store
    assert rag_service.similarity_threshold == 0.8


def test_send_message_no_relevant_docs(rag_service, mock_vector_store, mock_litellm):
    """Test sending a message with no relevant documents."""
    # Setup mock
    mock_vector_store.query_embeddings.return_value = [
        DocumentMatch(text="Test doc", similarity=0.5, metadata={})
    ]

    # Test
    response = rag_service.send_message("test query")

    # Verify
    assert response == "Test response"
    mock_vector_store.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_called_once_with(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": "test query"}],
        api_key=ANY,
    )


def test_send_message_with_relevant_docs(rag_service, mock_vector_store, mock_litellm):
    """Test sending a message with relevant documents."""
    # Setup mock
    mock_vector_store.query_embeddings.return_value = [
        DocumentMatch(text="Relevant doc", similarity=0.9, metadata={})
    ]

    # Test
    response = rag_service.send_message("test query")

    # Verify
    assert response == "Test response"
    mock_vector_store.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_called_once()
    # Verify the prompt includes the context
    assert "Relevant doc" in mock_litellm.call_args[1]["messages"][0]["content"]


def test_send_message_multiple_relevant_docs(
    rag_service, mock_vector_store, mock_litellm
):
    """Test sending a message with multiple relevant documents."""
    # Setup mock
    mock_vector_store.query_embeddings.return_value = [
        DocumentMatch(text="Doc 1", similarity=0.9, metadata={}),
        DocumentMatch(text="Doc 2", similarity=0.85, metadata={}),
    ]

    # Test
    response = rag_service.send_message("test query")

    # Verify
    assert response == "Test response"
    mock_vector_store.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_called_once()
    # Verify both documents are included in the context
    prompt = mock_litellm.call_args[1]["messages"][0]["content"]
    assert "Doc 1" in prompt
    assert "Doc 2" in prompt


def test_send_message_custom_threshold(mock_vector_store, mock_litellm):
    """Test sending a message with a custom similarity threshold."""
    # Create service with custom threshold
    service = RAGService(vector_store=mock_vector_store, similarity_threshold=0.7)

    # Setup mock
    mock_vector_store.query_embeddings.return_value = [
        DocumentMatch(text="Doc 1", similarity=0.75, metadata={}),
    ]

    # Test
    response = service.send_message("test query")

    # Verify
    assert response == "Test response"
    mock_vector_store.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_called_once()
    assert "Doc 1" in mock_litellm.call_args[1]["messages"][0]["content"]


def test_send_message_empty_query(rag_service, mock_vector_store, mock_litellm):
    """Test sending an empty message."""
    # Test
    response = rag_service.send_message("")

    # Verify
    assert response == "Test response"
    mock_vector_store.query_embeddings.assert_called_once_with("")
    mock_litellm.assert_called_once_with(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": ""}],
        api_key=ANY,
    )
