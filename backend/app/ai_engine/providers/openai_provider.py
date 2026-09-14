import time
import logging
from typing import Any, Dict, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.ai_engine.providers.base import BaseLLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        # Inicializa LangChain ChatOpenAI. Requiere OPENAI_API_KEY en el entorno
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=settings.OPENAI_API_KEY,
            streaming=True,
            temperature=0.7
        )

    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        start_time = time.time()
        messages = self._build_messages(prompt, context)
        try:
            response = await self.llm.ainvoke(messages)
            elapsed = time.time() - start_time
            logger.info(f"OpenAIProvider ({self.model_name}) response time: {elapsed:.2f}s")
            return response.content
        except Exception as e:
            logger.error(f"Error in OpenAIProvider: {e}")
            raise

    async def generate_stream(self, prompt: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        start_time = time.time()
        messages = self._build_messages(prompt, context)
        try:
            async for chunk in self.llm.astream(messages):
                yield chunk.content
            elapsed = time.time() - start_time
            logger.info(f"OpenAIProvider ({self.model_name}) stream finished in: {elapsed:.2f}s")
        except Exception as e:
            logger.error(f"Error streaming from OpenAIProvider: {e}")
            raise

    def _build_messages(self, prompt: str, context: Dict[str, Any]) -> list:
        msgs = []
        # Inject System Prompt and Semantic Profile
        system_content = "Eres Lucil AI. Responde con neutralidad, objetividad y precisión médica si aplica."
        if context and context.get("semantic"):
            system_content += f" Preferencias del usuario: {context['semantic']}"
        msgs.append(SystemMessage(content=system_content))

        # Inject RAG / Long Term Context
        if context and context.get("long_term"):
            rag_info = "\n".join(context["long_term"])
            msgs.append(SystemMessage(content=f"Información relevante de tus documentos:\n{rag_info}"))

        # Inject Short Term History
        if context and context.get("short_term"):
            for msg in context["short_term"]:
                if msg.role == "user":
                    msgs.append(HumanMessage(content=msg.content))
                else:
                    msgs.append(AIMessage(content=msg.content))
                    
        msgs.append(HumanMessage(content=prompt))
        return msgs
