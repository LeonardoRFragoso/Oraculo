"""
Router de Autenticação
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from ..auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Instância global do serviço de autenticação
auth_service = AuthService()


# Modelos Pydantic
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    is_active: bool
    is_admin: bool


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


# Dependency para obter usuário atual
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Obtém usuário atual a partir do token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = auth_service.decode_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = auth_service.get_user(username)
    if user is None:
        raise credentials_exception
    
    return user


@router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserRegister):
    """
    Registrar novo usuário
    """
    try:
        user = auth_service.register_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        return UserResponse(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            full_name=user['full_name'],
            is_active=user['is_active'],
            is_admin=user.get('is_admin', False)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro no registro: {e}")
        raise HTTPException(status_code=500, detail="Erro ao registrar usuário")


@router.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login - Retorna token JWT
    """
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Criar token
    access_token = auth_service.create_access_token(
        data={"sub": user['username'], "user_id": user['id']}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            full_name=user['full_name'],
            is_active=user['is_active'],
            is_admin=user.get('is_admin', False)
        )
    )


@router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Obter dados do usuário atual
    """
    return UserResponse(
        id=current_user['id'],
        username=current_user['username'],
        email=current_user['email'],
        full_name=current_user['full_name'],
        is_active=current_user['is_active'],
        is_admin=current_user.get('is_admin', False)
    )


@router.post("/auth/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user)
):
    """
    Alterar senha do usuário atual
    """
    success = auth_service.change_password(
        username=current_user['username'],
        old_password=password_data.old_password,
        new_password=password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )
    
    return {"success": True, "message": "Senha alterada com sucesso"}


@router.get("/auth/users")
async def list_users(current_user: dict = Depends(get_current_user)):
    """
    Listar todos os usuários (apenas admin)
    """
    if not current_user.get('is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores."
        )
    
    users = auth_service.list_users()
    return {"users": users, "total": len(users)}


@router.delete("/auth/users/{username}")
async def delete_user(
    username: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Deletar usuário (apenas admin)
    """
    if not current_user.get('is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores."
        )
    
    if username == current_user['username']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível deletar seu próprio usuário"
        )
    
    success = auth_service.delete_user(username)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    return {"success": True, "message": f"Usuário '{username}' deletado com sucesso"}
