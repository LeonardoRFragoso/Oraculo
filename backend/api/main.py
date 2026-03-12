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
from dotenv import load_dotenv

from .routers import chat, analytics, files, health, auth
from .config import settings
from .middleware import LoggingMiddleware, AuthMiddleware

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console
        logging.FileHandler('../logs/api.log') if os.path.exists('../logs') else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação"""
    logger.info("🚀 Iniciando Oráculo API...")
    logger.info(f"📍 Ambiente: {settings.ENVIRONMENT}")
    logger.info(f"🔍 OpenRAG: {'Ativo' if settings.USE_OPENRAG else 'Inativo'}")
    
    # Inicializar recursos
    yield
    
    # Cleanup
    logger.info("👋 Encerrando Oráculo API...")


# Criar aplicação FastAPI
app = FastAPI(
    title="🔮 Oráculo API",
    description="API REST para análise de dados comerciais e logísticos com IA",
    version="3.0.0",
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
app.add_middleware(LoggingMiddleware)
if settings.REQUIRE_AUTH:
    app.add_middleware(AuthMiddleware)

# Incluir routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
app.include_router(files.router, prefix="/api", tags=["Files"])


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "name": "Oráculo API",
        "version": "3.0.0",
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
