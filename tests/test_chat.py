"""Tests for the grounded chat flow."""

import unittest.mock as mock

from backend import rag
from backend.tutor import answer_question


def _ingest(sample_file):
    rag.ingest_file(sample_file, "notes.md")


class TestAnswerQuestion:
    def test_grounded_answer_with_citations(self, temp_db, sample_file, fake_llm):
        _ingest(sample_file)
        with mock.patch("backend.tutor.llm.chat", return_value="Grounded answer. [1]"):
            result = answer_question("what is a binary search tree", [])
        assert result["answer"]
        assert result["citations"]
        assert result["citations"][0]["filename"] == "notes.md"

    def test_history_is_accepted(self, temp_db, sample_file, fake_llm):
        _ingest(sample_file)
        history = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
        with mock.patch("backend.tutor.llm.chat", return_value="ok"):
            result = answer_question("explain more", history)
        assert result["answer"]

    def test_no_material_message(self, temp_db, fake_llm):
        result = answer_question("anything", [])
        assert "upload" in result["answer"].lower() or "matched" in result["answer"].lower()

    def test_llm_down_falls_back_to_material(self, temp_db, sample_file, fake_llm):
        _ingest(sample_file)
        with mock.patch("backend.tutor.llm.chat", side_effect=RuntimeError("down")):
            result = answer_question("red black trees", [])
        assert "available" in result["answer"].lower()