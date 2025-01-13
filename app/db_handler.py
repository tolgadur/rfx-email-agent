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
            print("Setting up database...")

            # Create vector extension in its own transaction
            with self.SessionLocal.begin() as session:
                print("Creating vector extension...")
                session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                print("Vector extension created successfully")

            # Create tables in a separate transaction
            with self.SessionLocal.begin() as session:
                print("Creating tables...")
                print(f"Tables to create: {Base.metadata.tables.keys()}")
                Base.metadata.create_all(bind=session.connection())
                print("Tables created successfully")

            print("Database setup completed successfully")
        except SQLAlchemyError as e:
            print(f"Database setup failed: {e}")
            raise DatabaseError(f"Failed to setup database: {e}")
        except Exception as e:
            print(f"Unexpected error during database setup: {e}")
            raise

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
