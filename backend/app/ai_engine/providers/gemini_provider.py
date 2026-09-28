import time
import json
import logging
from typing import Any, Dict, List, AsyncGenerator
import httpx

from app.ai_engine.providers.base import BaseLLMProvider
from app.ai_engine.prompts import LUCIL_SYSTEM_PROMPT
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiProvider(BaseLLMProvider):
    """
    Proveedor de IA Cloud para Google Gemini mediante API REST (con streaming SSE).
    No expone ninguna clave en el cliente y se configura mediante GEMINI_API_KEY en el backend.
    """
    def __init__(
        self,
        model_name: str = None,
        api_key: str = None,
        temperature: float = 0.7
    ):
        self.model_name = model_name or getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash")
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", "")
        self.temperature = temperature
        self.client_timeout = httpx.Timeout(120.0, connect=10.0)

    def _build_payload(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        system_content = LUCIL_SYSTEM_PROMPT.strip()

        if context and context.get("semantic"):
            semantic_data = context["semantic"]
            pref_str = "\n".join(f"- {k}: {v}" for k, v in semantic_data.items()) if isinstance(semantic_data, dict) else str(semantic_data)
            system_content += f"\n\n[Recuerdos y Preferencias del Usuario]:\n{pref_str}"

        if context and context.get("long_term"):
            long_term_docs = context["long_term"]
            if isinstance(long_term_docs, list) and len(long_term_docs) > 0:
                formatted_docs = []
                for doc in long_term_docs:
                    if isinstance(doc, dict):
                        fname = doc.get("metadata", {}).get("filename", "Documento personal")
                        content = doc.get("content", "")
                        formatted_docs.append(f"--- [Documento propio: {fname}] ---\n{content}")
                    else:
                        formatted_docs.append(str(doc))
                rag_joined = "\n\n".join(formatted_docs)
                system_content += f"\n\n[Información Recuperada de tus Documentos en Memoria]:\n{rag_joined}"

        if context and context.get("web_search"):
            web_data = context["web_search"]
            if isinstance(web_data, str) and web_data.strip():
                system_content += f"\n\n[Información de Búsqueda Web Pública]:\n{web_data.strip()}"

        contents: List[Dict[str, Any]] = []

        if context and context.get("short_term"):
            for msg in context["short_term"]:
                role = "model" if getattr(msg, "role", "") in ["assistant", "ai", "model"] else "user"
                contents.append({
                    "role": role,
                    "parts": [{"text": getattr(msg, "content", "")}]
                })

        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        return {
            "system_instruction": {
                "parts": [{"text": system_content}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature
            }
        }

    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno del servidor.")

        start_time = time.time()
        payload = self._build_payload(prompt, context)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=self.client_timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                candidates = data.get("candidates", [])
                if not candidates:
                    return "No se obtuvo respuesta del proveedor Gemini."
                
                parts = candidates[0].get("content", {}).get("parts", [])
                text_result = "".join(part.get("text", "") for part in parts)
                
                elapsed = time.time() - start_time
                logger.info(f"GeminiProvider ({self.model_name}) respondió en {elapsed:.2f}s")
                return text_result
        except Exception as e:
            logger.error(f"Error en GeminiProvider.generate_response: {e}")
            raise

    async def generate_stream(self, prompt: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno del servidor.")

        start_time = time.time()
        payload = self._build_payload(prompt, context)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:streamGenerateContent?key={self.api_key}&alt=sse"

        try:
            async with httpx.AsyncClient(timeout=self.client_timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        json_str = line[6:].strip()
                        if not json_str:
                            continue
                        try:
                            chunk_data = json.loads(json_str)
                            candidates = chunk_data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for p in parts:
                                    chunk_text = p.get("text", "")
                                    if chunk_text:
                                        yield chunk_text
                        except json.JSONDecodeError:
                            continue
            elapsed = time.time() - start_time
            logger.info(f"GeminiProvider ({self.model_name}) streaming finalizado en {elapsed:.2f}s")
        except Exception as e:
            logger.error(f"Error en GeminiProvider.generate_stream: {e}")
            raise
