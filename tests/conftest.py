"""Shared fixtures for the test suite.

Every test runs against a fresh temporary database so tests never touch real
data and never need a real LLM API key.
"""

import os
import tempfile
import unittest.mock as mock

import pytest

from backend import config
from backend import db


@pytest.fixture()
def temp_db():
    """Point the app at a fresh temp database for one test."""
    tmp = tempfile.mkdtemp()
    config.DATA_DIR = tmp
    config.DB_PATH = os.path.join(tmp, "test.db")
    config.UPLOAD_DIR = os.path.join(tmp, "uploads")
    db._connection = None
    yield
    db._connection = None


@pytest.fixture()
def fake_llm():
    """Mock the LLM client so no API key is needed.

    - embed/embed_one return deterministic fake vectors.
    - chat returns a canned grounded answer.
    """
    def _embed(texts):
        return [[float(len(t) % 10 + 1), 0.5, -0.25] for t in texts]

    with mock.patch("backend.rag.llm.embed", side_effect=_embed), mock.patch(
        "backend.rag.llm.embed_one", side_effect=lambda t: _embed([t])[0]
    ), mock.patch("backend.tutor.llm.chat", return_value="Grounded answer. [1]"):
        yield


SAMPLE_TEXT = (
    "A binary search tree keeps keys in sorted order. The left child holds a "
    "smaller key. The right child holds a larger key. Search takes O(log n) "
    "time on a balanced tree. Red black trees are a balanced variant. "
    "Hash tables map keys to values. Chaining solves collisions. Open "
    "addressing tries another slot. A good hash function spreads keys evenly. "
    "Insertion in a tree takes O(log n) time. Deletion is more complex but "
    "still fast. AVL trees balance by rotations. Binary heaps are used for "
    "priority queues. Heaps are not sorted. The heap property is weaker than "
    "the search tree property. This is the end of the first section of the "
    "sample study notes. The second section starts right here. We talk about "
    "graph algorithms now. A graph has vertices and edges. Depth first search "
    "explores one branch fully before moving on. Breadth first search explores "
    "level by level. Dijkstra finds the shortest path with positive weights. "
    "A minimum spanning tree connects all vertices with the least total weight. "
    "Kruskal sorts edges by weight and joins them in order. Prim grows a tree "
    "from one vertex. This concludes the sample study notes on graphs."
)


@pytest.fixture()
def sample_file(temp_db, tmp_path):
    """Write the sample study text to a file and return its path."""
    path = tmp_path / "notes.md"
    path.write_text(SAMPLE_TEXT, encoding="utf-8")
    return str(path)
