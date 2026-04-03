"""SQLite database — votes and session tracking."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "arena.db"


def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS searches (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id           TEXT NOT NULL UNIQUE,
                label_a              TEXT NOT NULL,
                label_b              TEXT NOT NULL,
                latency_original_ms  INTEGER,
                latency_finetuned_ms INTEGER,
                voted                INTEGER DEFAULT 0,
                created_at           DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT NOT NULL UNIQUE,
                winner      TEXT NOT NULL CHECK(winner IN ('original', 'finetuned')),
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
