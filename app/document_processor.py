from pathlib import Path
import pypdf  # Updated from PyPDF2
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document
from sqlalchemy.orm import Session
from app.embeddings_dao import EmbeddingsDAO
from app.models import ProcessedDocument


class DocumentProcessor:
    """Handles processing of PDF and Markdown files for embedding generation."""

    def __init__(self, embeddings_dao: EmbeddingsDAO, docs_dir: str = "data/docs"):
        """Initialize the document processor.

        Args:
            embeddings_dao: DAO for storing embeddings
            docs_dir: Directory containing documents to process
        """
        self.embeddings_dao = embeddings_dao
        self.docs_dir = Path(docs_dir)
        self.text_splitter = SentenceSplitter(
            chunk_size=1024,
            chunk_overlap=20,
            paragraph_separator="\n\n",
            secondary_chunking_regex="[^,.;]+[,.;]?",
        )

    def process_all_documents(self) -> None:
        """Process all PDFs and Markdown files in the configured directory."""
        if not self.docs_dir.exists():
            print(f"Documents directory {self.docs_dir} does not exist")
            return

        # Process PDFs
        for pdf_path in self.docs_dir.glob("*.pdf"):
            try:
                if not self._should_process_file(pdf_path):
                    print(f"Skipping already processed PDF: {pdf_path.name}")
                    continue
                print(f"Processing PDF: {pdf_path.name}...")
                self.process_pdf(pdf_path)
                self._mark_file_processed(pdf_path)
            except Exception as e:
                print(f"Error processing PDF {pdf_path.name}: {e}")

        # Process Markdown files
        for md_path in self.docs_dir.glob("*.md"):
            try:
                if not self._should_process_file(md_path):
                    print(f"Skipping already processed Markdown: {md_path.name}")
                    continue
                print(f"Processing Markdown: {md_path.name}...")
                self.process_markdown(md_path)
                self._mark_file_processed(md_path)
            except Exception as e:
                print(f"Error processing Markdown {md_path.name}: {e}")

    def _should_process_file(self, file_path: Path) -> bool:
        """Check if a file needs processing.

        Args:
            file_path: Path to the file to check

        Returns:
            True if file should be processed, False if already processed
        """
        with Session(self.embeddings_dao.db_handler.engine) as session:
            processed = (
                session.query(ProcessedDocument)
                .filter_by(filepath=str(file_path))
                .first()
            )
            return processed is None

    def _mark_file_processed(self, file_path: Path) -> None:
        """Mark a file as processed in the database.

        Args:
            file_path: Path to the processed file
        """
        with Session(self.embeddings_dao.db_handler.engine) as session:
            processed = ProcessedDocument(filepath=str(file_path))
            session.add(processed)
            session.commit()

    def process_pdf(self, pdf_path: Path) -> None:
        """Process a single PDF file.

        Args:
            pdf_path: Path to the PDF file
        """
        try:
            text = self._extract_pdf_text(pdf_path)
            self._process_text(text, source=pdf_path.name)
        except Exception as e:
            print(f"Error processing PDF {pdf_path.name}: {e}")

    def process_markdown(self, md_path: Path) -> None:
        """Process a single Markdown file.

        Args:
            md_path: Path to the Markdown file
        """
        text = self._extract_markdown_text(md_path)
        self._process_text(text, source=md_path.name)

    def _process_text(self, text: str, source: str) -> None:
        """Process extracted text by chunking and storing embeddings.

        Args:
            text: The text to process
            source: Source file name for metadata
        """
        doc = Document(text=text)
        nodes = self.text_splitter.get_nodes_from_documents([doc])
        for i, node in enumerate(nodes):
            self.embeddings_dao.add_text(
                node.text,
                document_metadata={
                    "source": source,
                    "chunk_index": i,
                    "total_chunks": len(nodes),
                },
            )

    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text content from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text content
        """
        text = []
        with open(pdf_path, "rb") as file:
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                text.append(page.extract_text())

        return "\n".join(text)

    def _extract_markdown_text(self, md_path: Path) -> str:
        """Extract text content from a Markdown file.

        Args:
            md_path: Path to the Markdown file

        Returns:
            Extracted text content
        """
        with open(md_path, "r", encoding="utf-8") as file:
            return file.read()
