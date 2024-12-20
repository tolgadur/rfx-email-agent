import imaplib
import email
import smtplib
import time
from email.message import EmailMessage
from app.config import IMAP_SERVER, SMTP_SERVER, EMAIL, PASSWORD


def has_excel_attachment(msg: email.message.Message) -> bool:
    for part in msg.walk():
        if part.get_content_maintype() == "application":
            filename = part.get_filename()
            if filename and (filename.endswith(".xlsx") or filename.endswith(".xls")):
                return True
    return False


def fetch_emails():
    print(f"IMAP_SERVER: {IMAP_SERVER}, EMAIL: {EMAIL}")

    while True:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, port=993)
            mail.login(EMAIL, PASSWORD)
            mail.select("inbox")

            _, message_numbers = mail.search(None, "UNSEEN")
            for num in message_numbers[0].split():
                print(f"New email received: {num}")
                _, msg_data = mail.fetch(num, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple) and len(response_part) > 1:
                        msg = email.message_from_bytes(response_part[1])
                        sender = msg["From"]
                        subject = msg["Subject"]
                        body = extract_body(msg)

                        print(f"Email received from {sender}.")
                        yield sender, subject, body, msg

            mail.logout()
            time.sleep(30)

        except Exception as e:
            print(f"Connection error: {e}")
            time.sleep(5)
            continue


def extract_body(msg: email.message.Message) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode("utf-8")
                except UnicodeDecodeError:
                    # Fallback to a different encoding if UTF-8 fails
                    body = part.get_payload(decode=True).decode(
                        "iso-8859-1", errors="ignore"
                    )
                break
    else:
        try:
            body = msg.get_payload(decode=True).decode("utf-8")
        except UnicodeDecodeError:
            body = msg.get_payload(decode=True).decode("iso-8859-1", errors="ignore")
    return body


def send_email_response(to_email: str, subject: str, body: str, attachments=None):
    print("Sending email response...")
    msg = EmailMessage()
    msg["From"] = EMAIL
    msg["To"] = to_email
    msg["Subject"] = f"Re: {subject}"
    msg.set_content(body)

    # Add attachments if present
    if attachments:
        for filename, attachment in attachments.items():
            msg.add_attachment(
                attachment.getvalue(),
                maintype="application",
                subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename=filename,
            )

    with smtplib.SMTP(SMTP_SERVER, 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL, PASSWORD)
        smtp.send_message(msg)
    print("Email sent successfully.")
