"""Ingestion and retrieval.

Two jobs:

1. ingest_file - parse a file, split it into chunks, embed every chunk, store
   the chunks and their vectors in SQLite.
2. retrieve - embed a query, compare with all stored chunks using cosine
   similarity, return the best matches with citations.
"""

import math
import uuid

from backend import config
from backend import db
from backend import parsers
from backend.llm import llm


def chunk_text(text: str, size: int | None = None, overlap: int | None = None) -> list[str]:
    """Split text into overlapping chunks of roughly `size` characters.

    Chunks break on paragraph or sentence boundaries when possible so a chunk
    does not cut a sentence in half.
    """
    size = size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))

        # Back up to a sentence or paragraph boundary if we are close to one.
        if end < len(text):
            cut = max(text.rfind(". ", start + size // 2, end), text.rfind("\n", start + size // 2, end))
            if cut != -1:
                end = cut + 1

        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)

    return [c for c in chunks if c]


def ingest_file(file_path: str, filename: str) -> str:
    """Parse, chunk, embed, and store a file. Returns the new document id.

    If embedding fails partway, any partial rows are removed so the database
    never ends up with an empty document.
    """
    raw_text = parsers.parse_file(file_path)
    if not raw_text.strip():
        raise ValueError("The file has no readable text.")

    doc_id = str(uuid.uuid4())
    chunks = chunk_text(raw_text)
    try:
        for i in range(0, len(chunks), config.EMBED_BATCH_SIZE):
            batch = chunks[i : i + config.EMBED_BATCH_SIZE]
            vectors = llm.embed(batch)
            for chunk, vector in zip(batch, vectors):
                db.execute(
                    "INSERT INTO chunks (document_id, content, embedding) VALUES (?, ?, ?)",
                    (doc_id, chunk, _encode(vector)),
                )
        db.execute(
            "INSERT INTO documents (id, filename, created_at) VALUES (?, ?, ?)",
            (doc_id, filename, db.now()),
        )
    except Exception:
        # Remove partial rows so no empty document survives a failed ingest.
        db.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
        db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        raise
    return doc_id


def delete_document(doc_id: str) -> None:
    """Remove a document and all its chunks."""
    db.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
    db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))


def _encode(vector: list[float]) -> bytes:
    """Pack floats into bytes for storage."""
    import struct

    return struct.pack(f"{len(vector)}f", *vector)


def _decode(blob: bytes) -> list[float]:
    """Unpack stored bytes back into floats."""
    import struct

    return list(struct.unpack(f"{len(blob) // 4}f", blob))


def _cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors, both assumed normalized."""
    return sum(x * y for x, y in zip(a, b))


def retrieve(query: str, top_k: int | None = None) -> list[dict]:
    """Return the best matching chunks for a query.

    Each result has: content, document_id, filename, score.
    """
    top_k = top_k or config.TOP_K
    query_vector = llm.embed_one(query)

    rows = db.query("SELECT id, document_id, content, embedding FROM chunks")
    scored: list[tuple[float, dict]] = []
    for row in rows:
        vector = _decode(row["embedding"])
        score = _cosine(query_vector, vector)
        scored.append((score, row))

    # Sort by score descending, take the top_k.
    scored.sort(key=lambda item: item[0], reverse=True)

    doc_ids = {r["document_id"] for _, r in scored[:top_k]}
    doc_names = {}
    if doc_ids:
        placeholders = ",".join("?" for _ in doc_ids)
        for doc in db.query(
            f"SELECT id, filename FROM documents WHERE id IN ({placeholders})",
            tuple(doc_ids),
        ):
            doc_names[doc["id"]] = doc["filename"]

    results = []
    for score, row in scored[:top_k]:
        if score <= 0:
            break
        results.append(
            {
                "content": row["content"],
                "document_id": row["document_id"],
                "filename": doc_names.get(row["document_id"], "unknown"),
                "score": round(score, 4),
            }
        )
    return results
