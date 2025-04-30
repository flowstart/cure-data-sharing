from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from app.config import settings
from db.session import get_db
from db.crud.user import UserCrud
from db.crud.data import DataCrud
from db.crud.attribute import AttributeCrud
from db.crud.audit import AuditCrud

from core.services.user_service import UserService
from core.services.data_service import DataService
from core.services.attribute_service import AttributeService
from core.services.audit_service import AuditService

from core.crypto.cp_abe import CPABEManager
from core.blockchain.ethereum import EthereumClient
from core.storage.ipfs import IPFSClient

# OAuth2 设置
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/users/token")

# 单例服务实例
_user_service = None
_data_service = None
_attribute_service = None
_audit_service = None
_cpabe_manager = None
_ethereum_client = None
_ipfs_client = None


def get_user_crud(db=Depends(get_db)):
    """获取用户CRUD实例"""
    return UserCrud(db)


def get_data_crud(db=Depends(get_db)):
    """获取数据CRUD实例"""
    return DataCrud(db)


def get_attribute_crud(db=Depends(get_db)):
    """获取属性CRUD实例"""
    return AttributeCrud(db)


def get_audit_crud(db=Depends(get_db)):
    """获取审计CRUD实例"""
    return AuditCrud(db)


def get_cpabe_manager():
    """获取CP-ABE管理器实例"""
    global _cpabe_manager
    if _cpabe_manager is None:
        _cpabe_manager = CPABEManager()
    return _cpabe_manager


def get_ethereum_client():
    """获取以太坊客户端实例"""
    global _ethereum_client
    if _ethereum_client is None:
        _ethereum_client = EthereumClient()
    return _ethereum_client


def get_ipfs_client():
    """获取IPFS客户端实例"""
    global _ipfs_client
    if _ipfs_client is None:
        _ipfs_client = IPFSClient()
    return _ipfs_client


def get_user_service(
    user_crud: UserCrud = Depends(get_user_crud)
):
    """获取用户服务实例"""
    global _user_service
    if _user_service is None:
        _user_service = UserService(user_crud)
    return _user_service


def get_data_service(
    cpabe_manager: CPABEManager = Depends(get_cpabe_manager),
    ethereum_client: EthereumClient = Depends(get_ethereum_client),
    ipfs_client: IPFSClient = Depends(get_ipfs_client),
    data_crud: DataCrud = Depends(get_data_crud),
    user_crud: UserCrud = Depends(get_user_crud)
):
    """获取数据服务实例"""
    global _data_service
    if _data_service is None:
        _data_service = DataService(
            cpabe_manager,
            ethereum_client,
            ipfs_client,
            data_crud,
            user_crud
        )
    return _data_service


def get_attribute_service(
    ethereum_client: EthereumClient = Depends(get_ethereum_client),
    user_crud: UserCrud = Depends(get_user_crud),
    attribute_crud: AttributeCrud = Depends(get_attribute_crud)
):
    """获取属性服务实例"""
    global _attribute_service
    if _attribute_service is None:
        _attribute_service = AttributeService(
            ethereum_client,
            user_crud,
            attribute_crud
        )
    return _attribute_service


def get_audit_service(
    ethereum_client: EthereumClient = Depends(get_ethereum_client),
    audit_crud: AuditCrud = Depends(get_audit_crud),
    data_crud: DataCrud = Depends(get_data_crud),
    user_crud: UserCrud = Depends(get_user_crud)
):
    """获取审计服务实例"""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService(
            ethereum_client,
            audit_crud,
            data_crud,
            user_crud
        )
    return _audit_service


def get_token_data(token: str = Depends(oauth2_scheme)):
    """获取令牌数据"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    token_data: dict = Depends(get_token_data),
    user_service: UserService = Depends(get_user_service)
):
    """获取当前用户"""
    user_id = int(token_data.get("sub"))
    user = user_service.get_user(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    """获取当前管理员用户"""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return current_user


def get_current_issuer_user(current_user: dict = Depends(get_current_user)):
    """获取当前属性颁发者用户"""
    if not current_user.get("is_issuer") and not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return current_user