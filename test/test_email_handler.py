import pytest
from unittest.mock import patch, MagicMock
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
from io import BytesIO
from app.email_handler import EmailHandler


@pytest.fixture
def email_handler():
    """Create an EmailHandler instance for testing."""
    return EmailHandler(
        email="test@example.com",
        password="test_password",
        imap_server="imap.test.com",
        smtp_server="smtp.test.com",
    )


@pytest.fixture
def sample_email_message():
    """Create a simple email message for testing."""
    msg = EmailMessage()
    msg.set_content("Test body")
    return msg


@pytest.fixture
def sample_multipart_message():
    """Create a multipart email message for testing."""
    msg = MIMEMultipart()
    text_part = MIMEText("Test body", "plain")
    msg.attach(text_part)
    return msg


def test_extract_body_simple(email_handler, sample_email_message):
    """Test body extraction from simple email."""
    body = email_handler._extract_body(sample_email_message)
    assert body.strip() == "Test body"


def test_extract_body_multipart(email_handler, sample_multipart_message):
    """Test body extraction from multipart email."""
    body = email_handler._extract_body(sample_multipart_message)
    assert body.strip() == "Test body"


@patch("smtplib.SMTP")
def test_send_email_response_without_attachments(mock_smtp, email_handler):
    """Test sending email response without attachments."""
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

    to_email = "test@example.com"
    subject = "Test Subject"
    body = "Test Body"

    email_handler.send_email_response(to_email, subject, body)

    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with(
        email_handler.email, email_handler.password
    )
    mock_smtp_instance.send_message.assert_called_once()

    sent_msg = mock_smtp_instance.send_message.call_args[0][0]
    assert sent_msg["To"] == to_email
    assert sent_msg["Subject"] == f"Re: {subject}"

    # For multipart messages, check the plain text part
    if sent_msg.is_multipart():
        for part in sent_msg.walk():
            if part.get_content_type() == "text/plain":
                assert part.get_payload().strip() == body
                break
    else:
        assert sent_msg.get_content().strip() == body


@patch("smtplib.SMTP")
def test_send_email_response_with_attachments(mock_smtp, email_handler):
    """Test sending email response with attachments."""
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

    to_email = "test@example.com"
    subject = "Test Subject"
    body = "Test Body"
    attachments = {"test.xlsx": BytesIO(b"test content")}

    email_handler.send_email_response(to_email, subject, body, attachments)

    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with(
        email_handler.email, email_handler.password
    )
    mock_smtp_instance.send_message.assert_called_once()

    sent_msg = mock_smtp_instance.send_message.call_args[0][0]
    assert sent_msg["To"] == to_email
    assert sent_msg["Subject"] == f"Re: {subject}"
    # For multipart messages, we need to check the first part for the body
    if sent_msg.is_multipart():
        body_part = None
        for part in sent_msg.walk():
            if part.get_content_type() == "text/plain":
                body_part = part
                break
        assert body_part is not None
        assert body_part.get_payload().strip() == body
