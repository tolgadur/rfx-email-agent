from dependency_injector import containers, providers
from app.email_handler import EmailHandler
from app.excel_handler import ExcelHandler
from app.pinecone_handler import PineconeHandler
from app.template_handler import TemplateHandler
from app.db_handler import DatabaseHandler


class Container(containers.DeclarativeContainer):
    """IoC container of handlers."""

    config = providers.Configuration()

    # Load configuration from environment variables
    config.email.from_env("EMAIL", required=True)
    config.password.from_env("PASSWORD", required=True)
    config.database_url.from_env("DATABASE_URL", required=True)
    config.pinecone_api_key.from_env("PINECONE_API_KEY", required=True)

    # Email server settings with defaults
    config.imap_server.from_env("IMAP_SERVER", default="imap.gmail.com")
    config.smtp_server.from_env("SMTP_SERVER", default="smtp.gmail.com")

    # Stateful handlers (Singletons)
    db_handler = providers.Singleton(
        DatabaseHandler,
        database_url=config.database_url,
    )

    email_handler = providers.Singleton(
        EmailHandler,
        email=config.email,
        password=config.password,
        imap_server=config.imap_server,
        smtp_server=config.smtp_server,
    )

    pinecone_handler = providers.Singleton(
        PineconeHandler,
        api_key=config.pinecone_api_key,
    )

    # Stateless handlers (Factory)
    template_handler = providers.Factory(TemplateHandler)
    excel_handler = providers.Factory(
        ExcelHandler,
        pinecone_handler=pinecone_handler,
    )
