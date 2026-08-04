"""Grounded answer generation.

Builds a prompt that contains only the user's own material and asks the chat
model to answer strictly from it, with citations. If the material does not
contain an answer, the model says so instead of guessing.
"""

from backend import rag
from backend.llm import llm

SYSTEM_PROMPT = (
    "You are a study companion. Answer the student's question using ONLY the "
    "context given below. The context is the student's own uploaded study "
    "material. Follow these rules:\n"
    "1. Answer from the context only. Never use your own general knowledge.\n"
    "2. Add a citation like [1] after every statement that comes from a "
    "numbered context block. Use the number of that block.\n"
    "3. If the context does not contain the answer, say clearly: 'This is not "
    "in your study material.' and do not guess.\n"
    "4. Be clear and short. Use simple words.\n"
    "5. You may use markdown for lists and emphasis.\n"
    "<context>\n{context}\n</context>\n"
)


def _format_context(chunks: list[dict]) -> str:
    """Turn retrieved chunks into numbered blocks for the prompt."""
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        blocks.append(f"[{i}] (from {chunk['filename']})\n{chunk['content']}")
    return "\n\n".join(blocks)


def answer_question(question: str, history: list[dict] | None = None) -> dict:
    """Answer a question grounded in the user's uploaded material.

    Returns: answer, citations, and the retrieved chunks used.
    """
    chunks = rag.retrieve(question)
    citations = [
        {
            "index": i,
            "text": chunk["content"][:400],
            "filename": chunk["filename"],
        }
        for i, chunk in enumerate(chunks, start=1)
    ]

    if not chunks:
        return {
            "answer": "You have not uploaded any study material yet, or nothing "
            "matched your question. Upload your notes first, then ask again.",
            "citations": [],
            "used_chunks": [],
        }

    system = SYSTEM_PROMPT.format(context=_format_context(chunks))

    # Include recent conversation so the model can keep context.
    user_parts = ""
    if history:
        lines = []
        for item in history[-6:]:
            role = item.get("role", "user")
            content = item.get("content", "")
            lines.append(f"{role}: {content}")
        user_parts = "Previous conversation:\n" + "\n".join(lines) + "\n\n"

    user_prompt = f"{user_parts}Question: {question}"

    try:
        answer = llm.chat(system, user_prompt)
    except Exception:
        # Fall back to showing the best matching material directly.
        answer = (
            "The AI answer service is not available right now. Here is the "
            "closest part of your study material:\n\n"
            + _format_context(chunks)
        )

    return {"answer": answer, "citations": citations, "used_chunks": chunks}
