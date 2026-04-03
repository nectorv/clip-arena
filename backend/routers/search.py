"""POST /search — runs both models in parallel, returns blind A/B results."""
import asyncio
import io
import random
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from backend.config import settings
from backend.db import get_conn
from backend.services.search_service import SearchService

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=4)

original_service = SearchService(
    lambda_url=settings.LAMBDA_URL_ORIGINAL,
    qdrant_url=settings.QDRANT_URL_ORIGINAL,
    qdrant_api_key=settings.QDRANT_API_KEY_ORIGINAL,
    collection_name=settings.QDRANT_COLLECTION_ORIGINAL,
)

finetuned_service = SearchService(
    lambda_url=settings.LAMBDA_URL_FINETUNED,
    qdrant_url=settings.QDRANT_URL_FINETUNED,
    qdrant_api_key=settings.QDRANT_API_KEY_FINETUNED,
    collection_name=settings.QDRANT_COLLECTION_FINETUNED,
)


def _run_search(service: SearchService, image: Image.Image, top_k: int):
    start = time.monotonic()
    results = service.search(image, top_k=top_k)
    latency_ms = int((time.monotonic() - start) * 1000)
    return results, latency_ms


@router.post("/search")
async def search(file: UploadFile = File(...), top_k: int = 4):
    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    loop = asyncio.get_event_loop()

    original_future = loop.run_in_executor(executor, _run_search, original_service, image, top_k)
    finetuned_future = loop.run_in_executor(executor, _run_search, finetuned_service, image, top_k)

    try:
        (original_results, lat_orig), (finetuned_results, lat_ft) = await asyncio.gather(
            original_future, finetuned_future
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Search failed: {str(e)}")

    session_id = str(uuid.uuid4())

    # Randomly assign A/B — store mapping server-side so the UI stays blind
    pairs = [("original", original_results, lat_orig), ("finetuned", finetuned_results, lat_ft)]
    random.shuffle(pairs)
    label_a, label_b = pairs[0][0], pairs[1][0]

    with get_conn() as conn:
        conn.execute(
            """INSERT INTO searches
               (session_id, latency_original_ms, latency_finetuned_ms, label_a, label_b)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, lat_orig, lat_ft, label_a, label_b),
        )

    # model_key is NOT returned — revealed only after POST /vote
    return {
        "session_id": session_id,
        "panel_a": {"results": pairs[0][1], "latency_ms": pairs[0][2]},
        "panel_b": {"results": pairs[1][1], "latency_ms": pairs[1][2]},
    }
