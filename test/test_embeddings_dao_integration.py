"""Integration tests for EmbeddingsDAO using real PostgreSQL database with pgvector."""

import pytest
import os
from dotenv import load_dotenv
from app.embeddings_dao import EmbeddingsDAO
from app.models import Document, ProcessedDocument
from app.db_handler import DatabaseHandler

# Load environment variables from .env file
load_dotenv()

# Skip all tests in this module if TEST_DATABASE_URL is not set
pytestmark = pytest.mark.skipif(
    os.environ.get("TEST_DATABASE_URL") is None, reason="TEST_DATABASE_URL not set"
)


@pytest.fixture
def db_handler():
    """Create a database handler using real PostgreSQL."""
    handler = DatabaseHandler(os.environ["TEST_DATABASE_URL"])
    handler.setup_database()
    yield handler
    # Cleanup after tests
    with handler.get_session() as session:
        session.query(Document).delete()
        session.query(ProcessedDocument).delete()
        session.commit()


@pytest.fixture
def embeddings_dao(db_handler):
    """Create an embeddings DAO with real PostgreSQL database."""
    return EmbeddingsDAO(db_handler=db_handler)


def test_capital_of_france_query(embeddings_dao):
    """Test querying about French capital with unrelated content."""
    # Add some unrelated technical documents
    print("\nAdding test documents...")
    embeddings_dao.add_text(
        "The process of photosynthesis in plants involves chlorophyll "
        "capturing sunlight to convert CO2 and water into glucose.",
        document_metadata={"type": "biology"},
    )
    embeddings_dao.add_text(
        "Software development lifecycle includes requirements gathering, "
        "design, implementation, testing, deployment, and maintenance.",
        document_metadata={"type": "technology"},
    )
    embeddings_dao.add_text(
        "Cloud computing services offer scalability, flexibility, and "
        "cost-effectiveness for modern businesses.",
        document_metadata={"type": "technology"},
    )

    # Verify documents were added
    with embeddings_dao.db_handler.get_session() as session:
        doc_count = session.query(Document).count()
        print(f"\nNumber of documents in database: {doc_count}")

    # Query about capital of France
    print("\nQuerying for 'What is the capital of France?'...")
    results = embeddings_dao.query_embeddings("What is the capital of France?")

    # Print all results for inspection
    print("\nSimilarity scores for 'What is the capital of France?':")
    for match in results:
        print(f"\nText: {match.text}")
        print(f"Similarity: {match.similarity}")
        print(f"Metadata: {match.document_metadata}")

    # Verify results
    assert len(results) > 0, "Should find the documents"
    for match in results:
        # The similarity scores should be low since content is unrelated
        assert match.similarity < 0.5, (
            f"Expected low similarity (<0.5) for unrelated content, "
            f"but got {match.similarity} for text: {match.text}"
        )


def test_semantic_similarity_contrast(embeddings_dao):
    """Test semantic similarity by comparing related and unrelated content."""
    # Add some documents about cities and capitals
    embeddings_dao.add_text(
        "Paris is the capital city of France, known for the Eiffel Tower.",
        document_metadata={"type": "geography", "subject": "cities"},
    )
    embeddings_dao.add_text(
        "London is the capital of England and the United Kingdom.",
        document_metadata={"type": "geography", "subject": "cities"},
    )

    # Add some unrelated technical content
    embeddings_dao.add_text(
        "Python is a popular programming language known for its simplicity.",
        document_metadata={"type": "technology", "subject": "programming"},
    )

    # Query about French capital
    results = embeddings_dao.query_embeddings("What is the capital of France?")

    print("\nSimilarity scores for related vs unrelated content:")
    for match in results:
        print(f"\nText: {match.text}")
        print(f"Similarity: {match.similarity}")
        print(f"Metadata: {match.document_metadata}")

    # The Paris document should have highest similarity
    assert (
        results[0].text.lower().find("paris") >= 0
    ), "Most similar result should be about Paris"
    assert results[0].similarity > 0.6, "Related content should have high similarity"

    # Technical content should have much lower similarity
    tech_results = [r for r in results if r.document_metadata["type"] == "technology"]
    for result in tech_results:
        assert result.similarity < 0.2, (
            f"Unrelated technical content should have low similarity, "
            f"but got {result.similarity} for: {result.text}"
        )
