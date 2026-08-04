"""Tests for the LLM client parsing (no network needed)."""

import unittest.mock as mock

from backend.llm import GeminiClient


class TestGeminiEmbedShapes:
    """Gemini changed the embedding response shape between model generations.

    Older models (text-embedding-004) nest the values at
    embeddings[i].embedding.values. Newer models (gemini-embedding-001)
    put them directly at embeddings[i].values. Both must parse.
    """

    def _client_with_response(self, response):
        client = GeminiClient(api_key="test-key", base_url="https://example.test")
        with mock.patch.object(client, "_post", return_value=response):
            return client.embed(["hello"])

    def test_old_nested_shape(self):
        values = [0.1, 0.2, 0.3]
        out = self._client_with_response(
            {"embeddings": [{"embedding": {"values": values}}]}
        )
        assert out == [values]

    def test_new_flat_shape(self):
        values = [0.4, 0.5, 0.6]
        out = self._client_with_response({"embeddings": [{"values": values}]})
        assert out == [values]

    def test_unknown_shape_raises(self):
        client = GeminiClient(api_key="test-key", base_url="https://example.test")
        with mock.patch.object(client, "_post", return_value={"embeddings": [{"nope": 1}]}):
            from backend.llm import LLMError
            try:
                client.embed(["hello"])
                raise AssertionError("expected LLMError")
            except LLMError:
                pass
