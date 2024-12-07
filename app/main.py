from email_handler import fetch_emails, send_email_response
from pinecone_handler import send_message_to_assistant


def main():
    print("Starting email processing...")
    for sender, subject, body in fetch_emails():
        print(f"Processing email from {sender}: {subject}")

        assistant_question = body
        response = send_message_to_assistant(assistant_question)

        send_email_response(to_email=sender, subject=subject, body=response)


if __name__ == "__main__":
    main()
