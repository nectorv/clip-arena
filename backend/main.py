from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db import init_db
from backend.routers import search, votes

app = FastAPI(title="CLIP Arena")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    # Pre-warm both Lambda endpoints to avoid cold-start 504s on first request
    from backend.routers.search import original_service, finetuned_service
    original_service.clip.warm_async()
    finetuned_service.clip.warm_async()


app.include_router(search.router)
app.include_router(votes.router)
