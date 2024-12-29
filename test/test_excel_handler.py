import pytest
import io
import pandas as pd
from email.message import Message
from unittest.mock import patch, MagicMock
from app.excel_handler import ExcelHandler


@pytest.fixture
def excel_handler():
    """Create an ExcelHandler instance for testing."""
    with patch("app.excel_handler.PineconeHandler") as mock_pinecone_cls:
        handler = ExcelHandler()
        # Store mock for easy access in tests
        handler.mock_pinecone = mock_pinecone_cls.return_value
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
    excel_handler.mock_pinecone.send_message.return_value = "Test answer"
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
