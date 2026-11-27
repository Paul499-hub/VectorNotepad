import sys
from types import ModuleType

import numpy as np
import pytest
from qdrant_client import QdrantClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ------- LAUNCH 
# Check test_setup.md under /tests for test env setup
# .\.venv-tests\Scripts\python.exe -m pytest tests/test_note_references.py -v

# ------------ TEST INFO 
# The tests check multiple Qdrant points referencing one SQLite note.
# Each test starts with two SQLite notes: one has three vectors—the original plus two variants—and the other has one vector.
# 1. Search
#    - All four points have unique IDs.
#    - Results contain each SQLite note only once.
#    - Each note receives its highest matching vector score.
#    - Results are sorted by score descending.
#    - Returned text comes from SQLite, not the matching variant.
# 2. Update
#    - All three old vectors for the edited note are removed.
#    - One replacement vector is created, matching your current implementation.
#    - The SQLite note keeps its ID and receives the updated text.
#    - The other note’s vector remains unchanged.
# 3. Delete
#    - The selected SQLite note and all three associated vectors disappear.
#    - The other note and its vector remain intact.
# The tests use temporary storage and predictable embeddings. They check storage relationships and CRUD behavior—not AI search quality, the frontend, or recovery from connection failures.

@pytest.fixture
def storage(monkeypatch, tmp_path):
    # Ensure imports cannot initialize the real SQLite database.
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "notes.sqlite"))
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("QDRANT_PORT", "6333")
    monkeypatch.setenv("QDRANT_VECTOR_LENGTH", "3")

    # EmbeddingService imports this module at startup.
    # The fixture uses fake embeddings and exercises vector-only search.
    registry = ModuleType("app.ai_models.model_registry")
    registry.embedding_model = None
    registry.reranker_model = None
    monkeypatch.setitem(sys.modules, registry.__name__, registry)

    from app.core.config import settings
    from app.db.models import NoteORM
    from app.schemas.embedding import F_EmbedTextOut
    from app.services import qdrant as qdrant_module
    from app.services import sqlite as sqlite_module
    from app.services.storage import StorageService

    monkeypatch.setattr(settings, "embedding_model", "test-model")
    monkeypatch.setattr(settings, "qdrant_vector_length", 3)

    vectors = {
        "Other note": [0.8, 0.6, 0.0],
        "Original note": [0.6, 0.8, 0.0],
        "First variant": [1.0, 0.0, 0.0],
        "Second variant": [0.9, 0.0, 0.435889894],
        "Updated note": [0.0, 1.0, 0.0],
        "query": [1.0, 0.0, 0.0],
    }

    class TestEmbeddingService:
        def embed_text(self, text):
            return F_EmbedTextOut(
                status="ok",
                vector=vectors[text],
                vector_size=3,
            )

    engine = create_engine("sqlite://")
    NoteORM.metadata.create_all(engine)
    monkeypatch.setattr(
        sqlite_module,
        "SessionLocal",
        sessionmaker(bind=engine),
    )

    client = QdrantClient(":memory:")
    monkeypatch.setattr(
        qdrant_module,
        "QdrantClient",
        lambda **kwargs: client,
    )

    qdrant = qdrant_module.QdrantService(
        host="localhost",
        port=6333,
        embedding_svc=TestEmbeddingService(),
    )

    try:
        qdrant.create_collection_default()
        yield StorageService(
            qdrant_svc=qdrant,
            sqlite_svc=sqlite_module.SQLiteService(),
            reranking_svc=None,
        )
    finally:
        client.close()
        engine.dispose()


def get_points(storage):
    points, next_offset = storage.qdrant_svc.client.scroll(
        collection_name="notes",
        limit=100,
        with_payload=True,
    )
    # These tests deliberately contain fewer than 100 points.
    assert next_offset is None
    return points


@pytest.fixture
def linked_notes(storage):
    # Create the lower-scoring note first, so IDs and ranking differ.
    storage.save_note("Other note")
    storage.save_note("Original note")

    notes = storage.sqlite_svc.find_note_contains("")
    ids = {note["text"]: note["id"] for note in notes}
    note_id = ids["Original note"]
    other_id = ids["Other note"]

    storage.qdrant_svc.store_vector("First variant", note_id)
    storage.qdrant_svc.store_vector("Second variant", note_id)

    return storage, note_id, other_id


