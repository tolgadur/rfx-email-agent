from email_handler import fetch_emails, send_email_response
from excel_handler import process_excel_attachment
from pinecone_handler import send_message_to_assistant


def process_email(sender: str, subject: str, body: str, msg):
    """Process a single email with its potential attachments."""
    # Get response from assistant for the email body
    response = send_message_to_assistant(body)
    
    # Process Excel attachment if present
    excel_result, attachment = process_excel_attachment(msg)
    has_excel = excel_result != "No Excel file found in attachment"

    # Combine assistant response with Excel results if applicable
    final_response = response
    if has_excel:
        final_response = f"{response}\n\nExcel Processing Result:\n{excel_result}"

    if final_response:
        send_email_response(
            to_email=sender,
            subject=subject,
            body=final_response,
            attachment=attachment
        )


def main():
    print("Starting email processing...")
    for sender, subject, body, msg in fetch_emails():
        print(f"Processing email from {sender}: {subject}")
        process_email(sender, subject, body, msg)


if __name__ == "__main__":
    main()
