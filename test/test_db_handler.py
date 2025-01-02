import pytest
from app.db_handler import DatabaseHandler, DatabaseError
from app.models import Document, Base


@pytest.fixture
def db_handler():
    """Create a test database handler."""
    handler = DatabaseHandler("sqlite:///:memory:")
    # Override setup to skip PostgreSQL-specific operations
    handler.setup_database = lambda: Base.metadata.create_all(bind=handler.engine)
    return handler


def test_setup_database(db_handler):
    """Test database initialization."""
    db_handler.setup_database()

    # Check if tables were created
    with db_handler.get_session() as session:
        # Try to select from the documents table
        result = session.query(Document).all()
        assert len(result) == 0


def test_database_initialization_error():
    """Test that DatabaseError is raised when initialization fails."""
    with pytest.raises(DatabaseError) as exc_info:
        DatabaseHandler("invalid://database-url")
    assert "Failed to initialize database" in str(exc_info.value)
