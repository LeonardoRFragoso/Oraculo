"""
Middlewares customizados
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import time
from typing import Callable

from core.logging_config import new_trace_id, set_trace_id

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de requisições"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log da requisição
        logger.info(f"→ {request.method} {request.url.path}")
        
        # Processar requisição
        response = await call_next(request)
        
        # Calcular tempo de processamento
        process_time = time.time() - start_time
        
        # Log da resposta
        logger.info(
            f"← {request.method} {request.url.path} "
            f"[{response.status_code}] {process_time:.3f}s"
        )
        
        # Adicionar header com tempo de processamento
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware de autenticação JWT real — valida assinatura e expiração."""

    # Paths que não requerem autenticação
    PUBLIC_PATHS = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/health",
        "/api/ping",
        "/api/auth/login",
        "/api/auth/register",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Permitir CORS preflight sem token
        if request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return Response(
                content='{"detail":"Token de autenticação não fornecido"}',
                status_code=401,
                media_type="application/json",
            )

        token = auth_header[len("Bearer "):]
        try:
            from .auth_service import AuthService
            _auth = AuthService()
            payload = _auth.decode_token(token)
            if payload is None:
                raise ValueError("Token inválido ou expirado")
            # Injetar username no state para uso nos routers
            request.state.username = payload.get("sub")
        except Exception as e:
            logger.warning(f"Auth falhou para {request.url.path}: {e}")
            return Response(
                content=f'{{"detail":"Token inválido ou expirado"}}',
                status_code=401,
                media_type="application/json",
            )

        return await call_next(request)


class TraceMiddleware(BaseHTTPMiddleware):
    """Injects a unique trace ID per request for structured logging and correlation."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Use client-provided trace ID if present (distributed tracing), else generate
        trace_id = request.headers.get("X-Trace-ID") or new_trace_id()
        set_trace_id(trace_id)
        request.state.trace_id = trace_id

        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware para rate limiting (simplificado)"""
    
    def __init__(self, app, max_requests: int = 100, window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self.requests = {}  # IP -> (count, timestamp)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Obter IP do cliente
        client_ip = request.client.host
        
        # Verificar rate limit
        current_time = time.time()
        
        if client_ip in self.requests:
            count, timestamp = self.requests[client_ip]
            
            # Resetar se janela expirou
            if current_time - timestamp > self.window:
                self.requests[client_ip] = (1, current_time)
            else:
                # Incrementar contador
                if count >= self.max_requests:
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit excedido. Tente novamente mais tarde."
                    )
                self.requests[client_ip] = (count + 1, timestamp)
        else:
            self.requests[client_ip] = (1, current_time)
        
        return await call_next(request)
