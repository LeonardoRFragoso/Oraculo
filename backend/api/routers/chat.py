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
from rag.hybrid_retriever import HybridRetriever, HybridResult
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
        hybrid_result: Optional[HybridResult] = None

        # Obter fontes conectadas e aplicar filtro opcional do frontend
        connected_sources = [
            s for s in _registry.list()
            if s.status in ("connected", "profiled", "analyzed")
        ]
        selected_ids = set(request.source_ids or [])
        active_sources = connected_sources if not selected_ids else [
            s for s in connected_sources if s.id in selected_ids
        ]

        if active_sources:
            # Rotear pergunta
            decision = _query_router.route(request.query, active_sources)
            query_type = decision.query_type.value
            logger.info(f"Chat routed as '{query_type}' for: {request.query[:80]}")

            if decision.query_type in (QueryType.NL2SQL, QueryType.RAG, QueryType.HYBRID):
                suggested = decision.suggested_sources or [s.id for s in active_sources[:3]]
                struct_sources = [
                    s for s in active_sources
                    if s.id in suggested and s.connector_type not in ("pdf", "docx", "txt", "xml")
                ]
                doc_sources = [
                    s for s in active_sources
                    if s.id in suggested and s.connector_type in ("pdf", "docx", "txt", "xml")
                ]

                try:
                    hybrid_result = await _hybrid.retrieve(
                        question=request.query,
                        structured_sources=struct_sources or None,
                        document_sources=doc_sources or None,
                    )
                    answer = hybrid_result.answer
                    sources = list({
                        s.name for s in active_sources
                        if s.id in (hybrid_result.sources_used or [])
                    })
                except Exception as e:
                    logger.warning(f"Hybrid retrieval failed, falling back to LLM: {e}")

        if not answer:
            # Fallback: LLM direto com contexto de fontes disponíveis
            ctx_hint = ""
            if active_sources:
                names = ", ".join(s.name for s in active_sources[:5])
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

        # Insights baseados em dados reais (SQL ou documentos)
        insights = _build_insights(hybrid_result)

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


def _build_insights(result: Optional[HybridResult]) -> List[Insight]:
    """Generate insights only from concrete data (SQL results or document chunks)."""
    insights: List[Insight] = []
    if not result:
        return insights

    sql_results = result.sql_results
    if sql_results and sql_results.get("rows"):
        rows = sql_results["rows"]
        columns = sql_results.get("columns") or []
        if not rows or not columns:
            return insights

        numeric_cols = []
        for col in columns:
            values = [r.get(col) for r in rows if r.get(col) is not None]
            numeric_values = []
            for v in values:
                try:
                    numeric_values.append(float(v))
                except (ValueError, TypeError):
                    break
            if len(numeric_values) >= max(2, len(values) // 2):
                numeric_cols.append((col, numeric_values))

        for col, values in numeric_cols:
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std = variance ** 0.5
            max_val = max(values)
            min_val = min(values)

            anomalies = [v for v in values if std > 0 and abs(v - mean) > 2 * std]
            if anomalies:
                insights.append(Insight(
                    id=str(uuid.uuid4()),
                    type=InsightType.ANOMALY,
                    title=f"Anomalia detectada em {col}",
                    description=f"Valores de {col} fora do padrão (média {mean:.2f}, desvio {std:.2f}).",
                    confidence=0.75,
                    data={"column": col, "anomalies": anomalies[:5], "mean": mean, "std": std},
                ))
            elif len(values) >= 2:
                first, last = values[0], values[-1]
                if last > first * 1.05:
                    insights.append(Insight(
                        id=str(uuid.uuid4()),
                        type=InsightType.TREND,
                        title=f"Crescimento em {col}",
                        description=f"{col} subiu de {first:.2f} para {last:.2f}.",
                        confidence=0.65,
                        data={"column": col, "start": first, "end": last},
                    ))
                elif last < first * 0.95:
                    insights.append(Insight(
                        id=str(uuid.uuid4()),
                        type=InsightType.ANOMALY,
                        title=f"Queda em {col}",
                        description=f"{col} caiu de {first:.2f} para {last:.2f}.",
                        confidence=0.65,
                        data={"column": col, "start": first, "end": last},
                    ))
                else:
                    insights.append(Insight(
                        id=str(uuid.uuid4()),
                        type=InsightType.OPPORTUNITY,
                        title=f"Variação em {col}",
                        description=f"{col} varia entre {min_val:.2f} e {max_val:.2f} (média {mean:.2f}).",
                        confidence=0.6,
                        data={"column": col, "min": min_val, "max": max_val, "mean": mean},
                    ))

    return insights


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
