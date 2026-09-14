import pytest
import pytest_asyncio
from app.ai_engine.providers.voice_provider import DeepgramSTTProvider, ElevenLabsTTSProvider
from app.ai_engine.providers.vision_provider import OpenAIVisionProvider

@pytest.mark.asyncio
async def test_stt_provider_decoupled():
    stt = DeepgramSTTProvider(api_key="test_key")
    # Mocking actual audio bytes
    audio = b"fake_audio_stream"
    text = await stt.speech_to_text(audio)
    assert isinstance(text, str)
    assert len(text) > 0

@pytest.mark.asyncio
async def test_tts_provider_decoupled():
    tts = ElevenLabsTTSProvider(api_key="test_key")
    text = "Hola, probando síntesis de voz."
    audio_out = await tts.text_to_speech(text)
    assert isinstance(audio_out, bytes)
    assert len(audio_out) > 0

@pytest.mark.asyncio
async def test_vision_provider():
    vision = OpenAIVisionProvider(api_key="test_key")
    image_bytes = b"fake_image"
    prompt = "¿Qué hay en la imagen?"
    response = await vision.analyze_image(image_bytes, prompt)
    assert isinstance(response, str)
    assert len(response) > 0
