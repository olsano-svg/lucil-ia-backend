import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.memory import MemoryItem
from app.schemas.memory import MemoryCreate, MemoryUpdate, MemoryResponse

router = APIRouter()

@router.get("/", response_model=List[MemoryResponse])
async def list_memories(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene la lista de recuerdos del usuario, con filtro opcional por categoría."""
    query = select(MemoryItem).filter(MemoryItem.user_id == current_user.id)
    if category:
        query = query.filter(MemoryItem.category == category)
    query = query.order_by(desc(MemoryItem.created_at))
    
    result = await db.execute(query)
    memories = result.scalars().all()
    return memories

@router.post("/", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    mem_in: MemoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Guarda un nuevo recuerdo o preferencia del usuario."""
    new_memory = MemoryItem(
        user_id=current_user.id,
        category=mem_in.category or "general",
        fact=mem_in.fact.strip()
    )
    db.add(new_memory)
    await db.commit()
    await db.refresh(new_memory)
    return new_memory

@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Consulta un recuerdo específico."""
    result = await db.execute(
        select(MemoryItem).filter(MemoryItem.id == memory_id, MemoryItem.user_id == current_user.id)
    )
    memory = result.scalars().first()
    if not memory:
        raise HTTPException(status_code=404, detail="Recuerdo no encontrado.")
    return memory

@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: uuid.UUID,
    mem_in: MemoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modifica o corrige un recuerdo existente."""
    result = await db.execute(
        select(MemoryItem).filter(MemoryItem.id == memory_id, MemoryItem.user_id == current_user.id)
    )
    memory = result.scalars().first()
    if not memory:
        raise HTTPException(status_code=404, detail="Recuerdo no encontrado.")
        
    if mem_in.category is not None:
        memory.category = mem_in.category
    if mem_in.fact is not None:
        memory.fact = mem_in.fact.strip()
        
    await db.commit()
    await db.refresh(memory)
    return memory

@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina definitivamente un recuerdo."""
    result = await db.execute(
        select(MemoryItem).filter(MemoryItem.id == memory_id, MemoryItem.user_id == current_user.id)
    )
    memory = result.scalars().first()
    if not memory:
        raise HTTPException(status_code=404, detail="Recuerdo no encontrado.")
        
    await db.delete(memory)
    await db.commit()
    return None
