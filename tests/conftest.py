import pytest
from backend.db import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Ensure DB tables exist before any test runs."""
    init_db()
