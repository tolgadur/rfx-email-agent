from jinja2 import Environment, FileSystemLoader
import uvicorn
import threading
from app.config import (
    EMAIL,
    PASSWORD,
    DATABASE_URL,
    IMAP_SERVER,
    SMTP_SERVER,
    ASSETS_DIR,
)
from app.document_processor import DocumentProcessor
from app.email_handler import EmailHandler
from app.excel_handler import ExcelHandler
from app.template_handler import TemplateHandler
from app.db_handler import DatabaseHandler
from app.embeddings_dao import EmbeddingsDAO
from app.rag_service import RAGService
from app.email_agent_runner import EmailAgentRunner
from app.api import init_app
from app.config import HOST, PORT


def run_email_agent(runner: EmailAgentRunner):
    """Run the email agent in a separate thread."""
    runner.run()


def main() -> None:
    """Entry point of the application."""
    try:
        # Create infrastructure services
        db_handler = DatabaseHandler(database_url=DATABASE_URL)
        embeddings_dao = EmbeddingsDAO(db_handler=db_handler)
        doc_processor = DocumentProcessor(embeddings_dao=embeddings_dao)

        rag_service = RAGService(embeddings_dao=embeddings_dao)

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

        # Initialize database and process documents
        print("Initializing database...")
        db_handler.setup_database()
        print("Processing documents...")
        doc_processor.process_all_documents()

        # Create and start the email agent in a separate thread
        runner = EmailAgentRunner(
            email_handler=email_handler,
            excel_handler=excel_handler,
            rag_service=rag_service,
            template_handler=template_handler,
        )
        email_thread = threading.Thread(target=run_email_agent, args=(runner,))
        email_thread.daemon = True
        email_thread.start()

        # Initialize and run FastAPI app
        app = init_app(embeddings_dao)
        uvicorn.run(app, host=HOST, port=PORT)

    except Exception as e:
        print("Exception occurred:", e)
        return
    finally:
        db_handler.close()


if __name__ == "__main__":
    main()
