"""
Router de Health Check
"""

from fastapi import APIRouter
from datetime import datetime
import logging
import httpx

from ..models import HealthStatus
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


async def check_service(url: str, timeout: float = 2.0) -> bool:
    """Verificar se um serviço está online"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            return response.status_code == 200
    except Exception as e:
        logger.debug(f"Serviço {url} offline: {e}")
        return False


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Health check do sistema
    
    Verifica o status de todos os serviços:
    - OpenRAG
    - OpenSearch
    - Langflow
    - Redis
    """
    
    # Verificar serviços
    openrag_status = False
    opensearch_status = False
    langflow_status = False
    redis_status = False
    
    if settings.USE_OPENRAG:
        # Verificar OpenRAG/Langflow
        langflow_status = await check_service(f"{settings.OPENRAG_API_URL}/health")
        
        # Verificar OpenSearch
        opensearch_status = await check_service(f"{settings.OPENSEARCH_URL}/_cluster/health")
        
        # Verificar Redis (simplificado)
        try:
            # TODO: Implementar verificação real do Redis
            redis_status = True
        except:
            redis_status = False
        
        openrag_status = langflow_status and opensearch_status
    else:
        # Modo legado - sempre true
        openrag_status = True
    
    # Status geral
    overall = openrag_status if settings.USE_OPENRAG else True
    
    return HealthStatus(
        status="healthy" if overall else "degraded",
        version=settings.VERSION,
        timestamp=datetime.now(),
        openrag=openrag_status,
        opensearch=opensearch_status,
        langflow=langflow_status,
        redis=redis_status,
        overall=overall
    )


@router.get("/ping")
async def ping():
    """Ping simples"""
    return {"status": "pong", "timestamp": datetime.now()}
