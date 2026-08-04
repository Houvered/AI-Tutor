"""Tests for ingestion and retrieval (uses fake embeddings)."""

import unittest.mock as mock

from backend import config
from backend import db
from backend import rag


def _ingest(sample_file):
    return rag.ingest_file(sample_file, "notes.md")


class TestIngest:
    def test_ingest_stores_chunks(self, temp_db, sample_file, fake_llm):
        doc_id = _ingest(sample_file)
        count = db.query("SELECT COUNT(*) AS n FROM chunks")[0]["n"]
        assert count >= 2
        assert db.query("SELECT id FROM documents WHERE id = ?", (doc_id,))

    def test_ingest_empty_file_raises(self, temp_db, tmp_path, fake_llm):
        path = tmp_path / "empty.md"
        path.write_text("   ", encoding="utf-8")
        try:
            rag.ingest_file(str(path), "empty.md")
            raise AssertionError("expected ValueError")
        except ValueError:
            pass


class TestRetrieve:
    def test_retrieve_returns_top_matches(self, temp_db, sample_file, fake_llm):
        _ingest(sample_file)
        results = rag.retrieve("red black trees", top_k=3)
        assert results
        assert results[0]["filename"] == "notes.md"
        joined = " ".join(r["content"] for r in results).lower()
        assert "red black" in joined

    def test_retrieve_empty_database(self, temp_db, fake_llm):
        assert rag.retrieve("anything") == []

    def test_delete_document_removes_chunks(self, temp_db, sample_file, fake_llm):
        doc_id = _ingest(sample_file)
        rag.delete_document(doc_id)
        assert db.query("SELECT COUNT(*) AS n FROM chunks")[0]["n"] == 0


class TestChunkEncode:
    def test_roundtrip(self):
        original = [0.1, 0.2, -0.3, 1.0]
        decoded = rag._decode(rag._encode(original))
        # Floats are stored as float32, so compare approximately.
        for a, b in zip(decoded, original):
            assert abs(a - b) < 1e-5


class TestIngestFailure:
    def test_failed_embed_leaves_no_orphan(self, temp_db, sample_file):
        """If embedding fails, no document row should remain."""
        from backend.llm import llm as llm_client
        with mock.patch.object(llm_client, "embed", side_effect=RuntimeError("api down")):
            try:
                rag.ingest_file(sample_file, "notes.md")
                raise AssertionError("expected RuntimeError")
            except RuntimeError:
                pass
        docs = db.query("SELECT COUNT(*) AS n FROM documents")[0]["n"]
        chunks = db.query("SELECT COUNT(*) AS n FROM chunks")[0]["n"]
        assert docs == 0
        assert chunks == 0