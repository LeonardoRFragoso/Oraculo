"""
Router de Upload de Arquivos
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import logging
import os
from pathlib import Path
import uuid

from ..models import FileUploadResponse
from ..config import settings
from ..dependencies import get_data_ingestion_manager
from ..file_processor import FileProcessor

logger = logging.getLogger(__name__)

router = APIRouter()

# Instância global do processador
file_processor = FileProcessor()


def validate_file(file: UploadFile) -> None:
    """Validar arquivo"""
    # Verificar extensão
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensão {file_ext} não permitida. Permitidas: {settings.ALLOWED_EXTENSIONS}"
        )


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    ingestion_manager = None  # Depends(get_data_ingestion_manager)
):
    """
    Upload de arquivo
    
    Aceita arquivos Excel, CSV, PDF, DOCX, etc.
    Processa e adiciona à base de conhecimento.
    """
    try:
        # Validar arquivo
        validate_file(file)
        
        # Criar diretório de upload se não existir
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Gerar nome único
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        unique_filename = f"{file_id}{file_ext}"
        file_path = upload_dir / unique_filename
        
        # Salvar arquivo
        content = await file.read()
        file_size = len(content)
        
        # Verificar tamanho
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo muito grande. Máximo: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
            )
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Arquivo salvo: {file_path}")
        
        # Processar arquivo e extrair conteúdo
        processed = False
        extracted_content = None
        
        try:
            result = file_processor.process_file(str(file_path))
            processed = result['success']
            extracted_content = result['content']
            logger.info(f"Arquivo processado: {file.filename} ({result['char_count']} caracteres)")
        except Exception as e:
            logger.error(f"Erro ao processar arquivo: {e}")
            extracted_content = f"Erro ao processar: {str(e)}"
        
        return FileUploadResponse(
            success=True,
            message=f"Arquivo enviado e processado com sucesso. {len(extracted_content) if extracted_content else 0} caracteres extraídos.",
            file_id=file_id,
            filename=file.filename,
            size=file_size,
            processed=processed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao fazer upload: {str(e)}"
        )


@router.post("/upload/multiple", response_model=List[FileUploadResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(...)
):
    """
    Upload de múltiplos arquivos
    """
    results = []
    
    for file in files:
        try:
            result = await upload_file(file)
            results.append(result)
        except Exception as e:
            logger.error(f"Erro ao processar {file.filename}: {e}")
            results.append(FileUploadResponse(
                success=False,
                message=str(e),
                filename=file.filename,
                size=0,
                processed=False
            ))
    
    return results


@router.get("/files")
async def list_files():
    """
    Listar arquivos enviados
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    
    if not upload_dir.exists():
        return {"files": []}
    
    files = []
    for file_path in upload_dir.iterdir():
        if file_path.is_file():
            files.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "created": file_path.stat().st_ctime
            })
    
    return {"files": files}


@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """
    Deletar arquivo
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    
    # Procurar arquivo com o ID
    for file_path in upload_dir.glob(f"{file_id}.*"):
        if file_path.is_file():
            file_path.unlink()
            return {"success": True, "message": "Arquivo deletado"}
    
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")
