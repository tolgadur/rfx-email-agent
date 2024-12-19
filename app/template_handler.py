from jinja2 import Environment, FileSystemLoader
from pathlib import Path


def render_email_template(
    body_response: str = "",
    num_attachments: int = 0,
    num_processed_files: int = 0,
    num_failed_files: int = 0,
    num_skipped_files: int = 0,
    detailed_summary: str = "",
) -> str:
    """Render the email template with the given context."""
    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent.parent / "assets"),
    )
    template = env.get_template("email.md")

    return template.render(
        body_response=body_response,
        num_attachments=num_attachments,
        num_processed_files=num_processed_files,
        num_failed_files=num_failed_files,
        num_skipped_files=num_skipped_files,
        detailed_summary=detailed_summary,
    )
