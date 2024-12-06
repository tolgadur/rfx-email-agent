import imaplib
import email
import smtplib
import time
from email.message import EmailMessage
from config import IMAP_SERVER, SMTP_SERVER, EMAIL, PASSWORD


def fetch_emails():
    print(f"IMAP_SERVER: {IMAP_SERVER}, EMAIL: {EMAIL}")
    
    while True:  # Keep running indefinitely
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, port=993)
            mail.login(EMAIL, PASSWORD)
            mail.select("inbox")

            _, message_numbers = mail.search(None, "UNSEEN")
            for num in message_numbers[0].split():
                print(f"New email received: {num}")
                _, msg_data = mail.fetch(num, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        sender = msg["From"]
                        subject = msg["Subject"]
                        body = extract_body(msg)
                        print(f"Email received from {sender}.")
                        yield sender, subject, body

            mail.logout()

            # Pause before checking for new emails again (e.g., 30 seconds)
            time.sleep(30)
        except Exception as e:
            print(f"Connection error: {e}")
            time.sleep(5)  # Wait before retrying
            continue


def extract_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode()
                break
    else:
        body = msg.get_payload(decode=True).decode()
    return body


def send_email_response(to_email, subject, body):
    print("Sending email response...")
    msg = EmailMessage()
    msg["From"] = EMAIL
    msg["To"] = to_email
    msg["Subject"] = f"Re: {subject}"
    msg.set_content(body)

    with smtplib.SMTP(SMTP_SERVER, 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL, PASSWORD)
        smtp.send_message(msg)
