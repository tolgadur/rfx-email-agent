"""Integration tests for EmbeddingsDAO using real PostgreSQL database with pgvector."""

import pytest
from app.embeddings_dao import EmbeddingsDAO
from app.models import Document, Embedding


@pytest.fixture
def embeddings_dao(db_handler):
    """Create an embeddings DAO with real PostgreSQL database."""
    return EmbeddingsDAO(db_handler=db_handler)


def test_capital_of_france_query(embeddings_dao):
    """Test querying about French capital with unrelated content."""
    with embeddings_dao.db_handler.get_session() as session:
        # Create and commit the test document first
        doc = Document(filepath="test.txt", processed=True)
        session.add(doc)
        session.flush()
        doc_id = doc.id

        # Add some unrelated technical documents
        embeddings_dao.add_text(
            "The process of photosynthesis in plants involves chlorophyll "
            "capturing sunlight to convert CO2 and water into glucose.",
            document_id=doc_id,
            embedding_metadata={"type": "biology"},
            session=session,
        )
        embeddings_dao.add_text(
            "Software development lifecycle includes requirements gathering, "
            "design, implementation, testing, deployment, and maintenance.",
            document_id=doc_id,
            embedding_metadata={"type": "technology"},
            session=session,
        )
        embeddings_dao.add_text(
            "Cloud computing services offer scalability, flexibility, and "
            "cost-effectiveness for modern businesses.",
            document_id=doc_id,
            embedding_metadata={"type": "technology"},
            session=session,
        )

        session.commit()

    # Verify embedding count
    with embeddings_dao.db_handler.get_session() as session:
        embedding_count = session.query(Embedding).count()
        assert embedding_count == 3, "Should have exactly 3 embeddings in database"

    # Query about capital of France
    results = embeddings_dao.query_embeddings("What is the capital of France?")

    # Since the content is unrelated and below threshold, we expect no results
    assert len(results) == 0, "Should not find any documents since they are unrelated"


def test_semantic_similarity_contrast(embeddings_dao):
    """Test semantic similarity by comparing related and unrelated content."""
    with embeddings_dao.db_handler.get_session() as session:
        doc = Document(filepath="test_semantic.txt", processed=True)
        session.add(doc)
        session.flush()
        doc_id = doc.id

        # Add some documents about cities and capitals
        embeddings_dao.add_text(
            "Paris is the capital city of France, known for the Eiffel Tower.",
            document_id=doc_id,
            embedding_metadata={"type": "geography", "subject": "cities"},
            session=session,
        )
        embeddings_dao.add_text(
            "London is the capital of England and the United Kingdom.",
            document_id=doc_id,
            embedding_metadata={"type": "geography", "subject": "cities"},
            session=session,
        )

        # Add some unrelated technical content
        embeddings_dao.add_text(
            "Python is a popular programming language known for its simplicity.",
            document_id=doc_id,
            embedding_metadata={"type": "technology", "subject": "programming"},
            session=session,
        )
        session.commit()

    # Verify embedding count
    with embeddings_dao.db_handler.get_session() as session:
        embedding_count = session.query(Embedding).count()
        assert embedding_count == 3, "Should have exactly 3 embeddings in database"

    # Query about French capital
    results = embeddings_dao.query_embeddings("What is the capital of France?")

    # The Paris document should have highest similarity
    assert (
        results[0].text.lower().find("paris") >= 0
    ), "Most similar result should be about Paris"
    assert results[0].similarity > 0.6, "Related content should have high similarity"

    # Technical content should have much lower similarity
    tech_results = [r for r in results if r.embedding_metadata["type"] == "technology"]
    for result in tech_results:
        assert result.similarity < 0.2, (
            f"Unrelated technical content should have low similarity, "
            f"but got {result.similarity} for: {result.text}"
        )
