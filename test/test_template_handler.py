import pytest
from pathlib import Path
from app.template_handler import render_email_template


TEST_CASES = [
    ({"body_response": "Test"}, ["Test"], "Single string parameter"),
    (
        {
            "num_attachments": 5,
            "num_processed_files": 3,
            "num_failed_files": 1,
            "num_skipped_files": 1,
        },
        ["5", "3", "1", "1"],
        "Single numeric parameter",
    ),
    (
        {
            "num_attachments": 5,
            "num_processed_files": 3,
            "num_failed_files": 2,
            "num_skipped_files": 0,
        },
        ["3", "2", "0"],
        "Multiple numeric parameters",
    ),
    (
        {
            "body_response": "Test response",
            "num_attachments": 2,
            "num_processed_files": 1,
            "num_failed_files": 1,
            "num_skipped_files": 0,
            "detailed_summary": "Test summary",
        },
        ["Test response", "2", "1", "1", "0", "Test summary"],
        "Basic test case",
    ),
    (
        {
            "body_response": "Complex\nResponse\nWith\nNewlines",
            "num_attachments": 10,
            "num_processed_files": 8,
            "num_failed_files": 2,
            "num_skipped_files": 0,
            "detailed_summary": "Detailed\nSummary\nHere",
        },
        ["Complex", "Response", "10", "8", "2", "0", "Detailed", "Summary"],
        "Complex test case with newlines",
    ),
    (
        {
            "body_response": "Special chars: !@#$%^&*()",
            "num_attachments": 2,
            "num_processed_files": 2,
            "num_failed_files": 0,
            "num_skipped_files": 0,
            "detailed_summary": "More special chars: <>?,./",
        },
        ["Special chars", "!@#$%^&*()", "<>?,./", "2", "0"],
        "Special characters test case",
    ),
    (
        {
            "num_attachments": 175,
            "num_processed_files": 100,
            "num_failed_files": 50,
            "num_skipped_files": 25,
        },
        ["175", "100", "50", "25"],
        "Large numbers",
    ),
]


INVALID_FILE_COUNTS = [
    (
        {
            "num_attachments": 5,
            "num_processed_files": 3,
            "num_failed_files": 1,
            "num_skipped_files": 0,
        },
        (
            "Sum of processed (3), failed (1), and skipped (0) files (4) must match "
            "num_attachments (5)"
        ),
        "Total less than attachments",
    ),
    (
        {
            "num_attachments": 5,
            "num_processed_files": 3,
            "num_failed_files": 2,
            "num_skipped_files": 1,
        },
        (
            "Sum of processed (3), failed (2), and skipped (1) files (6) must match ",
            "num_attachments (5)",
        ),
        "Total more than attachments",
    ),
    (
        {
            "num_attachments": 0,
            "num_processed_files": 1,
            "num_failed_files": 0,
            "num_skipped_files": 0,
        },
        (
            "Sum of processed (1), failed (0), and skipped (0) files (1) must match ",
            "num_attachments (0)",
        ),
        "Files present with no attachments",
    ),
]


@pytest.mark.parametrize("test_input,expected_substrings,test_name", TEST_CASES)
def test_render_email_template(test_input, expected_substrings, test_name):
    """
    Test template rendering with different inputs and verify both type and content.
    """
    result = render_email_template(**test_input)

    # Type check
    assert isinstance(result, str), f"Result not string on {test_name}"
    assert result != "", f"Empty result on {test_name}"

    # Content check
    for substring in expected_substrings:
        assert (
            str(substring) in result
        ), f"'{substring}' not found in result on {test_name}"


@pytest.mark.parametrize("test_input,expected_error,test_name", INVALID_FILE_COUNTS)
def test_invalid_file_counts(test_input, expected_error, test_name):
    """
    Test that appropriate error is raised when file counts don't match attachments.
    """
    with pytest.raises(ValueError) as exc_info:
        render_email_template(**test_input)
    if isinstance(expected_error, tuple):
        expected_error = "".join(expected_error)
    assert (
        str(exc_info.value) == expected_error
    ), f"Unexpected error message on {test_name}"


def test_empty_body_message():
    """Test that appropriate message is shown when body is empty."""
    result = render_email_template(body_response="")
    assert isinstance(result, str)
    assert "We could not identify any technical questions in your email body." in result


def test_no_attachments_message():
    """Test that appropriate message is shown when no attachments are present."""
    result = render_email_template(num_attachments=0)
    assert isinstance(result, str)
    assert "We did not find any Excel files in your email." in result


def test_empty_input():
    """Test behavior with completely empty input."""
    result = render_email_template()
    assert isinstance(result, str)
    assert "We could not identify any technical questions in your email body." in result
    assert "We did not find any Excel files in your email." in result


def test_template_file_exists():
    """Test that the email template file exists."""
    template_path = Path(__file__).parent.parent / "assets" / "email.md"
    assert template_path.exists(), "Template file does not exist"
