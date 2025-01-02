import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
from app.document_processor import DocumentProcessor
from app.models import ProcessedDocument


@pytest.fixture
def mock_embeddings_dao():
    """Create a mock embeddings DAO."""
    dao = MagicMock()
    dao.db_handler.engine = MagicMock()
    return dao


@pytest.fixture
def doc_processor(mock_embeddings_dao):
    """Create a document processor with mocked dependencies."""
    return DocumentProcessor(mock_embeddings_dao)


@patch("pathlib.Path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open)
@patch("pypdf.PdfReader")
@patch("sqlalchemy.orm.Session")
def test_process_pdf(
    mock_session_class, mock_reader, mock_file, mock_exists, doc_processor
):
    """Test PDF processing."""
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = None
    mock_session_class.return_value.__enter__.return_value = mock_session

    mock_pdf_content = "Test PDF content\nWith multiple lines"
    test_file = Path("test.pdf")

    # Mock PDF pages
    mock_page = MagicMock()
    mock_page.extract_text.return_value = mock_pdf_content
    mock_reader.return_value.pages = [mock_page]

    # Process the mock PDF
    doc_processor.process_pdf(test_file)

    # Verify the content was processed and added
    doc_processor.embeddings_dao.add_text.assert_called_with(
        mock_pdf_content,
        document_metadata={
            "source": "test.pdf",
            "chunk_index": 0,
            "total_chunks": 1,
        },
    )


@patch("pathlib.Path.glob")
@patch("pathlib.Path.exists", return_value=True)
@patch.object(DocumentProcessor, "process_pdf")
@patch.object(DocumentProcessor, "process_markdown")
@patch("sqlalchemy.orm.Session")
def test_skip_processed_documents(
    mock_session_class,
    mock_process_md,
    mock_process_pdf,
    mock_exists,
    mock_glob,
    doc_processor,
):
    """Test that already processed documents are skipped."""
    # Mock that files are already processed
    mock_session = MagicMock()
    processed_doc = ProcessedDocument(filepath="test1.pdf")
    mock_session.query.return_value.filter_by.return_value.first.return_value = (
        processed_doc
    )
    mock_session_class.return_value.__enter__.return_value = mock_session

    mock_glob.return_value = [Path("test1.pdf")]
    doc_processor.process_all_documents()

    # Verify no processing was attempted
    mock_process_pdf.assert_not_called()
    mock_process_md.assert_not_called()


@patch("pathlib.Path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open)
@patch("sqlalchemy.orm.Session")
def test_process_markdown(mock_session_class, mock_file, mock_exists, doc_processor):
    """Test Markdown processing."""
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = None
    mock_session_class.return_value.__enter__.return_value = mock_session

    mock_md_content = "# Test Markdown\nThis is a test document."
    test_file = Path("test.md")

    mock_file.return_value.read.return_value = mock_md_content
    doc_processor.process_markdown(test_file)

    # Verify the content was processed and added
    doc_processor.embeddings_dao.add_text.assert_called_with(
        mock_md_content,
        document_metadata={
            "source": "test.md",
            "chunk_index": 0,
            "total_chunks": 1,
        },
    )


@patch("pathlib.Path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open)
@patch("pypdf.PdfReader", side_effect=Exception("PDF Error"))
@patch("builtins.print")
def test_process_pdf_error_handling(
    mock_print, mock_reader, mock_file, mock_exists, doc_processor
):
    """Test error handling during PDF processing."""
    doc_processor.process_pdf(Path("bad.pdf"))

    # Verify error was logged
    mock_print.assert_called_with("Error processing PDF bad.pdf: PDF Error")
