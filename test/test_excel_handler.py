import pytest
import io
import pandas as pd
from email.message import Message
from unittest.mock import patch, MagicMock
from app.excel_handler import ExcelHandler
from app.rag_service import RAGResponse


@pytest.fixture
def excel_handler():
    """Create an ExcelHandler instance for testing."""
    with patch("app.excel_handler.RAGService") as mock_rag_cls:
        mock_rag = mock_rag_cls.return_value
        handler = ExcelHandler(rag_service=mock_rag)
        # Store mock for easy access in tests
        handler.mock_rag = mock_rag
        yield handler


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("test.xlsx", True),
        ("test.xls", True),
        ("test.pdf", False),
        ("test.txt", False),
        ("", False),
    ],
)
def test_is_excel_file(excel_handler, filename, expected):
    """Test Excel file extension validation."""
    assert excel_handler._is_excel_file(filename) is expected


def test_create_skipped_file_entry(excel_handler):
    """Test creation of skipped file entries."""
    filename = "test.pdf"
    result = excel_handler._create_skipped_file_entry(filename)
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result[0] == filename
    assert "Unsupported file format" in result[1]


def test_create_concatenated_questions(excel_handler):
    """Test concatenation of DataFrame questions."""
    data = {
        "Q1": ["What is X?", "What is Y?"],
        "Q2": ["Where is X?", None],
        "Q3": [None, "When is Y?"],
    }
    df = pd.DataFrame(data)
    result = excel_handler._create_concatenated_questions(df)

    assert len(result) == 2
    assert "What is X?" in result[0]
    assert "Where is X?" in result[0]
    assert "What is Y?" in result[1]
    assert "When is Y?" in result[1]


def test_save_processed_dataframe(excel_handler):
    """Test saving DataFrame to bytes buffer."""
    data = {"Column1": [1, 2, 3], "Column2": ["A", "B", "C"]}
    df = pd.DataFrame(data)

    output = excel_handler._save_processed_dataframe(df)
    assert isinstance(output, io.BytesIO)

    # Verify the output can be read back as an Excel file
    result_df = pd.read_excel(output)
    assert result_df.shape == df.shape
    assert all(result_df.columns == df.columns)
    assert result_df.values.tolist() == df.values.tolist()


def test_process_attachment_excel(excel_handler):
    """Test processing Excel attachment."""
    part = MagicMock(spec=Message)
    part.get_payload.return_value = b"test content"

    excel_file, skipped = excel_handler._process_attachment(part, "test.xlsx")
    assert isinstance(excel_file, io.BytesIO)
    assert skipped is None


def test_process_attachment_non_excel(excel_handler):
    """Test processing non-Excel attachment."""
    part = MagicMock(spec=Message)

    excel_file, skipped = excel_handler._process_attachment(part, "test.pdf")
    assert excel_file is None
    assert isinstance(skipped, tuple)
    assert skipped[0] == "test.pdf"


def test_process_questions_empty_df(excel_handler):
    """Test processing empty DataFrame."""
    df = pd.DataFrame()
    result_df, message = excel_handler._process_questions(df)
    assert result_df is None
    assert message == "Excel file is empty"


def test_process_questions_with_data(excel_handler):
    """Test processing DataFrame with data."""
    excel_handler.mock_rag.send_message.return_value = RAGResponse("Test answer", 0.8)
    df = pd.DataFrame({"Q1": ["Test question"]})

    result_df, message = excel_handler._process_questions(df)
    assert isinstance(result_df, pd.DataFrame)
    assert "Answers" in result_df.columns
    assert "successfully" in message


def test_process_single_excel_file_invalid(excel_handler):
    """Test processing invalid Excel file."""
    excel_file = io.BytesIO(b"invalid content")
    output, message = excel_handler._process_single_excel_file(excel_file, "test.xlsx")
    assert output is None
    assert isinstance(message, str)


def test_get_answers_with_rag_response(excel_handler):
    """Test that _get_answers properly handles RAGResponse objects."""
    # Create a DataFrame with test questions
    questions = pd.Series(["Question 1", "Question 2"])

    # Mock the RAG service to return RAGResponse objects
    excel_handler.mock_rag.send_message.side_effect = [
        RAGResponse("Answer 1", 0.8),
        RAGResponse("Answer 2", 0.6),
    ]

    # Get answers and scores
    answers, scores = excel_handler._get_answers(questions)

    # Verify the results
    assert isinstance(answers, pd.Series)
    assert isinstance(scores, pd.Series)
    assert answers.tolist() == ["Answer 1", "Answer 2"]
    assert scores.tolist() == [0.8, 0.6]


def test_excel_with_similarity_scores(mocker):
    """Test that Excel processing includes similarity scores."""
    # Mock the config threshold
    mocker.patch("app.excel_handler.SIMILARITY_THRESHOLD", 0.5)

    # Mock RAG service to return known responses and scores
    mock_rag = mocker.Mock()
    mock_rag.send_message.side_effect = [
        RAGResponse("Answer 1", 0.85),  # High similarity - should keep answer
        RAGResponse("Answer 2", 0.25),  # Low similarity - should be replaced
        RAGResponse("Answer 3", None),  # No similarity
    ]

    handler = ExcelHandler(mock_rag)

    # Create test DataFrame
    df = pd.DataFrame({"Question": ["Question 1", "Question 2", "Question 3"]})

    # Process questions
    processed_df, message = handler._process_questions(df)

    # Verify results
    assert "Similarity Score" in processed_df.columns
    assert processed_df["Similarity Score"].tolist() == ["85.0%", "25.0%", "N/A"]

    # Verify answers
    answers = processed_df["Answers"].tolist()
    assert answers[0] == "Answer 1"  # High similarity answer kept
    assert (
        answers[1] == "Not enough information to answer this question."
    )  # Low similarity replaced
    assert (
        answers[2] == "Not enough information to answer this question."
    )  # No similarity case
    assert "successfully" in message
