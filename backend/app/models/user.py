import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Uuid
from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Aquí podríamos agregar preferencias, configs específicas del usuario para aislar configuraciones
