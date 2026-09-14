import pytest
from app.ai_engine.providers.local_provider import LocalLLMProvider
from app.models.user import User
from app.models.project import Project
from app.models.conversation import Message

def test_local_provider_message_building():
    provider = LocalLLMProvider(model_name="qwen2.5:14b")
    
    mock_msg1 = Message(id="1", conversation_id="conv-1", role="user", content="Hola anterior")
    mock_msg2 = Message(id="2", conversation_id="conv-1", role="assistant", content="Respuesta anterior")
    
    context = {
        "semantic": {"idioma": "español", "tono": "profesional"},
        "long_term": ["Documento médico: El paracetamol es un analgésico."],
        "short_term": [mock_msg1, mock_msg2]
    }
    
    messages = provider._build_messages("¿Qué me puedes decir?", context)
    
    assert len(messages) == 4
    # System prompt con semantic y RAG
    assert messages[0]["role"] == "system"
    assert "Lucil AI" in messages[0]["content"]
    assert "Documento médico" in messages[0]["content"]
    assert "idioma" in messages[0]["content"]
    
    # Historial
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Hola anterior"
    assert messages[2]["role"] == "assistant"
    assert messages[2]["content"] == "Respuesta anterior"
    
    # Prompt actual
    assert messages[3]["role"] == "user"
    assert messages[3]["content"] == "¿Qué me puedes decir?"

@pytest.mark.asyncio
async def test_local_provider_real_inference():
    provider = LocalLLMProvider(model_name="qwen2.5:14b")
    response = await provider.generate_response("Responde solo: 'TEST_OK'")
    assert "TEST_OK" in response

@pytest.mark.asyncio
async def test_local_provider_real_stream():
    provider = LocalLLMProvider(model_name="qwen2.5:14b")
    chunks = []
    async for chunk in provider.generate_stream("Di los números del 1 al 3"):
        chunks.append(chunk)
    full_text = "".join(chunks)
    assert len(full_text) > 0
