"""Tests for POST /search endpoint."""
import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app

client = TestClient(app)


def make_jpeg_bytes(color=(200, 150, 100), size=(50, 50)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="JPEG")
    return buf.getvalue()


FAKE_RESULTS = [
    {"score": 0.95, "title": "Sofa A", "price": "499", "source": "ikea", "image_url": "http://img/1.jpg"},
    {"score": 0.90, "title": "Chair B", "price": "199", "source": "ikea", "image_url": "http://img/2.jpg"},
]


@pytest.fixture
def mock_search_services():
    """Patch both SearchService instances to avoid real network calls."""
    with patch("backend.routers.search.original_service") as mock_orig, \
         patch("backend.routers.search.finetuned_service") as mock_ft:
        mock_orig.search.return_value = FAKE_RESULTS
        mock_ft.search.return_value = FAKE_RESULTS
        yield mock_orig, mock_ft


def test_search_returns_two_panels(mock_search_services):
    resp = client.post("/search", files={"file": ("test.jpg", make_jpeg_bytes(), "image/jpeg")})
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "panel_a" in data
    assert "panel_b" in data


def test_search_panels_have_results_and_latency(mock_search_services):
    resp = client.post("/search", files={"file": ("test.jpg", make_jpeg_bytes(), "image/jpeg")})
    data = resp.json()
    for panel in ("panel_a", "panel_b"):
        assert "results" in data[panel]
        assert "latency_ms" in data[panel]
        assert isinstance(data[panel]["latency_ms"], int)
        assert len(data[panel]["results"]) == len(FAKE_RESULTS)


def test_search_does_not_reveal_model_key(mock_search_services):
    """Model identity must NOT be in the response before voting."""
    resp = client.post("/search", files={"file": ("test.jpg", make_jpeg_bytes(), "image/jpeg")})
    data = resp.json()
    assert "model_key" not in data["panel_a"]
    assert "model_key" not in data["panel_b"]


def test_search_rejects_non_image():
    resp = client.post("/search", files={"file": ("text.txt", b"not an image", "text/plain")})
    assert resp.status_code == 400


def test_search_panels_are_shuffled(mock_search_services):
    """Over many runs, both original and finetuned should appear as panel_a at least once."""
    mock_orig, mock_ft = mock_search_services
    mock_orig.search.return_value = [{"score": 0.9, "title": "orig", "price": "100", "source": "", "image_url": ""}]
    mock_ft.search.return_value = [{"score": 0.8, "title": "ft", "price": "200", "source": "", "image_url": ""}]

    # Run many times — shuffle should produce both orderings eventually
    titles_in_a = set()
    for _ in range(30):
        resp = client.post("/search", files={"file": ("test.jpg", make_jpeg_bytes(), "image/jpeg")})
        titles_in_a.add(resp.json()["panel_a"]["results"][0]["title"])

    assert len(titles_in_a) == 2, "Shuffle should randomize panel assignment"


def test_search_stores_session_in_db(mock_search_services):
    """A search should create a row in the searches table."""
    from backend.db import get_conn

    resp = client.post("/search", files={"file": ("test.jpg", make_jpeg_bytes(), "image/jpeg")})
    session_id = resp.json()["session_id"]

    with get_conn() as conn:
        row = conn.execute("SELECT * FROM searches WHERE session_id = ?", (session_id,)).fetchone()
    assert row is not None
    assert row["voted"] == 0
