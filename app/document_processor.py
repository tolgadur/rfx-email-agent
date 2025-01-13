from pathlib import Path
import pypdf
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document as LlamaDocument
from sqlalchemy.orm import Session
from app.embeddings_dao import EmbeddingsDAO
from app.models import Document, Embedding
from app.config import CHUNK_SIZE, CHUNK_OVERLAP


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
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
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
            doc = session.query(Document).filter_by(filepath=str(file_path)).first()
            return doc is None or not doc.processed

    def _create_document(self, file_path: Path, session: Session) -> Document:
        """Create a new document record in the database.

        Args:
            file_path: Path to the document file
            session: Database session to use

        Returns:
            The created Document instance or existing one if present.
        """
        print(f"\nChecking for existing document: {file_path}")
        # Check if the document already exists
        existing_doc = (
            session.query(Document).filter_by(filepath=str(file_path)).first()
        )
        if existing_doc:
            print(f"Found existing document with ID: {existing_doc.id}")
            return existing_doc

        # Create a new document record if it doesn't exist
        print("Creating new document record...")
        doc = Document(filepath=str(file_path))
        session.add(doc)
        session.flush()  # Flush to get the ID without committing
        print(f"Created new document with ID: {doc.id}")
        return doc

    def _mark_document_processed(self, document_id: int, session: Session) -> None:
        """Mark a document as processed in the database.

        Args:
            document_id: ID of the document to mark as processed
            session: Database session to use
        """
        doc = session.query(Document).filter_by(id=document_id).first()
        if doc:
            doc.processed = True

    def process_pdf(self, pdf_path: Path) -> None:
        """Process a single PDF file.

        Args:
            pdf_path: Path to the PDF file
        """
        try:
            print(f"\nStarting to process PDF: {pdf_path}")
            with Session(self.embeddings_dao.db_handler.engine) as session:
                doc = self._create_document(pdf_path, session)
                if doc.processed:
                    print("Document is already processed")
                    return

                print("Extracting text from PDF...")
                text = self._extract_pdf_text(pdf_path)
                print(f"Extracted {len(text)} characters of text")

                print("Processing text chunks...")
                self._process_text(text, pdf_path.name, doc.id, session)
                print("Text processing complete")

                print("Marking document as processed...")
                self._mark_document_processed(doc.id, session)

                # Commit all changes at once
                session.commit()
                print(f"Successfully processed PDF: {pdf_path}")

        except Exception as e:
            print(f"Error processing PDF {pdf_path.name}: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback

            print(f"Traceback:\n{traceback.format_exc()}")

    def process_markdown(self, md_path: Path) -> None:
        """Process a single Markdown file.

        Args:
            md_path: Path to the Markdown file
        """
        try:
            print(f"\nStarting to process Markdown: {md_path}")
            with Session(self.embeddings_dao.db_handler.engine) as session:
                doc = self._create_document(md_path, session)
                if doc.processed:
                    print("Document is already processed")
                    return

                print("Extracting text from Markdown...")
                text = self._extract_markdown_text(md_path)
                print(f"Extracted {len(text)} characters of text")

                print("Processing text chunks...")
                self._process_text(text, md_path.name, doc.id, session)

                print("Marking document as processed...")
                self._mark_document_processed(doc.id, session)

                # Commit all changes at once
                session.commit()
                print(f"Successfully processed Markdown: {md_path}")

        except Exception as e:
            print(f"Error processing Markdown {md_path.name}: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback

            print(f"Traceback:\n{traceback.format_exc()}")

    def _process_text(
        self, text: str, source: str, document_id: int, session: Session
    ) -> None:
        """Process extracted text by chunking and storing embeddings.

        Args:
            text: The text to process
            source: Source file name for metadata
            document_id: ID of the associated Document
            session: Database session to use for storing embeddings
        """
        print(f"\nProcessing text for document ID: {document_id}")
        print("Creating LlamaDocument...")
        llama_doc = LlamaDocument(text=text)

        print("Splitting text into nodes...")
        nodes = self.text_splitter.get_nodes_from_documents([llama_doc])
        print(f"Created {len(nodes)} text chunks")

        for i, node in enumerate(nodes):
            print(f"Processing chunk {i + 1}/{len(nodes)}...")
            embedding_vector = self.embeddings_dao._generate_embedding(node.text)
            print(f"\nGenerated embedding for text: {node.text[:50]}...")
            print(f"Embedding vector (first 5 values): {embedding_vector[:5]}")
            embedding_obj = Embedding(
                text=node.text,
                embedding=embedding_vector,
                embedding_metadata={
                    "source": source,
                    "chunk_index": i,
                    "total_chunks": len(nodes),
                },
                document_id=document_id,
            )
            session.add(embedding_obj)
            session.flush()  # Flush to get the ID without committing
            print(f"Created embedding with ID: {embedding_obj.id}")

        # Verify embeddings were created
        embeddings_count = (
            session.query(Embedding).filter_by(document_id=document_id).count()
        )
        print(
            f"\nTotal embeddings created for document {document_id}: {embeddings_count}"
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
