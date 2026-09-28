import logging
from app.ai_engine.providers.base import BaseLLMProvider, BaseVoiceProvider, BaseVisionProvider
from app.ai_engine.providers.local_provider import LocalLLMProvider
from app.ai_engine.providers.openai_provider import OpenAIProvider
from app.ai_engine.providers.gemini_provider import GeminiProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

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
        pref_provider = settings.DEFAULT_LLM_PROVIDER.lower()
        
        if pref_provider in self.llm_providers:
            return self.llm_providers[pref_provider]

        # Si el proveedor preferido no está disponible, intentar Gemini o OpenAI o fallback a Local
        if "gemini" in self.llm_providers:
            return self.llm_providers["gemini"]
        if "openai" in self.llm_providers:
            return self.llm_providers["openai"]
            
        return self.llm_providers.get("local")

