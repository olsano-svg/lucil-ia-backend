import logging
import io
from typing import List

# Importaciones requeridas para el procesamiento real
import PyPDF2
import docx
import pandas as pd

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Procesador de Documentos Real para Ingesta en Base de Conocimiento.
    Soporta PDF, Word (docx), Excel (xlsx).
    """
    
    @staticmethod
    async def extract_text(file_bytes: bytes, filename: str) -> str:
        """Extrae texto real de los documentos basado en su extensión."""
        logger.info(f"Extrayendo texto de {filename}...")
        text = ""
        
        try:
            if filename.lower().endswith(".pdf"):
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                for page in pdf_reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            
            elif filename.lower().endswith(".docx"):
                doc = docx.Document(io.BytesIO(file_bytes))
                for para in doc.paragraphs:
                    text += para.text + "\n"
                    
            elif filename.lower().endswith(".xlsx"):
                df = pd.read_excel(io.BytesIO(file_bytes))
                # Convertimos el excel a una representación tabular en texto
                text = df.to_string()
                
            else:
                raise ValueError("Formato de archivo no soportado.")
                
            return text.strip()
        except Exception as e:
            logger.error(f"Error procesando documento {filename}: {e}")
            raise

    @staticmethod
    def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        """
        Divide el texto en fragmentos (chunks) respetando párrafos, oraciones o palabras,
        manteniendo un solapamiento (overlap) para no perder contexto semántico.
        """
        if not text:
            return []
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = min(start + chunk_size, text_len)
            if end == text_len:
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break

            # Buscar límites naturales de salto de línea, punto y seguido o espacio
            boundary = text.rfind("\n", start, end)
            if boundary == -1 or boundary <= start + (chunk_size // 2):
                boundary = text.rfind(". ", start, end)
                if boundary != -1:
                    boundary += 1  # Incluir el punto
            if boundary == -1 or boundary <= start + (chunk_size // 2):
                boundary = text.rfind(" ", start, end)
            if boundary == -1 or boundary <= start:
                boundary = end

            chunk = text[start:boundary].strip()
            if chunk:
                chunks.append(chunk)

            next_start = boundary - chunk_overlap
            if next_start <= start:
                next_start = boundary
            start = next_start

        return chunks

    @staticmethod
    async def chunk_and_embed(
        text: str,
        project_id: str,
        filename: str = "documento",
        user_id: str = "",
        db_session = None
    ) -> bool:
        """
        Divide el texto en fragmentos (chunks) y genera embeddings en la base vectorial local ChromaDB.
        100% privado, local y sin llamadas a APIs externas.
        """
        from app.services.vector_store import vector_store

        logger.info(f"Fragmentando texto e indexando en ChromaDB para el proyecto {project_id} (archivo: {filename})...")
        chunks = DocumentProcessor.split_text(text, chunk_size=1000, chunk_overlap=200)
        if not chunks:
            logger.warning(f"No se generaron fragmentos para {filename}.")
            return False

        metadatas = [
            {
                "project_id": str(project_id),
                "filename": filename,
                "user_id": str(user_id) if user_id else "anonymous"
            }
            for _ in chunks
        ]

        try:
            await vector_store.add_documents(documents=chunks, metadatas=metadatas)
            logger.info(f"Éxito: {len(chunks)} fragmentos de '{filename}' indexados localmente en ChromaDB.")
            return True
        except Exception as e:
            logger.error(f"Error indexando en base vectorial local: {e}")
            raise

