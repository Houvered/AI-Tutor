"""StudyMate backend application.

One FastAPI server that serves both the API and the built frontend.
"""

import os
import shutil
import uuid

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend import config
from backend import db
from backend import quiz
from backend import rag
from backend import revision
from backend import tutor
from backend.llm import llm
from backend.llm import LLMError
from backend.quiz import QuizSchemaError


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create data folders and database tables on start."""
    config.ensure_dirs()
    db.connect()
    yield


app = FastAPI(title="StudyMate", version="1.0.0", lifespan=lifespan)


class AskRequest(BaseModel):
    message: str
    history: list[dict] | None = None


class QuizRequest(BaseModel):
    question: str
    count: int = 3


class EvaluateRequest(BaseModel):
    selected_index: int
    correct_index: int
    explanation: str | None = None
    topic: str | None = None


class GradeRequest(BaseModel):
    topic: str
    quality: int


@app.get("/api/health")
def health() -> dict:
    """Check that the app, the database, and the LLM connection are ready."""
    try:
        doc_count = db.query("SELECT COUNT(*) AS n FROM documents")[0]["n"]
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail="database not ready") from exc
    return {
        "status": "ok",
        "documents_count": doc_count,
        "llm_connected": llm.ping(),
    }


@app.post("/api/ask")
def ask_question(payload: AskRequest) -> dict:
    """Answer a question grounded in the user's uploaded material."""
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty.")
    result = tutor.answer_question(payload.message.strip(), payload.history)
    return result


@app.post("/api/quiz/generate")
def generate_quiz(payload: QuizRequest) -> dict:
    """Generate multiple choice questions from the study material."""
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question is empty.")
    try:
        questions = quiz.generate_quiz(payload.question.strip(), payload.count)
    except QuizSchemaError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"questions": questions}


@app.post("/api/quiz/evaluate")
def evaluate_answer(payload: EvaluateRequest) -> dict:
    """Grade a quiz answer. If correct and a topic is given, schedule it."""
    result = quiz.evaluate(
        selected_index=payload.selected_index,
        correct_index=payload.correct_index,
        explanation=payload.explanation,
    )
    if result["correct"] and payload.topic and payload.topic.strip():
        revision.schedule(payload.topic.strip())
    return result


@app.get("/api/revision")
def get_due_revisions() -> dict:
    """Return topics that are due for review."""
    return {"revisions": revision.get_due_revisions()}


@app.post("/api/revision/grade")
def grade_revision(payload: GradeRequest) -> dict:
    """Apply a quality grade (0-5) to a topic's spaced repetition card."""
    if not payload.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is empty.")
    try:
        return revision.grade(payload.topic.strip(), payload.quality)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/documents/upload")
def upload_document(file: UploadFile) -> dict:
    """Save, parse, chunk, embed, and index an uploaded study file."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {sorted(config.ALLOWED_EXTENSIONS)}",
        )

    # Save the upload to disk first.
    config.ensure_dirs()
    temp_id = uuid.uuid4().hex
    saved_path = os.path.join(config.UPLOAD_DIR, f"{temp_id}{ext}")
    with open(saved_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    if os.path.getsize(saved_path) > config.MAX_UPLOAD_BYTES:
        os.remove(saved_path)
        raise HTTPException(status_code=400, detail="File is too large.")

    try:
        doc_id = rag.ingest_file(saved_path, file.filename or saved_path)
    except ValueError as exc:
        os.remove(saved_path)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMError as exc:
        os.remove(saved_path)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        # Clean up the temporary upload; the text lives in the database now.
        if os.path.exists(saved_path):
            os.remove(saved_path)

    row = db.query("SELECT id, filename, created_at FROM documents WHERE id = ?", (doc_id,))[0]
    return {"id": row["id"], "filename": row["filename"], "created_at": row["created_at"]}


@app.get("/api/documents")
def list_documents() -> dict:
    """List all uploaded documents."""
    rows = db.query("SELECT id, filename, created_at FROM documents ORDER BY created_at DESC")
    return {"documents": rows}


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str) -> dict:
    """Delete a document and all its chunks."""
    exists = db.query("SELECT id FROM documents WHERE id = ?", (doc_id,))
    if not exists:
        raise HTTPException(status_code=404, detail="Document not found.")
    rag.delete_document(doc_id)
    return {"deleted": True}


# Serve the built frontend if it exists (after `npm run build`).
public_dir = os.path.join("frontend", "dist")
if os.path.isdir(public_dir):
    app.mount("/", StaticFiles(directory=public_dir, html=True), name="public")
else:
    @app.get("/")
    def root() -> dict:
        text = "StudyMate API is running. Build the frontend with npm run build to see the UI."
        return {"message": text, "docs": "/docs", "health": "/api/health"}
