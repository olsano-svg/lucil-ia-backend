import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Uuid, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class MemoryItem(Base):
    """
    Recuerdo persistente del usuario (Memoria Semántica y Preferencias).
    Permite consultar, editar y borrar recuerdos directamente.
    """
    __tablename__ = "user_memories"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String, default="general", index=True) # ej: "salud", "preferencias", "personal", "tecnologia"
    fact = Column(Text, nullable=False) # El hecho o recuerdo concreto
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="memories")
