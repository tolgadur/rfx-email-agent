from app.email_handler import fetch_emails, send_email_response
from app.excel_handler import process_excel_attachment, extract_excel_from_email
from app.pinecone_handler import send_message_to_assistant
from app.template_handler import render_email_template
from app.db_handler import DatabaseHandler


def process_email(sender: str, subject: str, body: str, msg):
    """Process a single email with its potential attachments."""
    # Get response for email body
    body_response = send_message_to_assistant(body) if body.strip() else ""

    # Process attachments
    summary, processed_files = process_excel_attachment(msg)

    # Get file counts from excel handler
    excel_files, skipped_files = extract_excel_from_email(msg)
    num_attachments = len(excel_files) + len(skipped_files)
    num_processed_files = len(processed_files)
    num_failed_files = len(excel_files) - len(processed_files)
    num_skipped_files = len(skipped_files)

    # Render email template
    email_body = render_email_template(
        body_response=body_response,
        num_attachments=num_attachments,
        num_processed_files=num_processed_files,
        num_failed_files=num_failed_files,
        num_skipped_files=num_skipped_files,
        detailed_summary=summary,
    )

    # Send response
    if email_body:
        send_email_response(
            to_email=sender,
            subject=subject,
            body=email_body,
            attachments=processed_files,
        )


def main():
    print("Initializing database...")
    db = DatabaseHandler()
    try:
        db.setup_database()
    except Exception as e:
        print(f"Failed to setup database: {e}")
        return

    print("Starting email processing...")
    for sender, subject, body, msg in fetch_emails():
        print(f"Processing email from {sender}: {subject}")
        process_email(sender, subject, body, msg)

    db.close()


if __name__ == "__main__":
    main()
