"""
Router de Chat
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging
from datetime import datetime
import uuid

from ..models import ChatRequest, ChatResponse, ChatMessage, Insight, InsightType
from ..config import settings
from ..dependencies import get_llm_manager
from ..conversation_store import ConversationStore

logger = logging.getLogger(__name__)

router = APIRouter()

# Instância global do store de conversas
conversation_store = ConversationStore()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    llm_manager = Depends(get_llm_manager)
):
    """
    Endpoint principal de chat
    
    Processa uma pergunta do usuário e retorna uma resposta gerada pela IA,
    junto com insights e sugestões relevantes.
    """
    try:
        logger.info(f"Chat request: {request.query[:100]}...")
        
        # Gerar conversation_id se não fornecido
        conversation_id = request.conversation_id or conversation_store.create_conversation()
        
        # Salvar mensagem do usuário
        conversation_store.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.query
        )
        
        # Processar com LLM Manager
        # Sempre tentar usar RAG se houver documentos indexados
        try:
            from ..rag_service import RAGService
            rag = RAGService()
            stats = rag.get_stats()
            
            if stats['total_documents'] > 0:
                # Usar RAG se houver documentos
                logger.info(f"Usando RAG: {stats['total_documents']} documentos disponíveis")
                response_text = await llm_manager.generate_with_rag(
                    query=request.query,
                    top_k=3,
                    context=request.context
                )
                source_docs = await llm_manager.search(request.query, top_k=3)
                source_names = [doc.get('metadata', {}).get('filename', 'Documento') for doc in source_docs]
            else:
                # Sem documentos, usar LLM simples
                logger.info("Sem documentos indexados, usando LLM simples")
                response_text = await llm_manager.generate_response(
                    query=request.query,
                    context=request.context
                )
                source_names = []
        except Exception as e:
            logger.error(f"Erro ao usar RAG: {e}")
            # Fallback para LLM simples
            response_text = await llm_manager.generate_response(
                query=request.query,
                context=request.context
            )
            source_names = []
        
        # Gerar insights (exemplo - pode ser mais sofisticado)
        insights = []
        if "crescimento" in response_text.lower() or "aumento" in response_text.lower():
            insights.append(Insight(
                id=str(uuid.uuid4()),
                type=InsightType.TREND,
                title="Tendência de Crescimento Detectada",
                description="Identificado padrão de crescimento nos dados analisados",
                confidence=0.75
            ))
        
        # Gerar sugestões
        suggestions = [
            "Ver detalhes por cliente",
            "Comparar com período anterior",
            "Analisar tendências sazonais"
        ]
        
        # Salvar resposta do assistente
        conversation_store.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            metadata={
                'insights_count': len(insights),
                'sources_count': len(source_names)
            }
        )
        
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            insights=insights,
            suggestions=suggestions,
            sources=source_names
        )
        
    except Exception as e:
        logger.error(f"Erro no chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar chat: {str(e)}"
        )


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
