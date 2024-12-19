from email_handler import fetch_emails, send_email_response
from excel_handler import process_excel_attachment
from pinecone_handler import send_message_to_assistant


def process_email(sender: str, subject: str, body: str, msg):
    """Process a single email with its potential attachments."""
    # Send the body to the assistant and get a response
    response = send_message_to_assistant(body)

    # Process the attachments
    processed_response, processed_files = process_excel_attachment(msg)

    # Combine the responses
    final_response = response + "\n\n" + processed_response

    # Send the email response with all attachments
    if final_response:
        send_email_response(
            to_email=sender,
            subject=subject,
            body=final_response,
            attachments=processed_files,
        )


def main():
    print("Starting email processing...")
    for sender, subject, body, msg in fetch_emails():
        print(f"Processing email from {sender}: {subject}")
        process_email(sender, subject, body, msg)


if __name__ == "__main__":
    main()
