"""Integration tests for DocumentProcessor using real PostgreSQL database."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from app.document_processor import DocumentProcessor
from app.embeddings_dao import EmbeddingsDAO
from app.models import Document, Embedding


@pytest.fixture
def embeddings_dao(db_handler):
    """Create an embeddings DAO with real PostgreSQL database."""
    return EmbeddingsDAO(db_handler=db_handler)


@pytest.fixture
def processor(embeddings_dao):
    """Create a document processor with real PostgreSQL database."""
    return DocumentProcessor(embeddings_dao=embeddings_dao, docs_dir=Path("test/data"))


def test_process_markdown(processor):
    content = "# Test\nThis is a test markdown file."
    with patch("pathlib.Path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data=content)
    ):
        processor.process_markdown(Path("test.md"))

    with processor.embeddings_dao.db_handler.get_session() as session:
        doc = session.query(Document).first()
        assert doc.filepath == "test.md"
        assert doc.processed is True

        embedding = session.query(Embedding).first()
        assert embedding.text == content
        assert embedding.document_id == doc.id


def test_process_pdf(processor):
    content = "This is a test PDF file."

    with patch("pathlib.Path.exists", return_value=True), patch(
        "builtins.open", mock_open()
    ), patch("pypdf.PdfReader") as mock_reader:

        mock_page = MagicMock()
        mock_page.extract_text.return_value = content
        mock_reader.return_value.pages = [mock_page]

        processor.process_pdf(Path("test.pdf"))

    with processor.embeddings_dao.db_handler.get_session() as session:
        doc = session.query(Document).first()
        assert doc.filepath == "test.pdf"
        assert doc.processed is True

        embedding = session.query(Embedding).first()
        assert embedding.text == content
        assert embedding.document_id == doc.id


def test_text_chunking(processor):
    """Test that text is properly chunked and preserved."""
    with processor.embeddings_dao.db_handler.get_session() as session:
        assert (
            session.query(Embedding).count() == 0
        ), "Database should be empty before test"

    with patch("pathlib.Path.exists", return_value=True):
        processor.process_pdf(Path("test/data/SAP Technical Questions.pdf"))

    with processor.embeddings_dao.db_handler.get_session() as session:
        embeddings = session.query(Embedding).order_by(Embedding.id).all()
        texts = [emb.text for emb in embeddings]
        unique_texts = set(texts)

        # Check that text is split into chunks without duplicates
        assert len(embeddings) == 1, "Text should be split in one chunk"
        assert len(texts) == len(unique_texts), "Found duplicate chunks"

        # Check that key information about byte limits is preserved
        assert any(
            "SAP SuccessFactors Learning labels have a limit of 10,000 bytes." in text
            for text in texts
        ), "Key information about byte limit was not preserved"
