from jinja2 import Environment, FileSystemLoader
from app.config import (
    EMAIL,
    PASSWORD,
    DATABASE_URL,
    IMAP_SERVER,
    SMTP_SERVER,
    SIMILARITY_THRESHOLD,
    ASSETS_DIR,
)
from app.email_handler import EmailHandler
from app.excel_handler import ExcelHandler
from app.template_handler import TemplateHandler
from app.db_handler import DatabaseHandler
from app.embeddings_dao import EmbeddingsDAO
from app.rag_service import RAGService
from app.email_agent_runner import EmailAgentRunner


def main() -> None:
    """Entry point of the application."""
    # Create infrastructure services
    db_handler = DatabaseHandler(database_url=DATABASE_URL)
    embeddings_dao = EmbeddingsDAO(db_handler=db_handler)
    rag_service = RAGService(
        embeddings_dao=embeddings_dao, similarity_threshold=SIMILARITY_THRESHOLD
    )

    email_handler = EmailHandler(
        email=EMAIL,
        password=PASSWORD,
        imap_server=IMAP_SERVER,
        smtp_server=SMTP_SERVER,
    )

    # Create template handler
    email_template = Environment(loader=FileSystemLoader(ASSETS_DIR)).get_template(
        "email.md"
    )

    template_handler = TemplateHandler(template=email_template)

    # Create business logic services
    excel_handler = ExcelHandler(rag_service=rag_service)

    # Create and run the application
    runner = EmailAgentRunner(
        email_handler=email_handler,
        excel_handler=excel_handler,
        rag_service=rag_service,
        template_handler=template_handler,
        db_handler=db_handler,
    )
    runner.run()


if __name__ == "__main__":
    main()
