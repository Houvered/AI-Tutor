# Architecture

How the project is put together, in plain words.

## Big picture

The project is one Python web server. That server does three jobs:

1. Serves the web page (the React app).
2. Provides the API that the web page talks to.
3. Stores all data in one SQLite file.

The only outside service is the LLM API. The server calls it for two things:

- Turning text into numbers (embeddings), used for search.
- Writing answers and quiz questions (chat).

There is no other infrastructure. No database server, no message queue, no
background workers, no containers.

```
Browser
   |
   v
FastAPI server (serves React app + API)
   |                         |
   v                         v
SQLite file            LLM API (hosted, OpenAI-compatible)
```

## The three layers of the backend

The backend code lives in `backend/`. It is small on purpose.

### 1. API layer (main.py)

`main.py` is the entrypoint. It creates the FastAPI app and defines all endpoints.
It also serves the built frontend files from `frontend/dist`.

The endpoints are grouped by feature:

- Documents: upload, list, delete.
- Ask: ask a question and get a grounded answer.
- Quiz: generate a quiz, evaluate an answer.
- Review: get due topics, grade a review.
- Health: check the app and the LLM connection.

### 2. Logic layer

- `rag.py` - ingestion and search. Turns files into chunks, stores them, finds the
  best matching chunks for a question.
- `tutor.py` - grounded answer generation. Builds a prompt from retrieved chunks
  and asks the chat model to answer only from them, with citations.
- `quiz.py` - quiz generation and grading.
- `revision.py` - spaced repetition math (SM-2).
- `llm.py` - all calls to the LLM API live here. This is the only file that talks
  to the outside provider, so changing provider only touches this file and config.
  Two providers are supported: any OpenAI-compatible API and Google Gemini.
- `config.py` - reads settings from environment variables.
- `db.py` - opens the SQLite database and provides small helper functions.

### 3. Parsers

`backend/parsers/` reads different file types and returns plain text:

- PDF via PyMuPDF.
- DOCX via python-docx.
- PPTX via python-pptx.
- TXT and Markdown read directly.

## The frontend

The frontend is a React app in `frontend/`. It has three tabs:

- Notes: upload files and see what you have uploaded.
- Ask: chat with your material, answers include citations and a mini quiz.
- Review: spaced repetition cards that are due today.

The frontend is a plain React app with no routing library and no state library.
It talks to the backend through `src/api.ts`. The backend serves the built
frontend files from `frontend/dist` when they exist, so one address serves
both the UI and the API.

## How a question flows through the system

1. The user types a question in the Ask tab.
2. The browser sends it to `POST /api/ask`.
3. The server embeds the question (turns it into numbers).
4. The server compares those numbers with every stored chunk using cosine
   similarity (pure Python, no vector database).
5. The best 5 chunks are placed into a prompt as context.
6. The chat model answers using only that context, with citations.
7. The answer, the citations, and a mini quiz question come back to the browser.

## How an upload flows through the system

1. The browser uploads a file to `POST /api/documents/upload`.
2. The server saves the file and parses it into plain text.
3. The text is split into chunks of about 800 characters, with some overlap.
4. Each chunk is embedded (turned into numbers) through the LLM API.
5. The chunk text and its numbers are stored in SQLite.
6. The file is now searchable.

## Storage

Everything is in one SQLite file. Three tables:

- `documents` - one row per uploaded file.
- `chunks` - the pieces of text and their embedding numbers.
- `revisions` - spaced repetition state per topic.

## Design rules

- One file does one job.
- No dead code. If a module does not earn its place, remove it.
- The LLM provider is the only external dependency.
- Everything must run with one command after setup.