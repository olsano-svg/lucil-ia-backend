import os
import uuid
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.ai_engine.providers.embedding_provider import LocalEmbeddingProvider

logger = logging.getLogger(__name__)

class VectorStoreService:
    """
    Servicio de Base de Datos Vectorial Local basado en ChromaDB.
    Almacena fragmentos de texto (chunks) indexados con nomic-embed-text
    para recuperación semántica (RAG) 100% privada y local.
    """
    _instance: Optional["VectorStoreService"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, persist_dir: str = None):
        if getattr(self, "_initialized", False):
            return
        self.persist_dir = persist_dir or settings.VECTOR_DB_DIR
        os.makedirs(self.persist_dir, exist_ok=True)
        
        logger.info(f"Inicializando ChromaDB PersistentClient en: {self.persist_dir}")
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.embedder = LocalEmbeddingProvider(
            model_name=settings.LOCAL_EMBEDDING_MODEL,
            base_url=settings.OLLAMA_BASE_URL
        )
        self._initialized = True

    def get_collection(self, collection_name: str = "lucil_knowledge"):
        """Obtiene o crea una colección de vectores."""
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    async def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
        collection_name: str = "lucil_knowledge"
    ) -> List[str]:
        """
        Genera embeddings para los fragmentos y los inserta en ChromaDB.
        """
        if not documents:
            return []

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        if len(metadatas) != len(documents):
            raise ValueError("La cantidad de metadatos debe coincidir con la cantidad de documentos.")

        sanitized_metadatas = []
        for m in metadatas:
            clean_m = {}
            for k, v in m.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_m[k] = v
                elif v is not None:
                    clean_m[k] = str(v)
            sanitized_metadatas.append(clean_m)

        collection = self.get_collection(collection_name)
        embeddings = await self.embedder.get_embeddings(documents)

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=sanitized_metadatas,
            embeddings=embeddings
        )

        logger.info(f"Indexados {len(documents)} fragmentos en la colección '{collection_name}'")
        return ids

    async def similarity_search(
        self,
        query: str,
        n_results: int = 4,
        where: Optional[Dict[str, Any]] = None,
        collection_name: str = "lucil_knowledge"
    ) -> List[Dict[str, Any]]:
        """
        Busca los fragmentos más similares a la consulta semántica.
        Retorna lista de diccionarios con content, metadata, distance e id.
        """
        collection = self.get_collection(collection_name)
        count = collection.count()
        if count == 0:
            return []

        actual_n = min(n_results, count)
        query_embedding = await self.embedder.get_embedding(query)

        query_kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": actual_n
        }
        if where:
            query_kwargs["where"] = where

        try:
            results = collection.query(**query_kwargs)
        except Exception as e:
            logger.warning(f"Error en query de ChromaDB con where={where}: {e}")
            return []

        items: List[Dict[str, Any]] = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            dists = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
            doc_ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

            for doc, meta, dist, doc_id in zip(docs, metas, dists, doc_ids):
                items.append({
                    "id": doc_id,
                    "content": doc,
                    "metadata": meta,
                    "distance": dist
                })

        return items

    async def delete_by_metadata(
        self,
        where: Dict[str, Any],
        collection_name: str = "lucil_knowledge"
    ) -> None:
        """Elimina documentos que coincidan con los metadatos indicados."""
        collection = self.get_collection(collection_name)
        collection.delete(where=where)
        logger.info(f"Eliminados documentos en '{collection_name}' con filtro: {where}")

    async def delete_documents(
        self,
        ids: List[str],
        collection_name: str = "lucil_knowledge"
    ) -> None:
        """Elimina documentos por sus IDs."""
        collection = self.get_collection(collection_name)
        collection.delete(ids=ids)
        logger.info(f"Eliminados {len(ids)} documentos en '{collection_name}'")

    def count(self, collection_name: str = "lucil_knowledge") -> int:
        """Retorna el total de vectores indexados en la colección."""
        collection = self.get_collection(collection_name)
        return collection.count()

# Instancia global reutilizable
vector_store = VectorStoreService()