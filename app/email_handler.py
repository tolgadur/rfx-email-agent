import imaplib
import email
import smtplib
import time
from email.message import EmailMessage, Message
from typing import Generator, Tuple, Dict, Optional
from io import BytesIO
import markdown


class EmailHandler:
    """Handles email operations including IMAP polling and SMTP sending."""

    def __init__(
        self,
        email: str,
        password: str,
        imap_server: str = "imap.gmail.com",
        smtp_server: str = "smtp.gmail.com",
    ):
        """Initialize the email handler with server configurations.

        Args:
            email: Email address for authentication
            password: Password for authentication
            imap_server: IMAP server address
            smtp_server: SMTP server address
        """
        self.email = email
        self.password = password
        self.imap_server = imap_server
        self.smtp_server = smtp_server

    def fetch_emails(self) -> Generator[Tuple[str, str, str, Message], None, None]:
        """Continuously fetch unread emails from the inbox.

        Yields:
            Tuple containing (sender, subject, body, message object)
        """
        print(f"IMAP_SERVER: {self.imap_server}, EMAIL: {self.email}")

        while True:
            try:
                mail = imaplib.IMAP4_SSL(self.imap_server, port=993)
                mail.login(self.email, self.password)
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
                            body = self._extract_body(msg)

                            print(f"Email received from {sender}.")
                            yield sender, subject, body, msg

                mail.logout()
                time.sleep(30)

            except Exception as e:
                print(f"Connection error: {e}")
                time.sleep(5)
                continue

    def send_email_response(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: Optional[Dict[str, BytesIO]] = None,
    ) -> None:
        """Send an email response with optional attachments.

        Args:
            to_email: The recipient's email address.
            subject: The email subject.
            body: The email body text.
            attachments: Optional dictionary of filename to file content mappings.
        """
        print("Sending email response...")
        msg = EmailMessage()
        msg["From"] = self.email
        msg["To"] = to_email
        msg["Subject"] = f"Re: {subject}"

        # Set plain text content first
        msg.set_content(body)

        # Then add HTML version
        html_content = markdown.markdown(body)
        msg.add_alternative(html_content, subtype="html")

        # Add attachments if present
        if attachments:
            for filename, attachment in attachments.items():
                msg.add_attachment(
                    attachment.getvalue(),
                    maintype="application",
                    subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    filename=filename,
                )

        with smtplib.SMTP(self.smtp_server, 587) as smtp:
            smtp.starttls()
            smtp.login(self.email, self.password)
            smtp.send_message(msg)
        print("Email sent successfully.")

    def _extract_body(self, msg: Message) -> str:
        """Extract the text body from an email message.

        Args:
            msg: The email message to extract the body from.

        Returns:
            The extracted body text.
        """
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
                body = msg.get_payload(decode=True).decode(
                    "iso-8859-1", errors="ignore"
                )
        return body
