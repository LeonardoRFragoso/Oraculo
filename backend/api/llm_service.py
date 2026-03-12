"""
Serviço simplificado de LLM para a API
"""

import os
import logging
from typing import Optional, Dict, Any, List
from openai import OpenAI

logger = logging.getLogger(__name__)


class SimpleLLMService:
    """Serviço simplificado de LLM usando OpenAI diretamente"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY não configurada. Chat não funcionará.")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
        
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    async def generate_response(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Gerar resposta usando OpenAI
        
        Args:
            query: Pergunta do usuário
            context: Contexto adicional (opcional)
        
        Returns:
            Resposta gerada
        """
        if not self.client:
            return (
                "Desculpe, o sistema de IA não está configurado. "
                "Por favor, configure a variável OPENAI_API_KEY."
            )
        
        try:
            logger.info(f"Processando query: {query[:100]}...")
            
            # Construir mensagens
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Você é o Oráculo, um assistente de IA especializado em "
                        "análise de dados comerciais e logísticos. Forneça respostas "
                        "claras, precisas e úteis. Se não tiver dados suficientes, "
                        "seja honesto sobre isso."
                    )
                }
            ]
            
            # Adicionar contexto se fornecido
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                messages.append({
                    "role": "system",
                    "content": f"Contexto adicional:\n{context_str}"
                })
            
            # Adicionar pergunta do usuário
            messages.append({
                "role": "user",
                "content": query
            })
            
            # Chamar OpenAI
            logger.info(f"Chamando OpenAI API - Modelo: {self.model}")
            logger.info(f"Mensagens: {len(messages)} mensagens")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Extrair resposta
            answer = response.choices[0].message.content
            logger.info(f"✓ Resposta gerada com sucesso ({len(answer)} caracteres)")
            
            return answer
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"✗ ERRO ao gerar resposta: {error_msg}", exc_info=True)
            logger.error(f"Tipo do erro: {type(e).__name__}")
            logger.error(f"Query que causou erro: {query}")
            
            # Retornar erro mais informativo
            return (
                f"Desculpe, encontrei uma dificuldade ao processar sua mensagem. "
                f"Erro: {error_msg[:100]}"
            )
    
    async def chat(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Alias para generate_response"""
        return await self.generate_response(query, context)
    
    async def search(self, query: str, top_k: int = 3) -> list:
        """
        Buscar documentos relevantes usando RAG
        """
        try:
            from .rag_service import RAGService
            rag = RAGService()
            results = rag.search(query, top_k=top_k)
            return results
        except Exception as e:
            logger.error(f"Erro na busca RAG: {e}")
            return []
    
    async def generate_with_rag(
        self,
        query: str,
        top_k: int = 3,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Gerar resposta usando RAG (busca em documentos)
        
        Args:
            query: Pergunta do usuário
            top_k: Número de documentos para recuperar
            context: Contexto adicional
            
        Returns:
            Resposta gerada com contexto de documentos
        """
        if not self.client:
            return (
                "Desculpe, o sistema de IA não está configurado. "
                "Por favor, configure a variável OPENAI_API_KEY."
            )
        
        try:
            # Buscar documentos relevantes
            relevant_docs = await self.search(query, top_k=top_k)
            
            logger.info(f"RAG: {len(relevant_docs)} documentos encontrados")
            
            # Construir mensagens
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Você é o Oráculo, um assistente de IA especializado em "
                        "análise de dados comerciais e logísticos. Você tem acesso a documentos "
                        "que o usuário enviou. Use SEMPRE as informações dos documentos fornecidos "
                        "para responder às perguntas. Analise os dados e forneça insights detalhados."
                    )
                }
            ]
            
            # Adicionar documentos como contexto
            if relevant_docs:
                docs_text = "\n\n=== DOCUMENTOS DISPONÍVEIS ===\n\n"
                for i, doc in enumerate(relevant_docs, 1):
                    docs_text += f"[Documento {i}]\n"
                    docs_text += f"Conteúdo:\n{doc['content']}\n"
                    if 'metadata' in doc and 'filename' in doc['metadata']:
                        docs_text += f"Fonte: {doc['metadata']['filename']}\n"
                    docs_text += f"Relevância: {doc.get('similarity', 0):.2f}\n\n"
                docs_text += "=== FIM DOS DOCUMENTOS ===\n"
                
                messages.append({
                    "role": "system",
                    "content": docs_text
                })
                
                logger.info(f"✓ Contexto RAG adicionado: {len(docs_text)} caracteres")
            
            # Adicionar contexto adicional se fornecido
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                messages.append({
                    "role": "system",
                    "content": f"Contexto adicional:\n{context_str}"
                })
            
            # Adicionar pergunta do usuário
            messages.append({
                "role": "user",
                "content": query
            })
            
            # Chamar OpenAI
            logger.info(f"Chamando OpenAI API com RAG - Modelo: {self.model}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Extrair resposta
            answer = response.choices[0].message.content
            logger.info(f"✓ Resposta com RAG gerada ({len(answer)} caracteres)")
            
            return answer
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"✗ ERRO ao gerar resposta com RAG: {error_msg}", exc_info=True)
            # Fallback para resposta sem RAG
            return await self.generate_response(query, context)
