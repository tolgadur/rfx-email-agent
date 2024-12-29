from jinja2 import Template


class TemplateHandler:
    """Handles email template rendering using Jinja2."""

    def __init__(self, template: Template):
        """Initialize the template handler with a Jinja2 template.

        Args:
            template: The Jinja2 template to use for rendering
        """
        self.template = template

    def render_template(
        self,
        body_response: str = "",
        num_attachments: int = 0,
        num_processed_files: int = 0,
        num_failed_files: int = 0,
        num_skipped_files: int = 0,
        detailed_summary: str = "",
    ) -> str:
        """Render the email template with the given context.

        Args:
            body_response: The response to the email body
            num_attachments: Total number of attachments
            num_processed_files: Number of successfully processed files
            num_failed_files: Number of files that failed processing
            num_skipped_files: Number of files that were skipped
            detailed_summary: Detailed summary of processing results

        Returns:
            The rendered template as a string.

        Raises:
            ValueError: If the sum of processed, failed, and skipped files does not
                equal num_attachments
        """
        total_files = num_processed_files + num_failed_files + num_skipped_files
        if total_files != num_attachments:
            raise ValueError(
                f"Sum of processed ({num_processed_files}), "
                f"failed ({num_failed_files}), "
                f"and skipped ({num_skipped_files}) files ({total_files}) "
                f"must match num_attachments ({num_attachments})"
            )

        return self.template.render(
            body_response=body_response,
            num_attachments=num_attachments,
            num_processed_files=num_processed_files,
            num_failed_files=num_failed_files,
            num_skipped_files=num_skipped_files,
            detailed_summary=detailed_summary,
        )
