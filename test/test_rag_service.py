import pytest
from unittest.mock import MagicMock, Mock
from app.rag_service import RAGService, RAGResponse
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
def rag_service(mock_embeddings_dao, monkeypatch):
    """Create a RAGService instance with a mock embeddings DAO."""
    # Mock the config threshold to match original test behavior
    monkeypatch.setattr("app.rag_service.SIMILARITY_THRESHOLD", 0.6)
    return RAGService(embeddings_dao=mock_embeddings_dao)


def test_initialization(rag_service, mock_embeddings_dao):
    """Test RAGService initialization."""
    assert rag_service.embeddings_dao == mock_embeddings_dao


def test_send_message_no_relevant_docs(rag_service, mock_embeddings_dao, mock_litellm):
    """Test sending a message with no relevant documents but above min similarity."""
    # Setup mock with score above MIN_SIMILARITY_TO_ANSWER but below threshold
    mock_embeddings_dao.query_embeddings.return_value = [
        DocumentMatch(text="Test doc", similarity=0.4, document_metadata={})
    ]

    # Test
    response = rag_service.send_message("test query")

    # Verify
    assert isinstance(response, RAGResponse)
    assert "don't have enough relevant information" in response.text
    assert response.max_similarity == 0.4  # Should return the highest similarity score
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_not_called()  # Should not generate response when no relevant docs


def test_send_message_with_relevant_docs(
    rag_service, mock_embeddings_dao, mock_litellm
):
    """Test sending a message with relevant documents."""
    # Setup mock
    mock_embeddings_dao.query_embeddings.return_value = [
        DocumentMatch(text="Relevant doc", similarity=0.7, document_metadata={})
    ]

    # Test
    response = rag_service.send_message("test query")

    # Verify
    assert isinstance(response, RAGResponse)
    assert response.text == "Test response"
    assert response.max_similarity == 0.7  # Highest similarity score
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
        DocumentMatch(text="Doc 1", similarity=0.7, document_metadata={}),
        DocumentMatch(text="Doc 2", similarity=0.65, document_metadata={}),
    ]

    # Test
    response = rag_service.send_message("test query")

    # Verify
    assert isinstance(response, RAGResponse)
    assert response.text == "Test response"
    assert response.max_similarity == 0.7  # Should be the highest similarity score
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_called_once()
    prompt = mock_litellm.call_args[1]["messages"][0]["content"]
    assert "Please provide a clear and concise response" in prompt
    assert "Context:" in prompt
    assert "Doc 1" in prompt
    assert "Doc 2" in prompt
    assert "Question: test query" in prompt


def test_send_message_empty_query(rag_service, mock_embeddings_dao, mock_litellm):
    """Test sending an empty message."""
    # Setup mock with empty result
    mock_embeddings_dao.query_embeddings.return_value = []

    # Test
    response = rag_service.send_message("")

    # Verify
    assert isinstance(response, RAGResponse)
    assert response.max_similarity is None  # No matches at all
    assert "don't have enough relevant information" in response.text
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
    response = rag_service.send_message("test query")

    # Verify
    assert isinstance(response, RAGResponse)
    assert response.max_similarity == 0.2  # Should still return the similarity score
    assert "don't have enough relevant information" in response.text
    assert "rephrase your question" in response.text
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_not_called()  # Should not generate response


def test_send_message_no_matches(rag_service, mock_embeddings_dao, mock_litellm):
    """Test sending a message with no matches at all."""
    # Setup mock with no matches
    mock_embeddings_dao.query_embeddings.return_value = []

    # Test
    response = rag_service.send_message("test query")

    # Verify
    assert isinstance(response, RAGResponse)
    assert response.max_similarity is None
    assert "don't have enough relevant information" in response.text
    assert "rephrase your question" in response.text
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_not_called()  # Should not generate response


def test_send_message_unrelated_content(rag_service, mock_embeddings_dao, mock_litellm):
    """Test that unrelated content returns low similarity scores."""
    # Setup mock with completely unrelated document
    mock_embeddings_dao.query_embeddings.return_value = [
        DocumentMatch(
            text=(
                "The process of photosynthesis in plants involves chlorophyll "
                "capturing sunlight."
            ),
            similarity=0.1,  # Should be low similarity
            document_metadata={},
        )
    ]

    # Test with unrelated query
    response = rag_service.send_message("What is the capital of France?")

    # Verify
    assert isinstance(response, RAGResponse)
    assert "don't have enough relevant information" in response.text
    assert response.max_similarity == 0.1  # Should maintain the low similarity score
    mock_embeddings_dao.query_embeddings.assert_called_once()
    mock_litellm.assert_not_called()  # Should not generate response for low similarity


def test_send_message_custom_threshold(mock_embeddings_dao, mock_litellm, monkeypatch):
    """Test sending a message with a custom similarity threshold."""
    # Mock the config threshold
    monkeypatch.setattr("app.rag_service.SIMILARITY_THRESHOLD", 0.5)
    service = RAGService(embeddings_dao=mock_embeddings_dao)

    # Setup mock
    mock_embeddings_dao.query_embeddings.return_value = [
        DocumentMatch(text="Doc 1", similarity=0.55, document_metadata={}),
    ]

    # Test
    response = service.send_message("test query")

    # Verify
    assert isinstance(response, RAGResponse)
    assert response.text == "Test response"
    assert (
        response.max_similarity == 0.55
    )  # Should be the similarity of the relevant doc
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_called_once()
    prompt = mock_litellm.call_args[1]["messages"][0]["content"]
    assert "Please provide a clear and concise response" in prompt
    assert "Context:" in prompt
    assert "Doc 1" in prompt
    assert "Question: test query" in prompt
