import imaplib
import email
from email.message import EmailMessage
from app.config import IMAP_SERVER, SMTP_SERVER, EMAIL, PASSWORD

def fetch_emails():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    _, message_numbers = mail.search(None, "UNSEEN")
    for num in message_numbers[0].split():
        _, msg_data = mail.fetch(num, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                sender = msg["From"]
                subject = msg["Subject"]
                body = extract_body(msg)
                yield sender, subject, body

    mail.logout()

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
    msg = EmailMessage()
    msg["From"] = EMAIL
    msg["To"] = to_email
    msg["Subject"] = f"Re: {subject}"
    msg.set_content(body)

    with smtplib.SMTP(SMTP_SERVER, 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL, PASSWORD)
        smtp.send_message(msg)
