"""
Serviço de Autenticação - JWT e gerenciamento de usuários
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import uuid

logger = logging.getLogger(__name__)


class AuthService:
    """Serviço de autenticação com JWT"""
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        users_file: str = "../dados/users.json"
    ):
        self.secret_key = secret_key or os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        
        # Password hashing - usando sha256_crypt para evitar limitação de 72 bytes do bcrypt
        self.pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
        
        # Armazenamento de usuários
        self.users_file = Path(users_file)
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        self.users = self._load_users()
    
    def _load_users(self) -> Dict[str, Any]:
        """Carrega usuários do arquivo JSON"""
        try:
            if self.users_file.exists():
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                    logger.info(f"✓ Usuários carregados: {len(users)} usuários")
                    return users
        except Exception as e:
            logger.error(f"Erro ao carregar usuários: {e}")
        
        # Criar usuário admin padrão
        default_users = {
            "admin": {
                "id": str(uuid.uuid4()),
                "username": "admin",
                "email": "admin@oraculo.com",
                "full_name": "Administrador",
                "hashed_password": self.get_password_hash("admin123"),
                "is_active": True,
                "is_admin": True,
                "created_at": datetime.now().isoformat()
            }
        }
        
        self._save_users(default_users)
        logger.info("✓ Usuário admin padrão criado (username: admin, password: admin123)")
        
        return default_users
    
    def _save_users(self, users: Optional[Dict[str, Any]] = None):
        """Salva usuários no arquivo JSON"""
        try:
            users_to_save = users if users is not None else self.users
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users_to_save, f, indent=2, ensure_ascii=False)
            logger.debug("✓ Usuários salvos")
        except Exception as e:
            logger.error(f"Erro ao salvar usuários: {e}")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica se a senha está correta"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Gera hash da senha"""
        return self.pwd_context.hash(password)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Autentica usuário
        
        Args:
            username: Nome de usuário ou email
            password: Senha
            
        Returns:
            Dados do usuário se autenticado, None caso contrário
        """
        # Buscar por username ou email
        user = None
        for u in self.users.values():
            if u['username'] == username or u.get('email') == username:
                user = u
                break
        
        if not user:
            logger.warning(f"Usuário não encontrado: {username}")
            return None
        
        if not user.get('is_active', True):
            logger.warning(f"Usuário inativo: {username}")
            return None
        
        if not self.verify_password(password, user['hashed_password']):
            logger.warning(f"Senha incorreta para: {username}")
            return None
        
        logger.info(f"✓ Usuário autenticado: {username}")
        return user
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Cria token JWT
        
        Args:
            data: Dados para incluir no token
            
        Returns:
            Token JWT
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decodifica e valida token JWT
        
        Args:
            token: Token JWT
            
        Returns:
            Payload do token se válido, None caso contrário
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"Token inválido: {e}")
            return None
    
    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registra novo usuário
        
        Args:
            username: Nome de usuário
            email: Email
            password: Senha
            full_name: Nome completo
            
        Returns:
            Dados do usuário criado
            
        Raises:
            ValueError: Se usuário já existe
        """
        # Verificar se já existe
        for user in self.users.values():
            if user['username'] == username:
                raise ValueError(f"Usuário '{username}' já existe")
            if user.get('email') == email:
                raise ValueError(f"Email '{email}' já está em uso")
        
        # Criar usuário
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "full_name": full_name or username,
            "hashed_password": self.get_password_hash(password),
            "is_active": True,
            "is_admin": False,
            "created_at": datetime.now().isoformat()
        }
        
        self.users[username] = user
        self._save_users()
        
        logger.info(f"✓ Usuário registrado: {username}")
        
        return user
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Retorna dados do usuário"""
        return self.users.get(username)
    
    def update_user(self, username: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza dados do usuário
        
        Args:
            username: Nome de usuário
            updates: Campos para atualizar
            
        Returns:
            Dados atualizados do usuário
        """
        if username not in self.users:
            raise ValueError(f"Usuário '{username}' não encontrado")
        
        # Campos permitidos para atualização
        allowed_fields = ['email', 'full_name', 'is_active']
        
        for field, value in updates.items():
            if field in allowed_fields:
                self.users[username][field] = value
        
        self.users[username]['updated_at'] = datetime.now().isoformat()
        self._save_users()
        
        logger.info(f"✓ Usuário atualizado: {username}")
        
        return self.users[username]
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Altera senha do usuário
        
        Args:
            username: Nome de usuário
            old_password: Senha atual
            new_password: Nova senha
            
        Returns:
            True se alterada com sucesso
        """
        user = self.users.get(username)
        if not user:
            return False
        
        if not self.verify_password(old_password, user['hashed_password']):
            logger.warning(f"Senha atual incorreta para: {username}")
            return False
        
        user['hashed_password'] = self.get_password_hash(new_password)
        user['updated_at'] = datetime.now().isoformat()
        self._save_users()
        
        logger.info(f"✓ Senha alterada: {username}")
        
        return True
    
    def delete_user(self, username: str) -> bool:
        """
        Deleta usuário
        
        Args:
            username: Nome de usuário
            
        Returns:
            True se deletado com sucesso
        """
        if username in self.users:
            del self.users[username]
            self._save_users()
            logger.info(f"✓ Usuário deletado: {username}")
            return True
        return False
    
    def list_users(self) -> list:
        """Lista todos os usuários (sem senhas)"""
        return [
            {
                'id': user['id'],
                'username': user['username'],
                'email': user.get('email'),
                'full_name': user.get('full_name'),
                'is_active': user.get('is_active', True),
                'is_admin': user.get('is_admin', False),
                'created_at': user.get('created_at')
            }
            for user in self.users.values()
        ]