def test_search_groups_points_and_uses_best_score(linked_notes):
    from app.schemas.embedding import IN_SimilaritySearchRequest

    storage, note_id, other_id = linked_notes
    points = get_points(storage)

    # Four distinct points, but only two SQLite notes.
    assert len(points) == 4
    assert len({point.id for point in points}) == 4
    assert storage.sqlite_svc.count_notes() == 2
    assert sum(
        point.payload["sqlite_note_id"] == note_id
        for point in points
    ) == 3

    results = storage.vector_search_note(
        IN_SimilaritySearchRequest(text="query", point_limit=10, rerank=False)
    )

    assert [note["id"] for note in results] == [note_id, other_id]
    assert results[0]["score"] == pytest.approx(1.0)
    assert results[1]["score"] == pytest.approx(0.8)
    assert all("reranked_score" not in note for note in results)

    # Display the source text, not the winning variant's text.
    assert results[0]["text"] == "Original note"
    assert results[0]["html_md"] == "<p>Original note</p>"


def test_batched_chunk_reranking_keeps_each_notes_best_score(linked_notes, monkeypatch):
    from app.schemas.embedding import IN_SimilaritySearchRequest

    storage, note_id, other_id = linked_notes
    original_text = "a" * 448 + "b" * 448 + "c" * 100
    other_text = "d" * 448 + "e" * 100
    storage.sqlite_svc.update_note(note_id, original_text)
    storage.sqlite_svc.update_note(other_id, other_text)

    chunk_scores = {
        original_text[:512]: 0.1,
        original_text[448:960]: 0.6,
        original_text[896:]: 0.2,
        other_text[:512]: 0.9,
        other_text[448:]: 0.4,
    }
    calls = []

    class TestReranker:
        def rerank(self, query, chunks):
            calls.append((query, chunks))
            return np.array([chunk_scores[chunk] for chunk in chunks], dtype=np.float32)

    monkeypatch.setattr(storage, "reranking_svc", TestReranker())

    results = storage.vector_search_note_chunks_batched(
        IN_SimilaritySearchRequest(text="query", point_limit=10, rerank=True)
    )

    assert len(calls) == 1
    query, chunks = calls[0]
    assert query == "query"
    assert sorted(chunks) == sorted(chunk_scores)
    assert [note["id"] for note in results] == [other_id, note_id]
    assert [note["reranked_score"] for note in results] == pytest.approx([0.9, 0.6])
    assert all(type(note["reranked_score"]) is float for note in results)


def test_update_replaces_all_related_points(linked_notes):
    storage, note_id, other_id = linked_notes
    before = get_points(storage)

    old_point_ids = {
        point.id
        for point in before
        if point.payload["sqlite_note_id"] == note_id
    }
    other_point_ids = {
        point.id
        for point in before
        if point.payload["sqlite_note_id"] == other_id
    }

    storage.update_note(note_id, "Updated note")

    after = get_points(storage)
    updated_points = [
        point for point in after
        if point.payload["sqlite_note_id"] == note_id
    ]

    # Current update implementation creates one replacement vector.
    assert len(updated_points) == 1
    assert old_point_ids.isdisjoint({point.id for point in after})
    assert {
        point.id for point in after
        if point.payload["sqlite_note_id"] == other_id
    } == other_point_ids

    note = storage.sqlite_svc.get_by_id(note_id)
    assert note["id"] == note_id
    assert note["text"] == "Updated note"
    assert storage.sqlite_svc.count_notes() == 2


def test_delete_removes_all_related_points_only(linked_notes):
    storage, note_id, other_id = linked_notes
    other_point_ids = {
        point.id
        for point in get_points(storage)
        if point.payload["sqlite_note_id"] == other_id
    }

    storage.del_note(note_id)

    remaining = get_points(storage)
    assert {point.id for point in remaining} == other_point_ids
    assert all(
        point.payload["sqlite_note_id"] == other_id
        for point in remaining
    )

    assert storage.sqlite_svc.find_notes_by_ids([note_id]) == []
    assert storage.sqlite_svc.get_by_id(other_id)["text"] == "Other note"
    assert storage.sqlite_svc.count_notes() == 1
