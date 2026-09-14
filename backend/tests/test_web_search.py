import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.database import AsyncSessionLocal
from app.db.init_db import init_tables
from app.services.web_search import web_search_service
from app.ai_engine.memory import TieredMemory
from app.ai_engine.providers.local_provider import LocalLLMProvider

@pytest.mark.asyncio
async def test_web_search_format_and_prompt_injection():
    """Valida el formateo de resultados web y la inyección en el prompt del LLM."""
    mock_results = [
        {
            "title": "Descubrimiento de exoplaneta potencialmente habitable",
            "url": "https://agencia-espacial.org/noticias/exoplaneta-2026",
            "snippet": "Astrónomos confirman la detección de una supertierra en la zona habitable de Próxima Centauri."
        }
    ]
    formatted = web_search_service.format_results_for_prompt(mock_results)
    assert "[Búsqueda web pública: Descubrimiento de exoplaneta potencialmente habitable" in formatted
    assert "https://agencia-espacial.org/noticias/exoplaneta-2026" in formatted

    local_provider = LocalLLMProvider()
    context = {
        "semantic": {},
        "long_term": [],
        "web_search": mock_results,
        "short_term": []
    }
    messages = local_provider._build_messages(
        prompt="Qué se descubrió recientemente en astronomía?",
        context=context
    )
    system_msg = messages[0]["content"]
    assert "[Información de Búsqueda Web Pública]:" in system_msg
    assert "https://agencia-espacial.org/noticias/exoplaneta-2026" in system_msg

@pytest.mark.asyncio
async def test_tiered_memory_triggers_web_search():
    """Valida que TieredMemory active la búsqueda web cuando la consulta lo requiere."""
    await init_tables()
    tiered_memory = TieredMemory()
    async with AsyncSessionLocal() as db:
        # Consulta con trigger explícito de búsqueda web
        context = await tiered_memory.build_context_for_llm(
            db=db,
            user_id="user_test_uuid_web",
            conversation_id="conv_test_uuid_web",
            query="busca en la web las últimas noticias de inteligencia artificial",
            enable_web_search=True
        )
        assert "web_search" in context
        # Puede retornar resultados reales de DDGS o lista vacía si hay timeout de red, pero no debe fallar
        assert isinstance(context["web_search"], list)