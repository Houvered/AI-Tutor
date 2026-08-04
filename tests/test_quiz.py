"""Tests for quiz JSON generation and evaluation."""

import json
import unittest.mock as mock

from backend import config
from backend import db
from backend import quiz
from backend import rag
from backend.quiz import QuizSchemaError

GOOD_JSON = json.dumps(
    {
        "questions": [
            {
                "question": "Which holds in a binary search tree?",
                "options": ["a", "b", "c", "d"],
                "correct_index": 1,
                "explanation": "Because the left child is smaller.",
            }
        ]
    }
)


def _ingest(sample_file):
    rag.ingest_file(sample_file, "notes.md")


class TestQuestionParsing:
    def test_good_json(self):
        parsed = quiz._parse_questions(GOOD_JSON)
        assert len(parsed) == 1
        assert len(parsed[0]["options"]) == 4

    def test_fenced_json(self):
        parsed = quiz._parse_questions(f"```json\n{GOOD_JSON}\n```")
        assert len(parsed) == 1

    def test_requires_four_options(self):
        bad = json.dumps(
            {"questions": [{"question": "q", "options": ["a"], "correct_index": 0, "explanation": ""}]}
        )
        try:
            quiz._parse_questions(bad)
            raise AssertionError("expected QuizSchemaError")
        except QuizSchemaError:
            pass


class TestGenerateQuiz:
    def test_generates_questions(self, temp_db, sample_file, fake_llm):
        _ingest(sample_file)
        with mock.patch("backend.quiz.llm.chat", return_value=GOOD_JSON):
            questions = quiz.generate_quiz("binary search tree", count=1)
        assert len(questions) == 1
        assert questions[0]["correct_index"] == 1

    def test_no_material_raises(self, temp_db, fake_llm):
        with mock.patch("backend.quiz.llm.chat", return_value=GOOD_JSON):
            try:
                quiz.generate_quiz("anything", count=1)
                raise AssertionError("expected QuizSchemaError")
            except QuizSchemaError:
                pass

    def test_bad_json_retries_then_raises(self, temp_db, sample_file, fake_llm):
        _ingest(sample_file)
        with mock.patch("backend.quiz.llm.chat", return_value="not json"):
            try:
                quiz.generate_quiz("binary search tree", count=1, max_retries=2)
                raise AssertionError("expected QuizSchemaError")
            except QuizSchemaError:
                pass


class TestEvaluate:
    def test_correct(self):
        assert quiz.evaluate(1, 1, "e")["correct"] is True

    def test_wrong(self):
        assert quiz.evaluate(0, 1, "e")["correct"] is False