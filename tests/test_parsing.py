"""Tests for chunking and file parsing."""

from backend import parsers
from backend.rag import chunk_text


class TestChunkText:
    def test_short_text_is_one_chunk(self):
        assert chunk_text("short") == ["short"]

    def test_empty_text_returns_no_chunks(self):
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_long_text_breaks_into_chunks(self):
        text = ("word " * 500) + "."
        chunks = chunk_text(text)
        assert len(chunks) >= 2
        # No chunk should exceed the configured size by much.
        assert all(len(c) <= 850 for c in chunks)
        # Rebuilding chunks should roughly recover the original content.
        assert "word" in " ".join(chunks)

    def test_chunks_are_not_empty(self):
        text = "sentence one. " * 300
        chunks = chunk_text(text)
        assert all(c.strip() for c in chunks)


class TestParseFile:
    def test_txt_parsing(self, tmp_path):
        path = tmp_path / "notes.txt"
        path.write_text("hello world", encoding="utf-8")
        assert "hello world" in parsers.parse_file(str(path))

    def test_markdown_parsing(self, tmp_path):
        path = tmp_path / "notes.md"
        path.write_text("# Title\n\nBody text.", encoding="utf-8")
        text = parsers.parse_file(str(path))
        assert "Title" in text and "Body text" in text

    def test_unsupported_extension_raises(self, tmp_path):
        path = tmp_path / "notes.exe"
        path.write_text("x", encoding="utf-8")
        try:
            parsers.parse_file(str(path))
            raise AssertionError("expected ValueError")
        except ValueError:
            pass
