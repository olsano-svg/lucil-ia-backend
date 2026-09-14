from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        pass
        
    @abstractmethod
    async def generate_stream(self, prompt: str, context: Dict[str, Any] = None):
        pass

class BaseVoiceProvider(ABC):
    async def text_to_speech(self, text: str) -> bytes:
        raise NotImplementedError("text_to_speech no está implementado en este proveedor")
        
    async def speech_to_text(self, audio_bytes: bytes) -> str:
        raise NotImplementedError("speech_to_text no está implementado en este proveedor")

class BaseVisionProvider(ABC):
    @abstractmethod
    async def analyze_image(self, image_bytes: bytes, prompt: str) -> str:
        pass

class BaseEmbeddingProvider(ABC):
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        pass

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [await self.get_embedding(t) for t in texts]

