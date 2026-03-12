"""
Armazenamento de conversas - Persistência de histórico de chat
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ConversationStore:
    """Gerencia persistência de conversas em JSON"""
    
    def __init__(self, storage_dir: str = "../dados/conversations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.conversations_file = self.storage_dir / "conversations.json"
        
        # Carregar conversas existentes
        self.conversations = self._load_conversations()
    
    def _load_conversations(self) -> Dict[str, Any]:
        """Carrega conversas do disco"""
        try:
            if self.conversations_file.exists():
                with open(self.conversations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"✓ Conversas carregadas: {len(data)} conversas")
                    return data
        except Exception as e:
            logger.error(f"Erro ao carregar conversas: {e}")
        
        return {}
    
    def _save_conversations(self):
        """Salva conversas no disco"""
        try:
            with open(self.conversations_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations, f, indent=2, ensure_ascii=False)
            logger.debug(f"✓ Conversas salvas: {len(self.conversations)} conversas")
        except Exception as e:
            logger.error(f"Erro ao salvar conversas: {e}")
    
    def create_conversation(
        self, 
        user_id: str = "default",
        title: Optional[str] = None
    ) -> str:
        """
        Cria nova conversa
        
        Args:
            user_id: ID do usuário
            title: Título da conversa
            
        Returns:
            ID da conversa criada
        """
        conversation_id = str(uuid.uuid4())
        
        self.conversations[conversation_id] = {
            'id': conversation_id,
            'user_id': user_id,
            'title': title or f"Conversa {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'messages': []
        }
        
        self._save_conversations()
        logger.info(f"✓ Conversa criada: {conversation_id}")
        
        return conversation_id
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Adiciona mensagem a uma conversa
        
        Args:
            conversation_id: ID da conversa
            role: 'user' ou 'assistant'
            content: Conteúdo da mensagem
            metadata: Metadados adicionais
            
        Returns:
            Mensagem criada
        """
        # Criar conversa se não existir
        if conversation_id not in self.conversations:
            self.create_conversation()
            conversation_id = list(self.conversations.keys())[-1]
        
        message = {
            'id': str(uuid.uuid4()),
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.conversations[conversation_id]['messages'].append(message)
        self.conversations[conversation_id]['updated_at'] = datetime.now().isoformat()
        
        # Atualizar título se for a primeira mensagem do usuário
        if role == 'user' and len(self.conversations[conversation_id]['messages']) == 1:
            self.conversations[conversation_id]['title'] = content[:50] + ('...' if len(content) > 50 else '')
        
        self._save_conversations()
        
        return message
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retorna conversa completa"""
        return self.conversations.get(conversation_id)
    
    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Retorna mensagens de uma conversa"""
        conversation = self.conversations.get(conversation_id)
        if conversation:
            return conversation['messages']
        return []
    
    def list_conversations(
        self, 
        user_id: str = "default",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Lista conversas de um usuário
        
        Args:
            user_id: ID do usuário
            limit: Número máximo de conversas
            
        Returns:
            Lista de conversas (sem mensagens)
        """
        user_conversations = [
            {
                'id': conv['id'],
                'title': conv['title'],
                'created_at': conv['created_at'],
                'updated_at': conv['updated_at'],
                'message_count': len(conv['messages'])
            }
            for conv in self.conversations.values()
            if conv['user_id'] == user_id
        ]
        
        # Ordenar por data de atualização (mais recente primeiro)
        user_conversations.sort(key=lambda x: x['updated_at'], reverse=True)
        
        return user_conversations[:limit]
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Deleta uma conversa
        
        Args:
            conversation_id: ID da conversa
            
        Returns:
            True se deletada com sucesso
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            self._save_conversations()
            logger.info(f"✓ Conversa deletada: {conversation_id}")
            return True
        return False
    
    def clear_all(self, user_id: Optional[str] = None):
        """
        Limpa todas as conversas (ou de um usuário específico)
        
        Args:
            user_id: Se fornecido, limpa apenas conversas deste usuário
        """
        if user_id:
            self.conversations = {
                k: v for k, v in self.conversations.items()
                if v['user_id'] != user_id
            }
        else:
            self.conversations = {}
        
        self._save_conversations()
        logger.info(f"✓ Conversas limpas{f' para usuário {user_id}' if user_id else ''}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do armazenamento"""
        total_messages = sum(len(conv['messages']) for conv in self.conversations.values())
        
        return {
            'total_conversations': len(self.conversations),
            'total_messages': total_messages,
            'storage_file': str(self.conversations_file),
            'storage_size_kb': self.conversations_file.stat().st_size / 1024 if self.conversations_file.exists() else 0
        }
