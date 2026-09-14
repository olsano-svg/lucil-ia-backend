import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class MemoryCreate(BaseModel):
    category: Optional[str] = "general"
    fact: str

class MemoryUpdate(BaseModel):
    category: Optional[str] = None
    fact: Optional[str] = None

class MemoryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category: str
    fact: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
