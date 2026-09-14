from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.document_processor import DocumentProcessor

router = APIRouter()

@router.post("/{project_id}/upload")
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para subir documentos (PDF, Word, Excel) a un proyecto.
    Integra los documentos en la memoria a largo plazo (Base de conocimiento).
    """
    if not file.filename.endswith((".pdf", ".docx", ".xlsx")):
        raise HTTPException(status_code=400, detail="Formato no soportado. Usa PDF, Word o Excel.")
        
    file_bytes = await file.read()
    
    # Extraer y procesar
    extracted_text = await DocumentProcessor.extract_text(file_bytes, file.filename)
    success = await DocumentProcessor.chunk_and_embed(
        text=extracted_text,
        project_id=project_id,
        filename=file.filename,
        user_id=str(current_user.id),
        db_session=db
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Error al indexar el documento en la base vectorial.")
        
    return {"message": f"Documento {file.filename} indexado exitosamente en la memoria del proyecto.", "status": "ok"}
