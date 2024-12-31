import pytest
from app.db_handler import DatabaseHandler, DatabaseError
from app.models import Document, Base


@pytest.fixture
def db_handler():
    """Create a test database handler."""
    handler = DatabaseHandler("sqlite:///:memory:")
    # Override setup to skip PostgreSQL-specific operations
    handler.setup_database = lambda seed=True: (
        Base.metadata.create_all(bind=handler.engine),
        handler.seed_database() if seed else None,
    )[0]
    return handler


def test_setup_database(db_handler):
    """Test database initialization."""
    db_handler.setup_database(seed=False)

    # Check if tables were created
    with db_handler.get_session() as session:
        # Try to select from the documents table
        result = session.query(Document).all()
        assert len(result) == 0


def test_seed_database(db_handler):
    """Test database seeding."""
    db_handler.setup_database(seed=True)

    # Check if seed data was inserted
    with db_handler.get_session() as session:
        result = session.query(Document).all()
        assert len(result) == 1

        doc = result[0]
        assert doc.text == "How to make a delicious pasta carbonara"
        assert len(doc.embedding) == 1536
        assert doc.document_metadata == {
            "type": "recipe",
            "cuisine": "italian",
            "difficulty": "medium",
        }


def test_seed_database_idempotent(db_handler):
    """Test that seeding is idempotent (won't add duplicates)."""
    # Seed twice
    db_handler.setup_database(seed=True)
    db_handler.seed_database()

    # Check that we still only have one document
    with db_handler.get_session() as session:
        result = session.query(Document).all()
        assert len(result) == 1


def test_database_initialization_error():
    """Test that DatabaseError is raised when initialization fails."""
    with pytest.raises(DatabaseError) as exc_info:
        DatabaseHandler("invalid://database-url")
    assert "Failed to initialize database" in str(exc_info.value)
