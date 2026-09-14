import pytest
import pytest_asyncio
from app.ai_engine.orchestrator import SmartOrchestrator
from app.ai_engine.providers.base import BaseLLMProvider

class MockLLMProvider(BaseLLMProvider):
    async def generate_response(self, prompt: str, context: dict = None) -> str:
        return f"Mocked response to: {prompt}"
        
    async def generate_stream(self, prompt: str, context: dict = None):
        yield "Mocked "
        yield "stream "
        yield "response"

@pytest.fixture
def orchestrator():
    orchestrator = SmartOrchestrator()
    orchestrator.register_llm("fast_tier", MockLLMProvider())
    orchestrator.register_llm("high_reasoning", MockLLMProvider())
    return orchestrator

def test_orchestrator_routing(orchestrator):
    # Test task routing
    fast_llm = orchestrator.get_optimal_llm("general")
    assert fast_llm is not None
    
    complex_llm = orchestrator.get_optimal_llm("complex_reasoning")
    assert complex_llm is not None

@pytest.mark.asyncio
async def test_mock_provider_stream(orchestrator):
    llm = orchestrator.get_optimal_llm("general")
    chunks = []
    async for chunk in llm.generate_stream("Hello"):
        chunks.append(chunk)
        
    assert "".join(chunks) == "Mocked stream response"
