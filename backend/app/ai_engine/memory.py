import uuid
import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.models.conversation import Message
from app.models.memory import MemoryItem

logger = logging.getLogger(__name__)

class TieredMemory:
    """
    Gestión de Memoria por Capas, estrictamente aislada por usuario.
    Integra recuerdos dinámicos (CRUD), historial reciente y RAG.
    """
    def __init__(self):
        pass

    async def get_short_term_context(self, db: AsyncSession, user_id: str, conversation_id: str) -> List[Message]:
        """Recupera contexto corto plazo aislado por usuario y sesión."""
        try:
            cid = uuid.UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
        except Exception:
            return []

        result = await db.execute(
            select(Message)
            .filter(Message.conversation_id == cid)
            .order_by(desc(Message.created_at))
            .limit(10)
        )
        messages = result.scalars().all()
        # Invertimos para orden cronológico
        return messages[::-1]


    async def retrieve_long_term_memory(
        self,
        query: str,
        user_id: str,
        project_id: str = None,
        n_results: int = 4
    ) -> List[Dict[str, Any]]:
        """Busca en la base vectorial ChromaDB filtrando por user_id y project_id."""
        from app.services.vector_store import vector_store

        if not query:
            return []

        try:
            where_filter = None
            if user_id and project_id:
                where_filter = {"$and": [{"user_id": str(user_id)}, {"project_id": str(project_id)}]}
            elif user_id:
                where_filter = {"user_id": str(user_id)}
            elif project_id:
                where_filter = {"project_id": str(project_id)}

            results = await vector_store.similarity_search(
                query=query,
                n_results=n_results,
                where=where_filter
            )
            return results
        except Exception as e:
            logger.error(f"Error recuperando memoria a largo plazo (RAG) para user {user_id}: {e}")
            return []
        
    async def get_semantic_profile(self, db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """Recupera recuerdos y preferencias reales del usuario desde la tabla user_memories."""
        try:
            uid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            result = await db.execute(
                select(MemoryItem).filter(MemoryItem.user_id == uid).order_by(desc(MemoryItem.created_at))
            )
            items = result.scalars().all()
            if not items:
                return {}
            
            profile: Dict[str, List[str]] = {}
            for item in items:
                cat = item.category or "general"
                if cat not in profile:
                    profile[cat] = []
                profile[cat].append(item.fact)
            return profile
        except Exception as e:
            logger.error(f"Error recuperando recuerdos para user {user_id}: {e}")
            return {}
        
    async def build_context_for_llm(
        self,
        db: AsyncSession,
        user_id: str,
        conversation_id: str,
        query: str,
        enable_web_search: bool = False
    ) -> Dict[str, Any]:
        """Construye el contexto combinando las 4 capas: corto plazo, perfil semántico, RAG y búsqueda web."""
        
        # 1. Obtener Historial Corto (Chat DB)
        short_term = await self.get_short_term_context(db, user_id, conversation_id)
        
        # 2. Obtener Perfil (Memoria Semántica / Recuerdos guardados por el usuario)
        semantic = await self.get_semantic_profile(db, user_id)
        
        # 3. Vector RAG (Documentos e Información de proyectos)
        long_term = await self.retrieve_long_term_memory(query=query, user_id=user_id)
        
        # 4. Búsqueda Web Pública (si el usuario la activa o si la consulta lo requiere)
        web_search_results = []
        should_search = enable_web_search
        if not should_search and query:
            q_lower = query.lower()
            triggers = [
                "busca en la web", "buscar en la web", "busca en internet", "buscar en internet",
                "noticias de", "últimas noticias", "noticia de", "precio actual",
                "cotización de", "busca sobre", "search the web", "busca qué", "busca quien",
                "busca quién", "busca dónde", "busca donde", "busca cuándo", "busca cuando",
                "¿qué pasó con", "que paso con", "hoy en día", "actualidad"
            ]
            should_search = any(t in q_lower for t in triggers)

        if should_search and query:
            from app.services.web_search import web_search_service
            try:
                clean_query = query
                for t in ["busca en la web", "busca en internet", "buscar en internet", "busca sobre"]:
                    clean_query = clean_query.replace(t, "").replace(t.title(), "")
                clean_query = clean_query.strip(" :¿?¡!,.")
                if not clean_query:
                    clean_query = query
                web_search_results = await web_search_service.search_with_content(clean_query, max_results=3)
            except Exception as e:
                logger.error(f"Error en búsqueda web para '{query}': {e}")

        return {
            "short_term": short_term,
            "long_term": long_term, 
            "semantic": semantic,
            "web_search": web_search_results
        }


