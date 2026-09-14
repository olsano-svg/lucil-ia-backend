import uuid
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List


from app.db.database import get_db, AsyncSessionLocal
from app.models.conversation import Conversation, Message
from app.schemas.conversation import ConversationCreate, ConversationResponse, MessageCreate, MessageResponse
from app.api.deps import get_current_user
from app.models.user import User

from app.ai_engine.orchestrator import SmartOrchestrator
from app.ai_engine.memory import TieredMemory
from app.ai_engine.providers.voice_provider import DeepgramSTTProvider, ElevenLabsTTSProvider

router = APIRouter()

ai_orchestrator = SmartOrchestrator()
tiered_memory = TieredMemory()

from app.models.project import Project

@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    conv_in: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensure project exists or create a default one for the personal user
    result = await db.execute(select(Project).filter(Project.user_id == current_user.id))
    project = result.scalars().first()
    
    if not project:
        project = Project(name="Default Project", user_id=current_user.id)
        db.add(project)
        await db.commit()
        await db.refresh(project)
        
    conv = Conversation(title=conv_in.title, project_id=project.id)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    conv.messages = []
    return conv

@router.get("/", response_model=List[ConversationResponse])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Project).filter(Project.user_id == current_user.id))
    project = result.scalars().first()
    if not project:
        return []
    conv_result = await db.execute(
        select(Conversation)
        .filter(Conversation.project_id == project.id)
        .order_by(Conversation.created_at.desc())
    )
    return conv_result.scalars().all()

@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: str,
    msg_in: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cid = uuid.UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
    user_msg = Message(conversation_id=cid, role=msg_in.role, content=msg_in.content)
    db.add(user_msg)
    await db.commit()

    llm = ai_orchestrator.get_optimal_llm()
    context = await tiered_memory.build_context_for_llm(
        db,
        str(current_user.id),
        str(cid),
        msg_in.content,
        enable_web_search=getattr(msg_in, "enable_web_search", False) or False
    )
    
    response_content = await llm.generate_response(msg_in.content, context)
    
    lucil_msg = Message(conversation_id=cid, role="assistant", content=response_content)
    db.add(lucil_msg)
    await db.commit()
    await db.refresh(lucil_msg)
    return lucil_msg

@router.post("/{conversation_id}/stream")
async def stream_message(
    conversation_id: str,
    msg_in: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cid = uuid.UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
    user_msg = Message(conversation_id=cid, role=msg_in.role, content=msg_in.content)
    db.add(user_msg)
    await db.commit()

    llm = ai_orchestrator.get_optimal_llm()
    context = await tiered_memory.build_context_for_llm(
        db,
        str(current_user.id),
        str(cid),
        msg_in.content,
        enable_web_search=getattr(msg_in, "enable_web_search", False) or False
    )

    async def event_generator():
        full_response = ""
        if llm:
            async for chunk in llm.generate_stream(msg_in.content, context):
                full_response += chunk
                yield f"data: {chunk}\n\n"
        else:
            yield "data: Error: No LLM provider configured.\n\n"
            
        yield "data: [DONE]\n\n"

        # Guardar respuesta generada en la base de datos de forma persistente
        if full_response.strip():
            try:
                async with AsyncSessionLocal() as save_db:
                    assistant_msg = Message(
                        conversation_id=cid,
                        role="assistant",
                        content=full_response
                    )
                    save_db.add(assistant_msg)
                    await save_db.commit()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error guardando mensaje de streaming: {e}")
        
    return StreamingResponse(event_generator(), media_type="text/event-stream")



@router.websocket("/{conversation_id}/voice")
async def voice_websocket(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    stt = DeepgramSTTProvider(api_key="mock")
    tts = ElevenLabsTTSProvider(api_key="mock")
    
    async with AsyncSessionLocal() as db:
        user_id_mock = "mock_user_id" 
        try:
            while True:
                audio_data = await websocket.receive_bytes()
                text_input = await stt.speech_to_text(audio_data)
                await websocket.send_json({"event": "stt_result", "text": text_input})
                
                llm = ai_orchestrator.get_optimal_llm()
                context = await tiered_memory.build_context_for_llm(db, user_id_mock, conversation_id, text_input)
                
                response_text = await llm.generate_response(text_input, context)
                await websocket.send_json({"event": "llm_result", "text": response_text})
                
                audio_out = await tts.text_to_speech(response_text)
                await websocket.send_bytes(audio_out)
                
        except WebSocketDisconnect:
            pass

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Conversation).filter(Conversation.id == conversation_id))
    conv = result.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    msg_result = await db.execute(select(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at))
    conv.messages = msg_result.scalars().all()
    
    return conv
