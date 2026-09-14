import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Uuid
from sqlalchemy.orm import relationship
from app.models.base import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid, ForeignKey("projects.id"), nullable=False)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    project = relationship("Project", back_populates="conversations", lazy="selectin")
    messages = relationship("Message", back_populates="conversation", lazy="selectin", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id = Column(Uuid, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False) # 'user' o 'assistant'
    content = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True) # Datos extra, tokens, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages", lazy="selectin")

