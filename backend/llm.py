"""LLM API clients.

The only module that talks to the outside AI provider. Everything else in the
app calls these functions. Two providers are supported, chosen by the
LLM_PROVIDER config value:

  "openai" - any OpenAI-compatible API (OpenAI, DeepSeek, Groq, OpenRouter).
  "gemini" - Google Gemini API.

Each provider implements the same interface:

  embed(texts) - turn text into numbers (for search).
  chat(system, user) - get a text answer from the chat model.
  ping() - check the provider is reachable.
"""

from typing import Any, Protocol

import httpx

from backend import config


class LLMError(Exception):
    """Raised when the LLM API cannot be reached or returns an error."""


class LLMClient(Protocol):
    """What every provider client must support."""

    def embed(self, texts: list[str]) -> list[list[float]]: ...

    def embed_one(self, text: str) -> list[float]: ...

    def chat(self, system: str, user: str) -> str: ...

    def ping(self) -> bool: ...


class OpenAICompatibleClient:
    """Client for any OpenAI-compatible API."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.base_url = (base_url or config.LLM_BASE_URL).rstrip("/")
        self.api_key = api_key or config.LLM_API_KEY
        self.timeout = timeout or config.LLM_TIMEOUT_SECONDS
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise LLMError("LLM_API_KEY is not set. See docs/setup.md.")
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/{path}",
                    headers=self._headers,
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM API unreachable: {exc}") from exc

        if resp.status_code >= 400:
            hint = " Check the API key and base URL in your .env file." if resp.status_code in (401, 403) else ""
            raise LLMError(
                f"LLM API returned status {resp.status_code}: {resp.text[:300]}{hint}"
            )
        return resp.json()

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        body = self._post(
            "embeddings",
            {"model": config.EMBED_MODEL, "input": texts},
        )
        ordered = sorted(body["data"], key=lambda item: item["index"])
        return [item["embedding"] for item in ordered]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]

    def chat(self, system: str, user: str) -> str:
        body = self._post(
            "chat/completions",
            {
                "model": config.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
            },
        )
        try:
            return body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError) as exc:
            raise LLMError(f"Unexpected LLM response shape: {body}") from exc

    def ping(self) -> bool:
        try:
            self.embed_one("ping")
            return True
        except LLMError:
            return False


class GeminiClient:
    """Client for the Google Gemini API."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.base_url = (base_url or config.GEMINI_BASE_URL).rstrip("/")
        self.api_key = api_key or config.GEMINI_API_KEY
        self.timeout = timeout or config.LLM_TIMEOUT_SECONDS
        self._headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise LLMError("GEMINI_API_KEY is not set. See docs/setup.md.")
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/{path}",
                    headers=self._headers,
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise LLMError(f"Gemini API unreachable: {exc}") from exc

        if resp.status_code >= 400:
            hint = " Check the API key in your .env file." if resp.status_code in (401, 403) else ""
            raise LLMError(
                f"Gemini API returned status {resp.status_code}: {resp.text[:300]}{hint}"
            )
        return resp.json()

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        body = self._post(
            f"models/{config.GEMINI_EMBED_MODEL}:batchEmbedContents",
            {
                "requests": [
                    {
                        "model": f"models/{config.GEMINI_EMBED_MODEL}",
                        "content": {"parts": [{"text": text}]},
                    }
                    for text in texts
                ]
            },
        )
        result = []
        for item in body["embeddings"]:
            # Newer models (gemini-embedding-001 and newer) return the values
            # at item["values"]; older models nested them at
            # item["embedding"]["values"]. Accept both.
            if "values" in item:
                result.append(item["values"])
            elif "embedding" in item and "values" in item["embedding"]:
                result.append(item["embedding"]["values"])
            else:
                raise LLMError(f"Unexpected Gemini embedding shape: {item}")
        return result

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]

    def chat(self, system: str, user: str) -> str:
        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": user}]}],
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        body = self._post(
            f"models/{config.GEMINI_MODEL}:generateContent",
            payload,
        )
        try:
            parts = body["candidates"][0]["content"]["parts"]
            return "".join(part.get("text", "") for part in parts).strip()
        except (KeyError, IndexError, AttributeError) as exc:
            raise LLMError(f"Unexpected Gemini response shape: {body}") from exc

    def ping(self) -> bool:
        try:
            self.embed_one("ping")
            return True
        except LLMError:
            return False


def get_client() -> LLMClient:
    """Return the client for the configured provider."""
    provider = config.LLM_PROVIDER.lower()
    if provider == "gemini":
        return GeminiClient()
    return OpenAICompatibleClient()


# Shared client used across the app.
llm = get_client()
