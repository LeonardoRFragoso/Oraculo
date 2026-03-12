"""
Middlewares customizados
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import time
from typing import Callable

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
    """Middleware para autenticação (simplificado)"""
    
    EXCLUDED_PATHS = ["/", "/docs", "/redoc", "/openapi.json", "/api/health", "/api/ping"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Verificar se path está excluído
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        
        # Verificar token (simplificado)
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Token de autenticação não fornecido"
            )
        
        # TODO: Implementar validação real do token JWT
        # Por enquanto, aceita qualquer token que comece com "Bearer "
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Formato de token inválido"
            )
        
        return await call_next(request)


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
