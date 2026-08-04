# Design Decisions

Why this project looks the way it does. Each decision lists the problem, what we
chose, and why.

## 1. Use a hosted LLM API instead of a local model

- Problem: The first version used Ollama plus a 3B model locally. This needed a
  heavy install and did not scale.
- Choice: Call any OpenAI-compatible hosted API for both chat and embeddings.
- Why: No GPU, no large download, works on any small server. The provider can be
  swapped by changing a few config values.

## 2. One web server instead of many services

- Problem: The first version ran Docker with Postgres, Redis, Qdrant, and Ollama.
  Many moving parts to keep running.
- Choice: One FastAPI process serves the web page, the API, and uses one SQLite file.
- Why: Simplest setup that works. Easy to run and easy to deploy. One command to start.

## 3. SQLite instead of a separate database server

- Problem: Postgres added install and connection complexity.
- Choice: SQLite, one file, no server to manage.
- Why: Perfectly fine for one user and thousands of chunks. Nothing else needs it.

## 4. No vector database

- Problem: The first version used Qdrant for embeddings.
- Choice: Store chunks in SQLite and search with pure Python cosine similarity.
- Why: At personal scale the speed is the same. It removes a whole service and its
  client library. No numpy needed.

## 5. No user accounts

- Problem: Accounts add work with no benefit for a single user.
- Choice: No login.
- Why: This is a personal app. A small optional bearer token can be added later if
  the app is ever made public.

## 6. Keep only SM-2, drop IRT and BKT

- Problem: The first version had a full psychometric engine (Item Response Theory,
  Bayesian Knowledge Tracing, SuperMemo SM-2).
- Choice: Keep only SM-2 spaced repetition.
- Why: For a study tool, correct or wrong plus spaced repetition gives most of the
  value. The other two added a lot of code with little benefit for one user.

## 7. No event system or middleware stack

- Problem: The first version had domain events, request logging middleware, rate
  limiting, and a repository layer.
- Choice: Plain function calls, plain SQLite helpers.
- Why: None of that helps a small app. It hid the flow instead of making it clear.

## 8. No background workers (Celery)

- Problem: The first version queued ingestion with Celery.
- Choice: Do ingestion synchronously in the request.
- Why: For personal files, parsing is fast enough. It removes a queue and a result
  backend.

## 9. All LLM calls in one file

- Choice: `backend/llm.py` is the only module that talks to the outside provider.
- Why: Changing provider or adding retry logic touches one small file and config.

## 10. Small, many commits on feature branches

- Choice: Work in branches, make many small commits, let the owner merge manually.
- Why: Easy to review. Easy to see what changed and why. Matches how the owner works.

## Rejected alternatives

- Keyword search only (no embeddings): simpler, but grounded answers would be much
  worse. The embeddings call is cheap and worth it.
- Streaming answers: nice but adds frontend complexity. Can be added later.
- Accounts and multi-user: rejected for now, see decision 5.