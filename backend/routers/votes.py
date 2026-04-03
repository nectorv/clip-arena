"""POST /vote — record winner and reveal model identities.
   GET  /stats — win rates, vote counts, avg latency.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.db import get_conn

router = APIRouter()


class VotePayload(BaseModel):
    session_id: str
    chosen_panel: str  # "a" or "b"


@router.post("/vote")
def vote(payload: VotePayload):
    if payload.chosen_panel not in ("a", "b"):
        raise HTTPException(status_code=400, detail="chosen_panel must be 'a' or 'b'")

    with get_conn() as conn:
        row = conn.execute(
            "SELECT label_a, label_b, voted FROM searches WHERE session_id = ?",
            (payload.session_id,),
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if row["voted"]:
            raise HTTPException(status_code=409, detail="Already voted for this session")

        winner = row["label_a"] if payload.chosen_panel == "a" else row["label_b"]

        conn.execute(
            "INSERT INTO votes (session_id, winner) VALUES (?, ?)",
            (payload.session_id, winner),
        )
        conn.execute(
            "UPDATE searches SET voted = 1 WHERE session_id = ?",
            (payload.session_id,),
        )

    return {
        "winner": winner,
        "reveal": {
            "panel_a": row["label_a"],
            "panel_b": row["label_b"],
        },
    }


@router.get("/stats")
def stats():
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM votes").fetchone()[0]

        original_wins = conn.execute(
            "SELECT COUNT(*) FROM votes WHERE winner = 'original'"
        ).fetchone()[0]

        finetuned_wins = conn.execute(
            "SELECT COUNT(*) FROM votes WHERE winner = 'finetuned'"
        ).fetchone()[0]

        avg_latencies = conn.execute(
            """SELECT
                AVG(latency_original_ms)  AS avg_original_ms,
                AVG(latency_finetuned_ms) AS avg_finetuned_ms
               FROM searches"""
        ).fetchone()

    return {
        "total_votes": total,
        "original": {
            "wins": original_wins,
            "win_rate": round(original_wins / total * 100, 1) if total else 0,
            "avg_latency_ms": round(avg_latencies["avg_original_ms"] or 0),
        },
        "finetuned": {
            "wins": finetuned_wins,
            "win_rate": round(finetuned_wins / total * 100, 1) if total else 0,
            "avg_latency_ms": round(avg_latencies["avg_finetuned_ms"] or 0),
        },
    }
