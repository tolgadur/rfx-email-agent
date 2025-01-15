import pytest
from unittest.mock import MagicMock
from app.rag_service import RAGService
from app.data_types import RAGResponse, DocumentMatch
from app.models import Document


@pytest.fixture
def mock_document():
    """Create a mock document."""
    doc = Document(id=1, filepath="test.txt", processed=True)
    return doc


@pytest.fixture
def mock_embeddings_dao():
    """Create a mock embeddings DAO."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_litellm(monkeypatch):
    """Mock litellm.completion."""
    mock = MagicMock()
    mock.return_value.choices = [MagicMock(message=MagicMock(content="Test response"))]
    monkeypatch.setattr("litellm.completion", mock)
    return mock


@pytest.fixture
def rag_service(mock_embeddings_dao):
    """Create a RAGService instance with a mock embeddings DAO."""
    return RAGService(embeddings_dao=mock_embeddings_dao)


def test_initialization(rag_service, mock_embeddings_dao):
    """Test RAGService initialization."""
    assert rag_service.embeddings_dao == mock_embeddings_dao


def test_send_message_no_relevant_docs(rag_service, mock_embeddings_dao, mock_litellm):
    """Test sending a message with no relevant documents."""
    # Setup mock with no relevant matches
    mock_embeddings_dao.query_embeddings.return_value = []

    # Test
    response = rag_service.send_message("test query")

    # Verify
    assert isinstance(response, RAGResponse)
    assert "I don't have enough relevant information" in response.text
    assert response.max_similarity is None
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_not_called()


def test_send_message_with_relevant_docs(
    rag_service, mock_embeddings_dao, mock_litellm, mock_document
):
    """Test sending a message with relevant documents."""
    # Setup mock with matches
    mock_embeddings_dao.query_embeddings.return_value = [
        DocumentMatch(
            text="Relevant doc",
            similarity=0.7,
            embedding_metadata={},
            document=mock_document,
        )
    ]

    # Test
    response = rag_service.send_message("test query")

    # Verify
    assert isinstance(response, RAGResponse)
    assert response.text == "Test response"
    assert response.max_similarity == 0.7
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_called_once()

    # Verify system message
    system_msg = mock_litellm.call_args[1]["messages"][0]["content"]
    assert "Please provide a clear and concise response" in system_msg
    assert "If the context isn't relevant" in system_msg

    # Verify user message with context and query
    user_msg = mock_litellm.call_args[1]["messages"][1]["content"]
    assert "Context:" in user_msg
    assert "Relevant doc" in user_msg
    assert "Question: test query" in user_msg


def test_send_message_multiple_relevant_docs(
    rag_service, mock_embeddings_dao, mock_litellm, mock_document
):
    """Test sending a message with multiple relevant documents."""
    # Setup mock with multiple matches
    mock_embeddings_dao.query_embeddings.return_value = [
        DocumentMatch(
            text="Doc 1",
            similarity=0.7,
            embedding_metadata={},
            document=mock_document,
        ),
        DocumentMatch(
            text="Doc 2",
            similarity=0.65,
            embedding_metadata={},
            document=mock_document,
        ),
    ]

    # Test
    response = rag_service.send_message("test query")

    # Verify
    assert isinstance(response, RAGResponse)
    assert response.text == "Test response"
    assert response.max_similarity == 0.7
    mock_embeddings_dao.query_embeddings.assert_called_once_with("test query")
    mock_litellm.assert_called_once()

    # Verify system message
    system_msg = mock_litellm.call_args[1]["messages"][0]["content"]
    assert "Please provide a clear and concise response" in system_msg
    assert "If the context isn't relevant" in system_msg

    # Verify user message with context and query
    user_msg = mock_litellm.call_args[1]["messages"][1]["content"]
    assert "Context:" in user_msg
    assert "Doc 1" in user_msg
    assert "Doc 2" in user_msg
    assert "Question: test query" in user_msg


def test_send_message_empty_query(rag_service, mock_embeddings_dao, mock_litellm):
    """Test sending an empty message."""
    # Setup mock with empty result
    mock_embeddings_dao.query_embeddings.return_value = []

    # Test
    response = rag_service.send_message("")

    # Verify
    assert isinstance(response, RAGResponse)
    assert response.max_similarity is None
    assert "I don't have enough relevant information" in response.text
    mock_embeddings_dao.query_embeddings.assert_called_once_with("")
    mock_litellm.assert_not_called()


def test_send_message_unrelated_content(
    rag_service, mock_embeddings_dao, mock_litellm, mock_document
):
    """Test that unrelated content returns low similarity scores."""
    # Setup mock with low similarity match
    mock_embeddings_dao.query_embeddings.return_value = [
        DocumentMatch(
            text=(
                "The process of photosynthesis in plants involves chlorophyll "
                "capturing sunlight."
            ),
            similarity=0.1,
            embedding_metadata={},
            document=mock_document,
        )
    ]

    # Test with unrelated query
    response = rag_service.send_message("What is the capital of France?")

    # Verify
    assert isinstance(response, RAGResponse)
    assert response.text == "Test response"
    assert response.max_similarity == 0.1
    mock_embeddings_dao.query_embeddings.assert_called_once()
    mock_litellm.assert_called_once()
