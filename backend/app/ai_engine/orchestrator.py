import logging
from app.ai_engine.providers.base import BaseLLMProvider, BaseVoiceProvider, BaseVisionProvider
from app.ai_engine.providers.local_provider import LocalLLMProvider
from app.ai_engine.providers.openai_provider import OpenAIProvider
from app.ai_engine.providers.gemini_provider import GeminiProvider
from app.core.config import settings

from typing import List, Dict, Any, AsyncGenerator

logger = logging.getLogger(__name__)

class ResilientLLMProvider(BaseLLMProvider):
    """
    Proveedor resiliente que intenta proveedores en cascada:
    1. Proveedores Cloud (Gemini, OpenAI) si están configurados
    2. Proveedor preferido (Local Ollama)
    3. Si todos fallan o la conexión local no está disponible en la nube (Render),
       devuelve un mensaje claro explicando cómo activar el servicio.
    """
    def __init__(self, orchestrator: "SmartOrchestrator"):
        self.orchestrator = orchestrator

    def _get_candidate_providers(self) -> List[tuple[str, BaseLLMProvider]]:
        candidates = []
        pref_name = settings.DEFAULT_LLM_PROVIDER.lower()

        # Priorizar proveedores Cloud si hay clave de API válida configurada en el servidor
        if settings.GEMINI_API_KEY and "gemini" in self.orchestrator.llm_providers:
            candidates.append(("gemini", self.orchestrator.llm_providers["gemini"]))
        if settings.OPENAI_API_KEY and "openai" in self.orchestrator.llm_providers:
            candidates.append(("openai", self.orchestrator.llm_providers["openai"]))

        # Añadir proveedor preferido si no está en la lista
        if pref_name in self.orchestrator.llm_providers:
            if not any(name == pref_name for name, _ in candidates):
                candidates.append((pref_name, self.orchestrator.llm_providers[pref_name]))
        elif "local" in self.orchestrator.llm_providers:
            if not any(name == "local" for name, _ in candidates):
                candidates.append(("local", self.orchestrator.llm_providers["local"]))

        return candidates

    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        candidates = self._get_candidate_providers()
        errors = []
        for name, provider in candidates:
            try:
                logger.info(f"Intentando generar respuesta con proveedor LLM: {name}")
                res = await provider.generate_response(prompt, context)
                if res and res.strip():
                    return res
            except Exception as e:
                logger.warning(f"Proveedor '{name}' falló: {e}")
                errors.append(f"{name}: {str(e)}")

        return (
            "⚠️ **Lucil AI está activa en Render**, pero actualmente no se puede conectar a un motor de IA.\n\n"
            "**Instrucciones para activarla:**\n"
            "1. **En Render (Nube)**: Agrega la variable de entorno `GEMINI_API_KEY` (clave gratuita de Google AI Studio) o `OPENAI_API_KEY` en el panel de Render.\n"
            "2. **En tu PC (Local)**: Si ejecutas el backend localmente, asegúrate de tener Ollama abierto en `http://localhost:11434` con el modelo Qwen 2.5."
        )

    async def generate_stream(self, prompt: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        candidates = self._get_candidate_providers()
        success = False

        for name, provider in candidates:
            try:
                logger.info(f"Intentando streaming con proveedor LLM: {name}")
                chunk_count = 0
                async for chunk in provider.generate_stream(prompt, context):
                    chunk_count += 1
                    yield chunk
                if chunk_count > 0:
                    success = True
                    break
            except Exception as e:
                logger.warning(f"Streaming con proveedor '{name}' falló: {e}")

        if not success:
            fallback_msg = (
                "⚠️ **Lucil AI está activa en Render**, pero actualmente no se puede conectar a un motor de IA.\n\n"
                "**Instrucciones para activarla:**\n"
                "1. **En Render (Nube)**: Agrega la variable de entorno `GEMINI_API_KEY` (clave gratuita de Google AI Studio) o `OPENAI_API_KEY` en el panel de Render.\n"
                "2. **En tu PC (Local)**: Si ejecutas el backend localmente, asegúrate de tener Ollama abierto en `http://localhost:11434` con el modelo Qwen 2.5."
            )
            yield fallback_msg

class SmartOrchestrator:
    """
    Orquestador Inteligente de Modelos.
    Soporta modelo local (Ollama + Qwen 2.5 14B), Google Gemini y OpenAI.
    Configurable vía variables de entorno (DEFAULT_LLM_PROVIDER, GEMINI_API_KEY, OPENAI_API_KEY).
    """
    def __init__(self):
        self.llm_providers = {}
        
        # 1. Registrar proveedor local autónomo (Ollama)
        local_provider = LocalLLMProvider(
            model_name=settings.LOCAL_MODEL_NAME,
            base_url=settings.OLLAMA_BASE_URL,
            context_window=settings.LOCAL_CONTEXT_WINDOW
        )
        self.register_llm("local", local_provider)
        self.register_llm("fast_tier", local_provider)
        self.register_llm("high_reasoning", local_provider)
        
        # 2. Registrar proveedor Gemini si hay API key
        if getattr(settings, "GEMINI_API_KEY", None):
            try:
                gemini_provider = GeminiProvider(
                    model_name=getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash"),
                    api_key=settings.GEMINI_API_KEY
                )
                self.register_llm("gemini", gemini_provider)
                logger.info("GeminiProvider inicializado correctamente.")
            except Exception as e:
                logger.warning(f"No se pudo inicializar GeminiProvider: {e}")

        # 3. Registrar proveedor OpenAI si hay API key
        if settings.OPENAI_API_KEY:
            try:
                high_model = getattr(settings, "COMPLEX_TASK_MODEL", "gpt-4o")
                fast_model = getattr(settings, "ROUTING_MODEL", "gpt-4o-mini")
                openai_provider = OpenAIProvider(model_name=fast_model)
                self.register_llm("openai", openai_provider)
                self.register_llm("openai_high", OpenAIProvider(model_name=high_model))
                self.register_llm("openai_fast", openai_provider)
                logger.info("OpenAIProvider inicializado correctamente.")
            except Exception as e:
                logger.warning(f"No se pudo inicializar OpenAIProvider fallback: {e}")

    def register_llm(self, name: str, provider: BaseLLMProvider):
        self.llm_providers[name] = provider
        logger.info(f"Registered LLM Provider: {name}")
        
    def get_optimal_llm(self, task_type: str = "general") -> BaseLLMProvider:
        logger.info(f"Orchestrator selecting optimal model for task: {task_type}")
        return ResilientLLMProvider(self)


