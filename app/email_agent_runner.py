from app.email_handler import EmailHandler
from app.excel_handler import ExcelHandler
from app.rag_service import RAGService, RAGResponse
from app.template_handler import TemplateHandler
from app.db_handler import DatabaseHandler
from app.document_processor import DocumentProcessor


class EmailAgentRunner:
    """Main class that orchestrates the email processing workflow.

    This runner continuously monitors for new emails and processes them using
    various specialized handlers for AI responses, Excel processing, and email
    templating. The process continues indefinitely until manually stopped.
    """

    def __init__(
        self,
        email_handler: EmailHandler,
        excel_handler: ExcelHandler,
        rag_service: RAGService,
        template_handler: TemplateHandler,
        db_handler: DatabaseHandler,
        doc_processor: DocumentProcessor,
    ):
        """Initialize the runner with required handlers.

        Args:
            email_handler: Handler for email operations
            excel_handler: Handler for Excel file operations
            rag_service: Service for RAG operations
            template_handler: Handler for template rendering
            db_handler: Handler for database operations
            doc_processor: Processor for document embeddings
        """
        self.email_handler = email_handler
        self.excel_handler = excel_handler
        self.rag_service = rag_service
        self.template_handler = template_handler
        self.db_handler = db_handler
        self.doc_processor = doc_processor

    def run(self):
        """Main processing loop that continuously monitors for new emails.

        This method will run indefinitely, processing new emails as they arrive.
        The loop can only be terminated by external interruption (Ctrl+C) or
        an unhandled exception.
        """
        print("Initializing database...")
        try:
            self.db_handler.setup_database()
            print("Processing documents...")
            self.doc_processor.process_all_documents()
        except Exception as e:
            print(f"Failed to setup database: {e}")
            return

        print("Starting email processing...")
        try:
            for sender, subject, body, msg in self.email_handler.fetch_emails():
                print(f"Processing email from {sender}: {subject}")
                self._process_email(sender, subject, body, msg)
        finally:
            self.db_handler.close()

    def _process_email(self, sender: str, subject: str, body: str, msg):
        """Process a single email with its potential attachments.

        Args:
            sender: The email address of the sender
            subject: The subject line of the email
            body: The main text content of the email
            msg: The full email message object
        """
        # Get response for email body
        rag_response: RAGResponse = (
            self.rag_service.send_message(body)
            if body.strip()
            else RAGResponse("", None)
        )

        # Process attachments
        summary, processed_files = self.excel_handler.process_excel_attachment(msg)

        # Get file counts from excel handler
        excel_files, skipped_files = self.excel_handler.extract_excel_from_email(msg)
        num_attachments = len(excel_files) + len(skipped_files)
        num_processed_files = len(processed_files)
        num_failed_files = len(excel_files) - len(processed_files)
        num_skipped_files = len(skipped_files)

        # Render email template
        email_body = self.template_handler.render_template(
            body_response=rag_response.text,
            similarity_score=rag_response.max_similarity,
            document_url=rag_response.document_url,
            num_attachments=num_attachments,
            num_processed_files=num_processed_files,
            num_failed_files=num_failed_files,
            num_skipped_files=num_skipped_files,
            detailed_summary=summary,
        )

        # Send response
        if email_body:
            self.email_handler.send_email_response(
                to_email=sender,
                subject=subject,
                body=email_body,
                attachments=processed_files,
            )
