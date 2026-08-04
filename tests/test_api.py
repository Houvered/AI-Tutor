"""Tests for the API endpoints (uses fake LLM)."""

import unittest.mock as mock

import pytest
from fastapi.testclient import TestClient

from backend import db
from backend.llm import LLMError
from backend.main import app


@pytest.fixture()
def client(temp_db, fake_llm):
    """A TestClient against the app with a fresh temp database."""
    with TestClient(app) as c:
        yield c


class TestUploadEndpoint:
    def test_upload_ok(self, client, tmp_path):
        path = tmp_path / "notes.md"
        path.write_text("study notes here", encoding="utf-8")
        with open(path, "rb") as f:
            res = client.post(
                "/api/documents/upload",
                files={"file": ("notes.md", f, "text/markdown")},
            )
        assert res.status_code == 200
        assert res.json()["filename"] == "notes.md"

    def test_upload_bad_extension(self, client, tmp_path):
        path = tmp_path / "notes.exe"
        path.write_text("x", encoding="utf-8")
        with open(path, "rb") as f:
            res = client.post(
                "/api/documents/upload",
                files={"file": ("notes.exe", f, "application/octet-stream")},
            )
        assert res.status_code == 400

    def test_upload_llm_down_returns_503(self, client, tmp_path):
        """When the LLM API fails, the upload should report a clean 503."""
        from backend.rag import llm as rag_llm

        path = tmp_path / "notes.md"
        path.write_text("study notes here", encoding="utf-8")
        with mock.patch.object(rag_llm, "embed", side_effect=LLMError("LLM API unreachable")):
            with open(path, "rb") as f:
                res = client.post(
                    "/api/documents/upload",
                    files={"file": ("notes.md", f, "text/markdown")},
                )
        assert res.status_code == 503
        # No orphan document should be left behind.
        assert db.query("SELECT COUNT(*) AS n FROM documents")[0]["n"] == 0


class TestAskEndpoint:
    def test_empty_message(self, client):
        res = client.post("/api/ask", json={"message": "   ", "history": []})
        assert res.status_code == 400


class TestHealth:
    def test_health(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"
