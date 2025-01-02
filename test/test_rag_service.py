import pytest
from unittest.mock import MagicMock, Mock, ANY
from app.rag_service import RAGService
from app.embeddings_dao import DocumentMatch
from app.config import MAX_TOKENS


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
    """Test sending a message with no relevant documents but above min similarity."""
    # Setup mock with score above MIN_SIMILARITY_TO_ANSWER but below threshold
    mock_embeddings_dao.query_embeddings.return_value = [
        DocumentMatch(text="Test doc", similarity=0.5, document_metadata={})
    ]

    # Test
    response, similarity = rag_service.send_message("test query")

    # Verify
    assert response == "Test response"
    assert similarity == 0.5  # Should return the highest similarity score
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_called_once()
    call_args = mock_litellm.call_args[1]
    assert call_args["model"] == "gpt-4-turbo"
    assert call_args["api_key"] == ANY
    assert call_args["max_tokens"] == MAX_TOKENS
    prompt = call_args["messages"][0]["content"]
    assert "Please provide a clear and concise response" in prompt
    assert "Question: test query" in prompt
    assert "Context:" not in prompt


def test_send_message_with_relevant_docs(
    rag_service, mock_embeddings_dao, mock_litellm
):
    """Test sending a message with relevant documents."""
    # Setup mock
    mock_embeddings_dao.query_embeddings.return_value = [
        DocumentMatch(text="Relevant doc", similarity=0.9, document_metadata={})
    ]

    # Test
    response, similarity = rag_service.send_message("test query")

    # Verify
    assert response == "Test response"
    assert similarity == 0.9  # Highest similarity score
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_called_once()
    prompt = mock_litellm.call_args[1]["messages"][0]["content"]
    assert "Please provide a clear and concise response" in prompt
    assert "Context:" in prompt
    assert "Relevant doc" in prompt
    assert "Question: test query" in prompt


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
    response, similarity = rag_service.send_message("test query")

    # Verify
    assert response == "Test response"
    assert similarity == 0.9  # Should be the highest similarity score
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_called_once()
    prompt = mock_litellm.call_args[1]["messages"][0]["content"]
    assert "Please provide a clear and concise response" in prompt
    assert "Context:" in prompt
    assert "Doc 1" in prompt
    assert "Doc 2" in prompt
    assert "Question: test query" in prompt


def test_send_message_custom_threshold(mock_embeddings_dao, mock_litellm):
    """Test sending a message with a custom similarity threshold."""
    # Create service with custom threshold
    service = RAGService(embeddings_dao=mock_embeddings_dao, similarity_threshold=0.7)

    # Setup mock
    mock_embeddings_dao.query_embeddings.return_value = [
        DocumentMatch(text="Doc 1", similarity=0.75, document_metadata={}),
    ]

    # Test
    response, similarity = service.send_message("test query")

    # Verify
    assert response == "Test response"
    assert similarity == 0.75  # Should be the similarity of the relevant doc
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_called_once()
    prompt = mock_litellm.call_args[1]["messages"][0]["content"]
    assert "Please provide a clear and concise response" in prompt
    assert "Context:" in prompt
    assert "Doc 1" in prompt
    assert "Question: test query" in prompt


def test_send_message_empty_query(rag_service, mock_embeddings_dao, mock_litellm):
    """Test sending an empty message."""
    # Setup mock with empty result
    mock_embeddings_dao.query_embeddings.return_value = []

    # Test
    response, similarity = rag_service.send_message("")

    # Verify
    assert similarity is None  # No matches at all
    assert "don't have enough relevant information" in response
    mock_embeddings_dao.query_embeddings.assert_called_once_with("")
    mock_litellm.assert_not_called()  # Should not generate response when no matches


def test_send_message_below_min_similarity(
    rag_service, mock_embeddings_dao, mock_litellm
):
    """Test sending a message where best match is below minimum similarity threshold."""
    # Setup mock with a low similarity match
    mock_embeddings_dao.query_embeddings.return_value = [
        DocumentMatch(text="Test doc", similarity=0.2, document_metadata={})
    ]

    # Test
    response, similarity = rag_service.send_message("test query")

    # Verify
    assert similarity == 0.2  # Should still return the similarity score
    assert "don't have enough relevant information" in response
    assert "rephrase your question" in response
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_not_called()  # Should not generate response


def test_send_message_no_matches(rag_service, mock_embeddings_dao, mock_litellm):
    """Test sending a message with no matches at all."""
    # Setup mock with no matches
    mock_embeddings_dao.query_embeddings.return_value = []

    # Test
    response, similarity = rag_service.send_message("test query")

    # Verify
    assert similarity is None
    assert "don't have enough relevant information" in response
    assert "rephrase your question" in response
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_not_called()  # Should not generate response
