"""HTTP client for a CLIP Lambda endpoint — returns 512-d embeddings."""
import io
import logging
import threading
import time

import requests
from PIL import Image

logger = logging.getLogger(__name__)


class LambdaCLIPService:
    def __init__(self, url: str, timeout: int = 30):
        self.url = url
        self.timeout = timeout
        self._last_warm = 0.0
        self._warm_interval = 20

    def _to_bytes(self, image: Image.Image) -> bytes:
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="JPEG")
        return buf.getvalue()

    def get_embedding(self, image: Image.Image) -> list[float]:
        image_bytes = self._to_bytes(image)
        resp = requests.post(
            self.url,
            data=image_bytes,
            headers={"Content-Type": "application/octet-stream"},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        payload = resp.json()

        if not isinstance(payload, dict) or "embedding" not in payload:
            raise ValueError(f"Unexpected Lambda response: {payload}")

        embedding = payload["embedding"]
        if isinstance(embedding, list) and len(embedding) == 1 and isinstance(embedding[0], list):
            embedding = embedding[0]

        if len(embedding) != 512:
            raise ValueError(f"Expected 512-d embedding, got {len(embedding)}")

        return [float(x) for x in embedding]

    def warm_async(self) -> None:
        now = time.time()
        if (now - self._last_warm) < self._warm_interval:
            return

        def _ping():
            try:
                buf = io.BytesIO()
                Image.new("RGB", (1, 1), (255, 255, 255)).save(buf, format="JPEG")
                requests.post(
                    self.url,
                    data=buf.getvalue(),
                    headers={"Content-Type": "application/octet-stream"},
                    timeout=5,
                )
            except Exception:
                pass
            finally:
                self._last_warm = time.time()

        threading.Thread(target=_ping, daemon=True).start()
