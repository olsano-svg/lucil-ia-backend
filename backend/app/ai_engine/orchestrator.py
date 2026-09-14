import logging
from app.ai_engine.providers.base import BaseLLMProvider, BaseVoiceProvider, BaseVisionProvider
from app.ai_engine.providers.local_provider import LocalLLMProvider
from app.ai_engine.providers.openai_provider import OpenAIProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class SmartOrchestrator:
    """
    Orquestador Inteligente de Modelos.
    Prioriza el modelo local (Qwen 2.5 14B) sin requerir APIs externas ni costos.
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
        
        # 2. Opcional: Proveedor cloud como fallback si hay API Key configurada
        if settings.OPENAI_API_KEY:
            try:
                self.register_llm("openai_high", OpenAIProvider(model_name=settings.COMPLEX_TASK_MODEL))
                self.register_llm("openai_fast", OpenAIProvider(model_name=settings.ROUTING_MODEL))
            except Exception as e:
                logger.warning(f"No se pudo inicializar OpenAIProvider fallback: {e}")
        
    def register_llm(self, name: str, provider: BaseLLMProvider):
        self.llm_providers[name] = provider
        logger.info(f"Registered LLM Provider: {name}")
        
    def get_optimal_llm(self, task_type: str = "general") -> BaseLLMProvider:
        logger.info(f"Orchestrator selecting optimal model for task: {task_type}")
        if task_type in ["medical_analysis", "complex_reasoning", "coding"]:
            return self.llm_providers.get("high_reasoning", self.llm_providers.get("local"))
        return self.llm_providers.get("fast_tier", self.llm_providers.get("local"))
