from email_handler import fetch_emails, send_email_response
from pinecone_handler import send_message_to_assistant


def main():
    print("Starting email processing...")
    for sender, subject, body, has_excel in fetch_emails():
        print(f"Processing email from {sender}: {subject}")

        response = send_message_to_assistant(body, has_excel)
        if response:  # Only send if we got a non-empty response
            send_email_response(to_email=sender, subject=subject, body=response)


if __name__ == "__main__":
    main()
