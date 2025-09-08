"""
Sistema de autenticação e controle de acesso para GPTRACKER
"""
import streamlit as st
import hashlib
import json
import os
from datetime import datetime, timedelta
import jwt
from typing import Dict, List, Optional

class AuthManager:
    def __init__(self, users_file="users.json", secret_key=None):
        self.users_file = users_file
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY', 'gptracker_secret_key_2024')
        self.session_timeout = 8  # 8 horas
        
    def hash_password(self, password: str) -> str:
        """Gera hash da senha"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def load_users(self) -> Dict:
        """Carrega usuários do arquivo"""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_users(self, users: Dict):
        """Salva usuários no arquivo"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    
    def create_user(self, username: str, password: str, role: str = "user", 
                   permissions: List[str] = None) -> bool:
        """Cria novo usuário"""
        users = self.load_users()
        
        if username in users:
            return False
        
        users[username] = {
            "password": self.hash_password(password),
            "role": role,
            "permissions": permissions or ["read"],
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "active": True
        }
        
        self.save_users(users)
        return True
    
    def authenticate(self, username: str, password: str) -> bool:
        """Autentica usuário"""
        users = self.load_users()
        
        if username not in users:
            return False
        
        user = users[username]
        if not user.get("active", True):
            return False
        
        password_hash = self.hash_password(password)
        if user["password"] == password_hash:
            # Atualizar último login
            users[username]["last_login"] = datetime.now().isoformat()
            self.save_users(users)
            return True
        
        return False
    
    def generate_token(self, username: str) -> str:
        """Gera token JWT para sessão"""
        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=self.session_timeout),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verifica token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['username']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """Retorna informações do usuário"""
        users = self.load_users()
        return users.get(username)
    
    def has_permission(self, username: str, permission: str) -> bool:
        """Verifica se usuário tem permissão específica"""
        user_info = self.get_user_info(username)
        if not user_info:
            return False
        
        permissions = user_info.get("permissions", [])
        role = user_info.get("role", "user")
        
        # Admin tem todas as permissões
        if role == "admin":
            return True
        
        return permission in permissions
    
    def login_form(self):
        """Renderiza formulário de login"""
        st.markdown("### 🔐 Login GPTRACKER")
        
        # Mostrar usuários disponíveis para debug
        users = self.load_users()
        if users:
            st.info(f"Usuários disponíveis: {', '.join(users.keys())}")
        else:
            st.warning("Nenhum usuário encontrado. Criando usuários padrão...")
            self.init_default_users()
            st.rerun()
        
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar")
            
            if submit:
                if self.authenticate(username, password):
                    token = self.generate_token(username)
                    st.session_state.auth_token = token
                    st.session_state.username = username
                    st.session_state.authenticated = True
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos")
    
    def logout(self):
        """Realiza logout"""
        for key in ['auth_token', 'username', 'authenticated']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    def require_auth(self):
        """Decorator para páginas que requerem autenticação"""
        # Inicializar usuários padrão se necessário
        if not hasattr(self, '_users_initialized'):
            self.init_default_users()
            self._users_initialized = True
        
        if not st.session_state.get('authenticated', False):
            self.login_form()
            return False
        
        # Verificar se token ainda é válido
        token = st.session_state.get('auth_token')
        if token:
            username = self.verify_token(token)
            if not username:
                # Token expirado, mas não fazer logout automático
                # Apenas mostrar aviso e permitir re-login
                st.warning("⚠️ Sua sessão expirou. Faça login novamente para continuar.")
                if st.button("🔄 Fazer Login Novamente"):
                    self.logout()
                    st.rerun()
                return False
        else:
            # Sem token, mostrar login
            self.login_form()
            return False
        
        return True
    
    def init_default_users(self):
        """Inicializa usuários padrão"""
        users = self.load_users()
        
        # Sempre criar usuários padrão se não existirem
        if "admin" not in users:
            self.create_user(
                "admin", 
                "admin123", 
                "admin", 
                ["read", "write", "admin", "analytics", "budget"]
            )
        
        if "comercial" not in users:
            self.create_user(
                "comercial", 
                "comercial123", 
                "comercial", 
                ["read", "analytics", "budget"]
            )
        
        if "operacional" not in users:
            self.create_user(
                "operacional", 
                "operacional123", 
                "operacional", 
                ["read", "analytics"]
            )

# Instância global do gerenciador de autenticação
auth_manager = AuthManager()
