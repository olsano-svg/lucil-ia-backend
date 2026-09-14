import logging
import httpx
from typing import List
from app.ai_engine.providers.base import BaseEmbeddingProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """
    Proveedor Local de Embeddings usando Ollama y nomic-embed-text.
    Totalmente privado, corre en GPU/CPU local sin costos de API.
    """
    def __init__(self, model_name: str = "nomic-embed-text", base_url: str = None):
        self.model_name = model_name
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.client_timeout = httpx.Timeout(180.0, connect=30.0)

    async def get_embedding(self, text: str) -> List[float]:
        """Genera un vector denso (embedding) para un texto dado."""
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.model_name,
            "prompt": text
        }
        try:
            async with httpx.AsyncClient(timeout=self.client_timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("embedding", [])
        except Exception as e:
            logger.error(f"Error generando embedding local con {self.model_name}: {e}")
            raise

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings en lote (batch) de forma eficiente."""
        if not texts:
            return []
        url = f"{self.base_url}/api/embed"
        payload = {
            "model": self.model_name,
            "input": texts
        }
        try:
            async with httpx.AsyncClient(timeout=self.client_timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("embeddings", [])
        except Exception as e:
            logger.warning(f"/api/embed no disponible o falló ({e}), usando fallback individual.")

        # Fallback individual si /api/embed no responde
        results = []
        for text in texts:
            results.append(await self.get_embedding(text))
        return results
