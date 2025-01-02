from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.models import Base


class DatabaseError(Exception):
    """Base exception for database operations."""

    pass


class DatabaseHandler:
    def __init__(self, database_url: str):
        """Initialize database handler with connection URL.

        Args:
            database_url: Database URL in format:
                postgresql://user:password@host:port/database
        """
        # Ensure we use postgresql:// instead of postgres://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        try:
            self.engine = create_engine(database_url)
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to initialize database: {e}")

    def setup_database(self) -> None:
        """Initialize database schema."""
        try:
            # Create vector extension first
            with self.SessionLocal.begin() as session:
                session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

            # Then create tables
            Base.metadata.create_all(bind=self.engine)
            print("Database setup completed successfully")
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to setup database: {e}")

    def get_session(self):
        """Get a database session.

        Returns:
            A SQLAlchemy session
        """
        return self.SessionLocal()

    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self, "engine"):
            self.engine.dispose()
