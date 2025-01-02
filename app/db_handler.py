from typing import List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.models import Base, Document


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

    def setup_database(self, seed: bool = True) -> None:
        """Initialize database schema and optionally seed with test data.

        Args:
            seed: Whether to seed the database with test data
        """
        try:
            # Create vector extension first
            with self.SessionLocal.begin() as session:
                session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

            # Then create tables
            Base.metadata.create_all(bind=self.engine)
            print("Database setup completed successfully")

            if seed:
                self.seed_database()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to setup database: {e}")

    def seed_database(self) -> None:
        """Seed the database with test data if it's empty."""
        try:
            with self.SessionLocal.begin() as session:
                # Check if we already have data
                if session.query(Document).first() is not None:
                    print("Database already contains data, skipping seed")
                    return

                # Add test documents
                test_docs = [
                    Document(
                        text="How to make a delicious pasta carbonara",
                        embedding=self._create_test_embedding(),
                        document_metadata={
                            "type": "recipe",
                            "cuisine": "italian",
                            "difficulty": "medium",
                        },
                    ),
                    # Add more test documents here as needed
                ]

                session.add_all(test_docs)
                print("Database seeded successfully")
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to seed database: {e}")

    def get_session(self):
        """Get a database session.

        Returns:
            A SQLAlchemy session
        """
        return self.SessionLocal()

    @staticmethod
    def _create_test_embedding(dim: int = 1536) -> List[float]:
        """Create a test embedding vector.

        Args:
            dim: Dimension of the embedding vector

        Returns:
            A list of floats representing a test embedding
        """
        return [0.1] * dim

    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self, "engine"):
            self.engine.dispose()
