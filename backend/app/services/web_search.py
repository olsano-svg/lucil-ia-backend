import asyncio
import logging
from typing import List, Dict, Any, Optional

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

import trafilatura

logger = logging.getLogger(__name__)

class WebSearchService:
    """
    Servicio de Búsqueda Web Abierta, Legal y Pública.
    No requiere APIs comerciales ni claves de pago.
    Utiliza DDGS para descubrimiento y Trafilatura para extracción limpia de texto.
    """

    @staticmethod
    def _sync_search(query: str, max_results: int = 4) -> List[Dict[str, str]]:
        if not DDGS:
            logger.error("Módulo DDGS no disponible.")
            return []
        try:
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=max_results))
                formatted = []
                for r in raw_results:
                    title = r.get("title", "Sin título")
                    url = r.get("href", "")
                    snippet = r.get("body", "")
                    if url:
                        formatted.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet
                        })
                return formatted
        except Exception as e:
            logger.warning(f"Error en búsqueda web con DDGS para '{query}': {e}")
            return []

    @staticmethod
    def _sync_fetch_content(url: str, max_chars: int = 2500) -> Optional[str]:
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
            if text:
                return text[:max_chars].strip()
            return None
        except Exception as e:
            logger.warning(f"Error extrayendo contenido de {url}: {e}")
            return None

    async def search(self, query: str, max_results: int = 4) -> List[Dict[str, str]]:
        """Realiza una búsqueda web pública de manera asíncrona."""
        logger.info(f"Ejecutando búsqueda web para: '{query}'")
        return await asyncio.to_thread(self._sync_search, query, max_results)

    async def fetch_page(self, url: str, max_chars: int = 2500) -> Optional[str]:
        """Descarga y extrae el texto limpio de un enlace web."""
        return await asyncio.to_thread(self._sync_fetch_content, url, max_chars)

    async def search_with_content(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """
        Busca en la web y complementa el snippet con extracción limpia del artículo
        para el resultado principal si es relevante.
        """
        results = await self.search(query, max_results=max_results)
        if not results:
            return []

        # Enriquecer el primer resultado con contenido limpio si el snippet es corto
        if results and len(results[0].get("snippet", "")) < 120:
            top_url = results[0]["url"]
            full_text = await self.fetch_page(top_url, max_chars=1200)
            if full_text:
                results[0]["snippet"] = full_text

        return results

    @staticmethod
    def format_results_for_prompt(results: List[Dict[str, str]]) -> str:
        """Formatea los resultados de búsqueda web para ser inyectados en el contexto del LLM."""
        if not results:
            return ""
        formatted_blocks = []
        for r in results:
            title = r.get("title", "")
            url = r.get("url", "")
            snippet = r.get("snippet", "")
            block = f"--- [Búsqueda web pública: {title} ({url})] ---\n{snippet}"
            formatted_blocks.append(block)
        return "\n\n".join(formatted_blocks)

web_search_service = WebSearchService()