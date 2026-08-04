"""Quiz generation and evaluation.

Generates multiple choice questions from the student's study material using the
chat model. The model returns strict JSON which we validate. If the JSON is bad,
we retry a few times and finally give up gracefully instead of crashing.
"""

import json
import re

from backend import rag
from backend.llm import llm
from backend.llm import LLMError

QUESTION_PROMPT = (
    "Write {count} multiple choice question(s) about the study material in the "
    "context below. The material is the student's own uploaded notes. The "
    "questions must be answerable ONLY from this material. Follow these rules:\n"
    "1. Each question has exactly 4 options. Exactly one is correct.\n"
    "2. The incorrect options must look believable but be wrong.\n"
    "3. Give a short explanation for the correct answer, based on the material.\n"
    "4. Return ONLY valid JSON, no other text. Use exactly this shape:\n"
    '{"questions": [{"question": "...", "options": ["a", "b", "c", "d"], '
    '"correct_index": 2, "explanation": "..."}]}\n'
    "correct_index is the 0-based index of the right option.\n"
    "<context>\n{context}\n</context>\n"
)


class QuizSchemaError(Exception):
    """Raised when the model does not return valid quiz JSON."""


def _clean_code_blocks(text: str) -> str:
    """Strip markdown code fences if the model wrapped the JSON in them."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ``` wrappers.
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop the first fence line and the last fence line.
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def _parse_questions(raw: str) -> list[dict]:
    """Parse and validate the model's JSON into a clean question list."""
    payload = json.loads(_clean_code_blocks(raw))
    questions = payload.get("questions")
    if not isinstance(questions, list) or not questions:
        raise QuizSchemaError("no questions in response")

    parsed = []
    for q in questions:
        if not isinstance(q, dict):
            raise QuizSchemaError("question is not an object")
        question = str(q.get("question", "")).strip()
        options = q.get("options")
        if not question or not isinstance(options, list) or len(options) != 4:
            raise QuizSchemaError("question missing text or 4 options")
        if not all(isinstance(o, str) and o.strip() for o in options):
            raise QuizSchemaError("options must be non-empty strings")
        correct = q.get("correct_index")
        if not isinstance(correct, int) or not (0 <= correct < 4):
            raise QuizSchemaError("correct_index must be 0 to 3")
        parsed.append(
            {
                "question": question,
                "options": [o.strip() for o in options],
                "correct_index": correct,
                "explanation": str(q.get("explanation", "")).strip(),
            }
        )
    return parsed


def generate_quiz(question: str, count: int = 3, max_retries: int = 3) -> list[dict]:
    """Generate quiz questions grounded in the material. Raises on failure."""
    chunks = rag.retrieve(question, top_k=5)
    if not chunks:
        raise QuizSchemaError(
            "No study material found to build a quiz from. Upload notes first."
        )

    context = "\n\n".join(
        f"[{i}] {c['content']}" for i, c in enumerate(chunks, start=1)
    )
    system = "You create quiz questions. Return only valid JSON."
    # Use str.replace so the JSON braces in the template are safe.
    user = QUESTION_PROMPT.replace("{count}", str(count)).replace("{context}", context)

    last_error: Exception = QuizSchemaError("quiz generation failed")
    for _ in range(max_retries):
        try:
            raw = llm.chat(system, user)
            return _parse_questions(raw)
        except (json.JSONDecodeError, QuizSchemaError, LLMError) as exc:
            last_error = exc
    raise QuizSchemaError(f"quiz generation failed after {max_retries} attempts: {last_error}") from last_error


def evaluate(
    selected_index: int,
    correct_index: int,
    explanation: str | None = None,
) -> dict:
    """Grade an answer. Returns the result as a dict."""
    correct = selected_index == correct_index
    return {
        "correct": correct,
        "explanation": explanation or "",
        "selected_index": selected_index,
        "correct_index": correct_index,
    }


def extract_quiz_from_answer(answer: str, max_retries: int = 2) -> list[dict] | None:
    """Try to pull a single inline quiz out of a response that mixed it in.

    Looks for a top-level "questions" JSON array in the answer text. Returns
    None if nothing valid is found (so the caller can skip the quiz quietly).
    """
    match = re.search(r"\{.*\"questions\".*\}\s*$", answer, flags=re.S)
    if not match:
        return None
    try:
        return _parse_questions(match.group(0))
    except (json.JSONDecodeError, QuizSchemaError):
        return None