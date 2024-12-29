from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from app.config import Config
from app.email_handler import EmailHandler
from app.excel_handler import ExcelHandler
from app.pinecone_handler import PineconeHandler
from app.template_handler import TemplateHandler
from app.db_handler import DatabaseHandler
from app.email_agent_runner import EmailAgentRunner


def main() -> None:
    """Entry point of the application."""
    # Load configuration
    config = Config.from_env()

    # Create infrastructure services
    db_handler = DatabaseHandler(database_url=config.database_url)

    pinecone_handler = PineconeHandler(api_key=config.pinecone_api_key)

    email_handler = EmailHandler(
        email=config.email,
        password=config.password,
        imap_server=config.imap_server,
        smtp_server=config.smtp_server,
    )

    # Create template handler
    email_template = Environment(
        loader=FileSystemLoader(Path(__file__).parent.parent / "assets")
    ).get_template("email.md")

    template_handler = TemplateHandler(template=email_template)

    # Create business logic services
    excel_handler = ExcelHandler(pinecone_handler=pinecone_handler)

    # Create and run the application
    runner = EmailAgentRunner(
        email_handler=email_handler,
        excel_handler=excel_handler,
        pinecone_handler=pinecone_handler,
        template_handler=template_handler,
        db_handler=db_handler,
    )
    runner.run()


if __name__ == "__main__":
    main()
