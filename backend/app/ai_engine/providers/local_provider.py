import time
import json
import logging
from typing import Any, Dict, List, AsyncGenerator
import httpx

from app.ai_engine.providers.base import BaseLLMProvider
from app.ai_engine.prompts import LUCIL_SYSTEM_PROMPT
from app.core.config import settings

logger = logging.getLogger(__name__)

class LocalLLMProvider(BaseLLMProvider):
    """
    Proveedor Local Desacoplado para Lucil AI conectado a Ollama.
    Permite inferencia 100% local, privada y sin cuotas ni APIs de pago.
    """
    def __init__(
        self,
        model_name: str = None,
        base_url: str = None,
        context_window: int = None,
        temperature: float = 0.7
    ):
        self.model_name = model_name or settings.LOCAL_MODEL_NAME
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.context_window = context_window or settings.LOCAL_CONTEXT_WINDOW
        self.temperature = temperature
        self.client_timeout = httpx.Timeout(180.0, connect=10.0)

    def _build_messages(self, prompt: str, context: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """Construye los mensajes estructurados inyectando el prompt del sistema, memoria y RAG."""
        messages: List[Dict[str, str]] = []

        # 1. System Prompt Base con los principios de Lucil
        system_content = LUCIL_SYSTEM_PROMPT.strip()

        # 2. Inyección de Memoria Semántica y Preferencias del Usuario
        if context and context.get("semantic"):
            semantic_data = context["semantic"]
            if isinstance(semantic_data, dict):
                pref_str = "\n".join(f"- {k}: {v}" for k, v in semantic_data.items())
            else:
                pref_str = str(semantic_data)
            system_content += f"\n\n[Recuerdos y Preferencias del Usuario]:\n{pref_str}"

        # 3. Inyección de Memoria a Largo Plazo / Documentos RAG
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

        # 3.1 Inyección de Búsqueda Web Pública
        if context and context.get("web_search"):
            web_data = context["web_search"]
            if isinstance(web_data, str) and web_data.strip():
                system_content += f"\n\n[Información de Búsqueda Web Pública]:\n{web_data.strip()}"
            elif isinstance(web_data, list) and len(web_data) > 0:
                from app.services.web_search import web_search_service
                formatted_web = web_search_service.format_results_for_prompt(web_data)
                if formatted_web:
                    system_content += f"\n\n[Información de Búsqueda Web Pública]:\n{formatted_web}"

        messages.append({"role": "system", "content": system_content})


        # 4. Inyección del Historial a Corto Plazo (últimos mensajes)
        if context and context.get("short_term"):
            for msg in context["short_term"]:
                role = "assistant" if msg.role in ["assistant", "ai"] else "user"
                messages.append({"role": role, "content": msg.content})

        # 5. Mensaje actual del usuario
        messages.append({"role": "user", "content": prompt})
        return messages

    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Genera una respuesta completa de texto usando el modelo local."""
        start_time = time.time()
        messages = self._build_messages(prompt, context)
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.context_window
            }
        }

        url = f"{self.base_url}/api/chat"
        try:
            async with httpx.AsyncClient(timeout=self.client_timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data.get("message", {}).get("content", "")
                elapsed = time.time() - start_time
                logger.info(f"LocalLLMProvider ({self.model_name}) respondió en {elapsed:.2f}s")
                return content
        except Exception as e:
            logger.error(f"Error en LocalLLMProvider.generate_response: {e}")
            raise

    async def generate_stream(self, prompt: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """Genera un flujo de texto en tiempo real (streaming) mediante chunks."""
        start_time = time.time()
        messages = self._build_messages(prompt, context)
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.context_window
            }
        }

        url = f"{self.base_url}/api/chat"
        try:
            async with httpx.AsyncClient(timeout=self.client_timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk_json = json.loads(line)
                            chunk_text = chunk_json.get("message", {}).get("content", "")
                            if chunk_text:
                                yield chunk_text
                            if chunk_json.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
            elapsed = time.time() - start_time
            logger.info(f"LocalLLMProvider ({self.model_name}) streaming finalizado en {elapsed:.2f}s")
        except Exception as e:
            logger.error(f"Error en LocalLLMProvider.generate_stream: {e}")
            raise
