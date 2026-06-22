"""
🔮 Oráculo API - FastAPI Backend
Sistema de análise de dados com IA usando OpenRAG
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import List, Optional
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend root is on path so connectors/ and catalog/ are importable
_backend_root = str(Path(__file__).parent.parent)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

from .routers import chat, analytics, files, health, auth, datasources, query
from .config import settings
from .middleware import LoggingMiddleware, AuthMiddleware, TraceMiddleware

# Carregar variáveis de ambiente
load_dotenv()

# Structured logging
from core.logging_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação"""
    logger.info("🚀 Iniciando Oráculo API...")
    logger.info(f"📍 Ambiente: {settings.ENVIRONMENT}")
    logger.info(f"� Auth obrigatória: {settings.REQUIRE_AUTH}")

    # Validação de segurança ao iniciar
    if settings.ENVIRONMENT == "production" and not settings.SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY não configurada. "
            "Defina a variável de ambiente SECRET_KEY antes de iniciar em produção."
        )
    if not settings.SECRET_KEY:
        logger.warning(
            "⚠️  SECRET_KEY não definida — usando chave efêmera. "
            "Tokens serão invalidados ao reiniciar. Configure SECRET_KEY no .env"
        )

    # Criar tabelas automaticamente se não existirem (dev/SQLite)
    # Em produção, use: alembic upgrade head
    try:
        from db.engine import engine
        from db.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables verified/created")
    except Exception as e:
        logger.warning(f"DB init warning (non-fatal): {e}")

    yield

    logger.info("👋 Encerrando Oráculo API...")


# Criar aplicação FastAPI
app = FastAPI(
    title="🔮 Oráculo API",
    description="Plataforma Universal de Inteligência Corporativa — Data Intelligence + AI Agents",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adicionar middlewares customizados
app.add_middleware(TraceMiddleware)   # outermost — sets trace_id first
app.add_middleware(LoggingMiddleware)
if settings.REQUIRE_AUTH:
    app.add_middleware(AuthMiddleware)

# Incluir routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
app.include_router(files.router, prefix="/api", tags=["Files"])
app.include_router(datasources.router, prefix="/api", tags=["Data Sources"])
app.include_router(query.router, prefix="/api", tags=["Query"])


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "name": "Oráculo API",
        "version": "4.0.0",
        "status": "online",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global de exceções"""
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.DEBUG else "Ocorreu um erro interno"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
