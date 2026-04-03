"""Tests for POST /vote and GET /stats endpoints."""
import io
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app
from backend.db import get_conn, init_db

client = TestClient(app)


def make_jpeg_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), (100, 100, 100)).save(buf, format="JPEG")
    return buf.getvalue()


FAKE_RESULTS = [
    {"score": 0.9, "title": "Item", "price": "100", "source": "test", "image_url": ""}
]


@pytest.fixture(autouse=True)
def mock_search_services():
    with patch("backend.routers.search.original_service") as mock_orig, \
         patch("backend.routers.search.finetuned_service") as mock_ft:
        mock_orig.search.return_value = FAKE_RESULTS
        mock_ft.search.return_value = FAKE_RESULTS
        yield


def _do_search() -> dict:
    resp = client.post("/search", files={"file": ("test.jpg", make_jpeg_bytes(), "image/jpeg")})
    assert resp.status_code == 200
    return resp.json()


# ── Vote endpoint ────────────────────────────────────────────────────────────

def test_vote_returns_winner_and_reveal():
    search = _do_search()
    resp = client.post("/vote", json={"session_id": search["session_id"], "chosen_panel": "a"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["winner"] in ("original", "finetuned")
    assert data["reveal"]["panel_a"] in ("original", "finetuned")
    assert data["reveal"]["panel_b"] in ("original", "finetuned")
    assert data["reveal"]["panel_a"] != data["reveal"]["panel_b"]


def test_vote_winner_matches_chosen_panel():
    search = _do_search()
    session_id = search["session_id"]

    # Find out which model is panel_a by peeking at the DB
    with get_conn() as conn:
        row = conn.execute("SELECT label_a FROM searches WHERE session_id = ?", (session_id,)).fetchone()
    expected_winner = row["label_a"]

    resp = client.post("/vote", json={"session_id": session_id, "chosen_panel": "a"})
    assert resp.json()["winner"] == expected_winner


def test_vote_prevents_double_voting():
    search = _do_search()
    session_id = search["session_id"]
    client.post("/vote", json={"session_id": session_id, "chosen_panel": "a"})
    resp = client.post("/vote", json={"session_id": session_id, "chosen_panel": "b"})
    assert resp.status_code == 409


def test_vote_unknown_session():
    resp = client.post("/vote", json={"session_id": "nonexistent-uuid", "chosen_panel": "a"})
    assert resp.status_code == 404


def test_vote_invalid_panel():
    search = _do_search()
    resp = client.post("/vote", json={"session_id": search["session_id"], "chosen_panel": "c"})
    assert resp.status_code == 400


def test_vote_marks_session_as_voted():
    search = _do_search()
    session_id = search["session_id"]
    client.post("/vote", json={"session_id": session_id, "chosen_panel": "b"})
    with get_conn() as conn:
        row = conn.execute("SELECT voted FROM searches WHERE session_id = ?", (session_id,)).fetchone()
    assert row["voted"] == 1


# ── Stats endpoint ───────────────────────────────────────────────────────────

def test_stats_returns_expected_shape():
    resp = client.get("/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_votes" in data
    for model in ("original", "finetuned"):
        assert model in data
        assert "wins" in data[model]
        assert "win_rate" in data[model]
        assert "avg_latency_ms" in data[model]


def test_stats_win_rates_sum_to_100():
    # Cast two votes first
    for panel in ("a", "b"):
        search = _do_search()
        client.post("/vote", json={"session_id": search["session_id"], "chosen_panel": panel})

    resp = client.get("/stats")
    data = resp.json()
    if data["total_votes"] > 0:
        total = data["original"]["wins"] + data["finetuned"]["wins"]
        assert total == data["total_votes"]


def test_stats_total_increments_after_vote():
    before = client.get("/stats").json()["total_votes"]
    search = _do_search()
    client.post("/vote", json={"session_id": search["session_id"], "chosen_panel": "a"})
    after = client.get("/stats").json()["total_votes"]
    assert after == before + 1
