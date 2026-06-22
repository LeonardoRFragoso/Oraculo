"""
Router de Chat — unified architecture (QueryRouter + HybridRetriever)

Replaces legacy rag_service.py + llm_service.py dependency.
"""

import sys
import uuid
from pathlib import Path
from typing import List, Optional
import logging

from fastapi import APIRouter, HTTPException, Depends

from ..models import ChatRequest, ChatResponse, ChatMessage, Insight, InsightType
from ..conversation_store import ConversationStore

_root = Path(__file__).parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from catalog.registry import DataSourceRegistry
from nl2sql.router import QueryRouter, QueryType
from rag.hybrid_retriever import HybridRetriever
from core.llm_client import LLMClient

logger = logging.getLogger(__name__)
router = APIRouter()
conversation_store = ConversationStore()

# Singletons — mesmos do query.py para consistência
_registry = DataSourceRegistry()
_query_router = QueryRouter()
_hybrid = HybridRetriever()
_llm = LLMClient()

_FALLBACK_SYSTEM = (
    "Você é o Oráculo, assistente de inteligência corporativa. "
    "Responda de forma clara e objetiva. "
    "Se não tiver dados conectados, oriente o usuário a adicionar fontes de dados."
)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint de chat — roteado pela nova arquitetura unificada:
      - Com fontes conectadas: NL2SQL / RAG / Hybrid via QueryRouter
      - Sem fontes: resposta LLM direta com orientação
    """
    try:
        conversation_id = request.conversation_id or conversation_store.create_conversation()
        conversation_store.add_message(conversation_id, role="user", content=request.query)

        answer = ""
        sources: List[str] = []
        query_type = "direct"

        # Obter fontes conectadas
        connected_sources = [
            s for s in _registry.list()
            if s.status in ("connected", "profiled", "analyzed")
        ]

        if connected_sources:
            # Rotear pergunta
            decision = _query_router.route(request.query, connected_sources)
            query_type = decision.query_type.value
            logger.info(f"Chat routed as '{query_type}' for: {request.query[:80]}")

            if decision.query_type in (QueryType.NL2SQL, QueryType.RAG, QueryType.HYBRID):
                suggested = decision.suggested_sources or [s.id for s in connected_sources[:3]]
                struct_sources = [
                    s for s in connected_sources
                    if s.id in suggested and s.connector_type not in ("pdf", "docx", "txt", "xml")
                ]
                doc_sources = [
                    s for s in connected_sources
                    if s.id in suggested and s.connector_type in ("pdf", "docx", "txt", "xml")
                ]

                try:
                    result = await _hybrid.retrieve(
                        question=request.query,
                        structured_sources=struct_sources or None,
                        document_sources=doc_sources or None,
                    )
                    answer = result.answer
                    sources = list({
                        s.name for s in connected_sources
                        if s.id in (result.source_ids or [])
                    })
                except Exception as e:
                    logger.warning(f"Hybrid retrieval failed, falling back to LLM: {e}")

        if not answer:
            # Fallback: LLM direto com contexto de fontes disponíveis
            ctx_hint = ""
            if connected_sources:
                names = ", ".join(s.name for s in connected_sources[:5])
                ctx_hint = f"\n\nFontes de dados conectadas: {names}."
            resp = _llm.chat(
                system=_FALLBACK_SYSTEM,
                user=request.query + ctx_hint,
                temperature=0.4,
                max_tokens=800,
            )
            answer = resp.content

        conversation_store.add_message(
            conversation_id, role="assistant", content=answer,
            metadata={"query_type": query_type, "sources": sources}
        )

        # Insight simples baseado em palavras-chave
        insights: List[Insight] = []
        _kw = answer.lower()
        if any(w in _kw for w in ("crescimento", "aumento", "alta", "elevação")):
            insights.append(Insight(
                id=str(uuid.uuid4()), type=InsightType.TREND,
                title="Tendência de Crescimento", description="Padrão de crescimento detectado na resposta.",
                confidence=0.7,
            ))
        elif any(w in _kw for w in ("queda", "redução", "diminuição", "declínio")):
            insights.append(Insight(
                id=str(uuid.uuid4()), type=InsightType.ANOMALY,
                title="Tendência de Queda", description="Padrão de queda detectado na resposta.",
                confidence=0.7,
            ))

        return ChatResponse(
            response=answer,
            conversation_id=conversation_id,
            insights=insights,
            suggestions=[
                "Adicionar mais fontes de dados",
                "Ver análise detalhada em AI Analyst",
                "Configurar alertas automáticos",
            ],
            sources=sources,
        )

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao processar chat: {str(e)}")


@router.get("/chat/history/{conversation_id}", response_model=List[ChatMessage])
async def get_chat_history(conversation_id: str):
    """
    Obter histórico de uma conversa
    """
    try:
        messages = conversation_store.get_messages(conversation_id)
        
        # Converter para formato ChatMessage
        chat_messages = [
            ChatMessage(
                role=msg['role'],
                content=msg['content'],
                timestamp=msg['timestamp']
            )
            for msg in messages
        ]
        
        return chat_messages
    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/conversations")
async def list_conversations(limit: int = 50):
    """
    Listar todas as conversas
    """
    try:
        conversations = conversation_store.list_conversations(limit=limit)
        return {"conversations": conversations, "total": len(conversations)}
    except Exception as e:
        logger.error(f"Erro ao listar conversas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/history/{conversation_id}")
async def delete_chat_history(conversation_id: str):
    """
    Deletar histórico de uma conversa
    """
    try:
        success = conversation_store.delete_conversation(conversation_id)
        if success:
            return {"success": True, "message": "Histórico deletado com sucesso"}
        else:
            raise HTTPException(status_code=404, detail="Conversa não encontrada")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))
