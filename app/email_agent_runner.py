from app.email_handler import EmailHandler
from app.excel_handler import ExcelHandler
from app.pinecone_handler import PineconeHandler
from app.template_handler import TemplateHandler
from app.db_handler import DatabaseHandler


class EmailAgentRunner:
    """Main class that orchestrates the email processing workflow.

    This runner continuously monitors for new emails and processes them using
    various specialized handlers for AI responses, Excel processing, and email
    templating. The process continues indefinitely until manually stopped.
    """

    def __init__(self):
        """Initialize all handlers."""
        self.email_handler = EmailHandler()
        self.excel_handler = ExcelHandler()
        self.pinecone_handler = PineconeHandler()
        self.template_handler = TemplateHandler()
        self.db_handler = DatabaseHandler()

    def run(self):
        """Main processing loop that continuously monitors for new emails.

        This method will run indefinitely, processing new emails as they arrive.
        The loop can only be terminated by external interruption (Ctrl+C) or
        an unhandled exception.
        """
        print("Initializing database...")
        try:
            self.db_handler.setup_database()
        except Exception as e:
            print(f"Failed to setup database: {e}")
            return

        print("Starting email processing...")
        for sender, subject, body, msg in self.email_handler.fetch_emails():
            print(f"Processing email from {sender}: {subject}")
            self._process_email(sender, subject, body, msg)

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
        body_response = self.pinecone_handler.send_message(body) if body.strip() else ""

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
            body_response=body_response,
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
