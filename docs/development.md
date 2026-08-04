# Development Guide

How to work on this project, aimed at developers. Written for people who will
continue the work after the owner.

## Project layout

```
backend/
  main.py        - FastAPI app, all endpoints, serves the frontend.
  config.py      - settings from environment variables.
  db.py          - SQLite connection and helpers.
  llm.py         - all calls to the LLM API.
  rag.py         - ingestion and retrieval.
  quiz.py        - quiz generation and grading.
  revision.py    - SM-2 spaced repetition.
  parsers/       - one parser per file type.
  requirements.txt
frontend/
  src/App.tsx    - the whole UI (three tabs).
  src/api.ts     - how the UI talks to the backend.
  src/styles.css - all styling.
docs/            - this documentation.
```

## Run the app for development

Backend only, with auto reload:

```
uvicorn backend.main:app --reload --port 8000
```

Frontend with hot reload (separate terminal):

```
cd frontend
npm run dev
```

During development the frontend runs on its own address (usually port 5173) and
forwards API calls to the backend on port 8000. See `vite.config.ts` for the proxy
setup.

For a production-like test, build the frontend once:

```
cd frontend
npm run build
```

The backend serves the built files automatically.

## Working on branches

The owner works feature by feature:

- Create a branch from main: `git checkout -b feature/your-feature`
- Make many small commits with clear messages.
- Do not merge. The owner merges manually after review.

## Code style

- Python: follow PEP 8. Keep functions small and clear. Use type hints.
- TypeScript/React: simple and plain. No routing or state libraries.
- No em dashes in code, docs, or commit messages. Use a hyphen or rewrite.
- No emoji in code or docs.
- Simple English in comments and docs. Write for a person who is new to the repo.

## Adding a new provider

The project uses the OpenAI chat format. To add a provider:

1. Find the base URL and model names of the provider.
2. Put them in the `.env` file.
3. No code change is needed if the provider follows the OpenAI format.

If a provider needs a different format, change only `backend/llm.py`.

## Adding a new file type

1. Create a parser in `backend/parsers/`.
2. Every parser exposes one function that takes a file path and returns text.
3. Register the parser for its file extension in the same folder (see `parsers/__init__.py`).
4. Add the extension to `ALLOWED_EXTENSIONS` in `backend/config.py`.

## Running the tests

The project keeps a proper pytest suite. Run it from the project root:

```
python -m pytest tests/
```

Install the test tools first:

```
pip install -r backend/requirements-dev.txt
```

The tests use fake embeddings and a temporary database, so they never need an
LLM API key and never touch real data.

Test areas:

- test_parsing.py - file parsing and chunking.
- test_rag.py - ingestion, retrieval, and vector storage.
- test_chat.py - grounded answers and fallbacks.
- test_quiz.py - quiz JSON parsing, generation, and evaluation.
- test_revision.py - SM-2 spacing and scheduling.

## Things that need the owner

- The LLM API key. It lives in `.env` which is never committed.
- Merging branches. The owner does this manually after review.
- Deploying. See `docs/setup.md`.