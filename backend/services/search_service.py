"""Wraps one Lambda + one Qdrant cluster into a single search call."""
import logging

import numpy as np
from PIL import Image
from qdrant_client import QdrantClient

from backend.services.clip_service import LambdaCLIPService

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(
        self,
        lambda_url: str,
        qdrant_url: str,
        qdrant_api_key: str,
        collection_name: str,
    ):
        self.clip = LambdaCLIPService(url=lambda_url)
        self.collection = collection_name
        self.client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=30,
            prefer_grpc=False,
        )

    def search(self, image: Image.Image, top_k: int = 4) -> list[dict]:
        embedding = self.clip.get_embedding(image)

        vec = np.array(embedding, dtype=np.float32)
        vec = vec / (np.linalg.norm(vec) + 1e-8)

        results = self.client.query_points(
            collection_name=self.collection,
            query=vec.tolist(),
            limit=top_k,
            with_payload=True,
        )

        items = []
        for hit in results.points:
            payload = hit.payload or {}
            title = payload.get("title") or payload.get("name", "Unknown")
            items.append(
                {
                    "score": round(float(hit.score), 4),
                    "title": title,
                    "price": str(payload.get("price", "N/A")),
                    "source": payload.get("source", ""),
                    "image_url": payload.get("image_url", ""),
                }
            )
        return items
