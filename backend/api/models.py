"""
Modelos Pydantic para validação de dados
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Roles de mensagem"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Mensagem de chat"""
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Quantos containers foram movimentados em março?",
                "timestamp": "2024-03-12T10:30:00"
            }
        }


class ChatRequest(BaseModel):
    """Requisição de chat"""
    query: str = Field(..., min_length=1, max_length=2000, description="Pergunta do usuário")
    conversation_id: Optional[str] = Field(None, description="ID da conversa")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional")
    
    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Query não pode estar vazia')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Quantos containers foram movimentados em março?",
                "conversation_id": "conv-123",
                "context": {"client": "Acme Corp"}
            }
        }


class InsightType(str, Enum):
    """Tipos de insight"""
    TREND = "trend"
    ANOMALY = "anomaly"
    OPPORTUNITY = "opportunity"
    RISK = "risk"


class Insight(BaseModel):
    """Insight gerado pela IA"""
    id: str
    type: InsightType
    title: str
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "insight-123",
                "type": "trend",
                "title": "Crescimento de 23% em Março",
                "description": "Identificado crescimento significativo...",
                "confidence": 0.85,
                "data": {"growth": 0.23}
            }
        }


class ChatResponse(BaseModel):
    """Resposta de chat"""
    response: str
    conversation_id: str
    insights: Optional[List[Insight]] = []
    suggestions: Optional[List[str]] = []
    sources: Optional[List[str]] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Em março foram movimentados 1.234 containers...",
                "conversation_id": "conv-123",
                "insights": [],
                "suggestions": ["Ver detalhes por cliente", "Comparar com mês anterior"],
                "sources": ["data_march_2024.xlsx"]
            }
        }


class FileUploadResponse(BaseModel):
    """Resposta de upload de arquivo"""
    success: bool
    message: str
    file_id: Optional[str] = None
    filename: str
    size: int
    processed: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Arquivo enviado com sucesso",
                "file_id": "file-123",
                "filename": "data.xlsx",
                "size": 1024000,
                "processed": True
            }
        }


class HealthStatus(BaseModel):
    """Status de saúde do sistema"""
    status: str
    version: str
    timestamp: datetime
    openrag: bool
    opensearch: bool
    langflow: bool
    redis: bool
    overall: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "3.0.0",
                "timestamp": "2024-03-12T10:30:00",
                "openrag": True,
                "opensearch": True,
                "langflow": True,
                "redis": True,
                "overall": True
            }
        }


class AnalyticsMetrics(BaseModel):
    """Métricas de analytics"""
    total_containers: int
    active_clients: int
    growth_rate: float
    insights_generated: int
    period: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_containers": 1234,
                "active_clients": 45,
                "growth_rate": 0.23,
                "insights_generated": 12,
                "period": "2024-03"
            }
        }


class ErrorResponse(BaseModel):
    """Resposta de erro"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Query não pode estar vazia",
                "details": {"field": "query"}
            }
        }
