# CLIP Arena

A web app to compare the performance of an **original** vs **fine-tuned** CLIP ViT-B/32 model through human preference voting.

Upload a furniture image — both models search their respective vector databases in parallel — you vote for the better result set — the winner is revealed.

**Live demo:** https://djti9taa0h749.cloudfront.net

---

## What it does

1. User uploads a furniture image
2. Both CLIP models embed the image via AWS Lambda (in parallel)
3. Each embedding is used to query a Qdrant vector database
4. Results are shown side-by-side, **blind** (no model labels)
5. User votes for the better result set
6. The winning model is revealed
7. Votes are aggregated on a leaderboard

---

## Architecture

```
Browser (React + Tailwind)
    │  HTTPS
    ▼
CloudFront
    ├── /           → S3 (static React build)
    ├── /search     ┐
    ├── /vote       ├→ EC2 t3.micro (FastAPI + Docker)
    └── /stats      ┘       │
                            ├── Lambda A (original CLIP)  → Qdrant A (GCP)
                            └── Lambda B (fine-tuned CLIP) → Qdrant B (AWS)
                            └── SQLite (votes + latency)
```

### Key design decisions

- **Blind comparison** — model identity is stored server-side, never sent to the browser until after the vote
- **Parallel inference** — both Lambda calls run concurrently via `asyncio.gather` + thread pool
- **L2 normalization** — embeddings are normalized before querying Qdrant for consistent cosine similarity scores
- **Same dataset** — both clusters index the same furniture images, ensuring a fair comparison

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Tailwind CSS v4, Vite |
| Backend | FastAPI, Python 3.11, uvicorn |
| Embeddings | CLIP ViT-B/32 via AWS Lambda (custom container) |
| Vector DB | Qdrant (cloud) |
| Vote storage | SQLite |
| Hosting | AWS EC2 t3.micro + S3 + CloudFront |

---

## Project structure

```
clip-arena/
├── backend/
│   ├── main.py                  # FastAPI app, CORS, startup
│   ├── config.py                # pydantic-settings (.env)
│   ├── db.py                    # SQLite schema + connection
│   ├── routers/
│   │   ├── search.py            # POST /search
│   │   └── votes.py             # POST /vote · GET /stats
│   └── services/
│       ├── clip_service.py      # Lambda HTTP client
│       └── search_service.py    # CLIP + Qdrant combined
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Arena.tsx        # Main comparison UI
│       │   └── Stats.tsx        # Leaderboard
│       └── components/
│           ├── ImageUploader.tsx
│           └── ResultPanel.tsx
├── tests/
│   ├── test_search.py
│   └── test_votes.py
├── Dockerfile.backend
├── docker-compose.yml
└── requirements.txt
```

---

## API

### `POST /search`
Upload an image, get back two blind result panels.

```bash
curl -X POST https://djti9taa0h749.cloudfront.net/search \
  -F "file=@your_image.jpg"
```

Response:
```json
{
  "session_id": "uuid",
  "panel_a": { "results": [...], "latency_ms": 1200 },
  "panel_b": { "results": [...], "latency_ms": 980 }
}
```

### `POST /vote`
Submit your vote and reveal the model identities.

```bash
curl -X POST https://djti9taa0h749.cloudfront.net/vote \
  -H "Content-Type: application/json" \
  -d '{"session_id": "uuid", "chosen_panel": "a"}'
```

Response:
```json
{
  "winner": "finetuned",
  "reveal": { "panel_a": "finetuned", "panel_b": "original" }
}
```

### `GET /stats`

```bash
curl https://djti9taa0h749.cloudfront.net/stats
```

Response:
```json
{
  "total_votes": 42,
  "original":  { "wins": 18, "win_rate": 42.9, "avg_latency_ms": 1340 },
  "finetuned": { "wins": 24, "win_rate": 57.1, "avg_latency_ms": 1180 }
}
```

---

## Running locally

### Backend

```bash
cd clip-arena
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in your credentials
uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # → http://localhost:5173
```

### Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

### Docker

```bash
docker-compose up --build
```

---

## Environment variables

| Variable | Description |
|---|---|
| `LAMBDA_URL_ORIGINAL` | Lambda function URL for original CLIP |
| `LAMBDA_URL_FINETUNED` | Lambda function URL for fine-tuned CLIP |
| `QDRANT_URL_ORIGINAL` | Qdrant cluster URL (original) |
| `QDRANT_API_KEY_ORIGINAL` | Qdrant API key (original) |
| `QDRANT_COLLECTION_ORIGINAL` | Collection name (original) |
| `QDRANT_URL_FINETUNED` | Qdrant cluster URL (fine-tuned) |
| `QDRANT_API_KEY_FINETUNED` | Qdrant API key (fine-tuned) |
| `QDRANT_COLLECTION_FINETUNED` | Collection name (fine-tuned) |
