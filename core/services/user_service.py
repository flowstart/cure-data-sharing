import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.config import settings
from core.blockchain.utils import generate_ethereum_account
from utils.security import get_password_hash, verify_password
from db.crud.user import UserCrud

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    """用户服务类，负责用户认证、注册和管理"""
    
    def __init__(self, user_crud: UserCrud = None):
        """
        初始化用户服务
        
        Args:
            user_crud: 用户CRUD实例
        """
        self.user_crud = user_crud
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str = None,
        role: str = "user"
    ) -> Dict:
        """
        创建新用户
        
        Args:
            username: 用户名
            email: 电子邮件
            password: 密码
            full_name: 全名
            role: 角色
            
        Returns:
            user: 创建的用户信息
        """
        # 检查用户名是否已存在
        existing_user = self.user_crud.get_by_username(username)
        if existing_user:
            raise ValueError(f"Username {username} already exists")
        
        # 检查邮箱是否已存在
        existing_email = self.user_crud.get_by_email(email)
        if existing_email:
            raise ValueError(f"Email {email} already exists")
        
        # 根据角色设置权限
        is_admin = False
        is_issuer = False
        
        if role == "admin":
            is_admin = True
        elif role == "issuer":
            is_issuer = True
        
        # 创建用户
        user_data = {
            "username": username,
            "email": email,
            "password_hash": get_password_hash(password),
            "full_name": full_name,
            "role": role,
            "is_active": True,
            "is_admin": is_admin,
            "is_issuer": is_issuer,
            "created_at": datetime.now(),
            "last_login": None
        }
        
        # 保存到数据库
        user = self.user_crud.create(user_data)
        
        # 返回用户信息（不包含密码哈希）
        user_dict = user.__dict__.copy()
        user_dict.pop("password_hash", None)
        
        logger.info(f"Created new user: {username} with role: {role}")
        return user_dict
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        验证用户
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            user: 验证成功则返回用户信息，否则返回None
        """
        # 获取用户信息
        user = self.user_crud.get_by_username(username)
        
        # 检查用户是否存在
        if not user:
            return None
        
        # 检查用户是否激活
        if not user.is_active:
            return None
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            return None
        
        # 更新最后登录时间
        self.user_crud.update(user.id, {"last_login": datetime.now()})
        
        # 返回用户信息（不包含密码哈希）
        user_dict = user.__dict__.copy()
        user_dict.pop("password_hash", None)
        
        logger.info(f"User authenticated: {username}")
        return user_dict
    
    def create_access_token(self, user_id: int, expires_delta: timedelta = None) -> str:
        """
        创建访问令牌
        
        Args:
            user_id: 用户ID
            expires_delta: 过期时间间隔
            
        Returns:
            token: JWT访问令牌
        """
        # 设置过期时间
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # 创建JWT负载
        to_encode = {
            "sub": str(user_id),
            "exp": expire
        }
        
        # 签名JWT
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    def decode_token(self, token: str) -> Dict:
        """
        解码令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            payload: JWT负载
            
        Raises:
            JWTError: 如果令牌无效
        """
        try:
            # 解码JWT
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # 提取用户ID
            user_id = payload.get("sub")
            if user_id is None:
                raise JWTError("Invalid token payload")
            
            return payload
        except JWTError as e:
            logger.error(f"JWT decode error: {str(e)}")
            raise
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            user: 用户信息，如果不存在则返回None
        """
        # 获取用户
        user = self.user_crud.get(user_id)
        
        if not user:
            return None
        
        # 返回用户信息（不包含密码哈希）
        user_dict = user.__dict__.copy()
        user_dict.pop("password_hash", None)
        
        return user_dict
    
    def update_user(
        self,
        user_id: int,
        full_name: str = None,
        email: str = None,
        password: str = None,
        is_active: bool = None,
        role: str = None
    ) -> Dict:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            full_name: 全名
            email: 电子邮件
            password: 密码
            is_active: 是否激活
            role: 角色
            
        Returns:
            user: 更新后的用户信息
        """
        # 获取用户
        user = self.user_crud.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # 准备更新数据
        updates = {}
        
        # 更新全名
        if full_name is not None:
            updates["full_name"] = full_name
        
        # 更新邮箱
        if email is not None and email != user.email:
            # 检查邮箱是否已被使用
            existing_email = self.user_crud.get_by_email(email)
            if existing_email and existing_email.id != user_id:
                raise ValueError(f"Email {email} already exists")
            updates["email"] = email
        
        # 更新密码
        if password is not None:
            updates["password_hash"] = get_password_hash(password)
        
        # 更新激活状态
        if is_active is not None:
            updates["is_active"] = is_active
        
        # 更新角色
        if role is not None and role != user.role:
            updates["role"] = role
            if role == "admin":
                updates["is_admin"] = True
                updates["is_issuer"] = False
            elif role == "issuer":
                updates["is_admin"] = False
                updates["is_issuer"] = True
            else:
                updates["is_admin"] = False
                updates["is_issuer"] = False
        
        # 更新时间戳
        updates["updated_at"] = datetime.now()
        
        # 更新用户
        if updates:
            updated_user = self.user_crud.update(user_id, updates)
            
            # 返回用户信息（不包含密码哈希）
            user_dict = updated_user.__dict__.copy()
            user_dict.pop("password_hash", None)
            
            logger.info(f"Updated user: {user.username}, updates: {list(updates.keys())}")
            return user_dict
        else:
            # 没有更新，返回原始用户信息
            user_dict = user.__dict__.copy()
            user_dict.pop("password_hash", None)
            return user_dict
    
    def generate_blockchain_account(self, user_id: int) -> Dict:
        """
        为用户生成区块链账户
        
        Args:
            user_id: 用户ID
            
        Returns:
            account: 账户信息
        """
        # 获取用户
        user = self.user_crud.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # 检查用户是否已有区块链账户
        if user.blockchain_address:
            return {
                "blockchain_address": user.blockchain_address,
                "message": "User already has a blockchain account"
            }
        
        # 生成区块链账户
        account = generate_ethereum_account()
        
        # 更新用户记录
        updates = {
            "blockchain_address": account["address"],
            "blockchain_private_key": account["private_key"]
        }
        
        self.user_crud.update(user_id, updates)
        
        logger.info(f"Generated blockchain account for user {user_id}")
        return {
            "blockchain_address": account["address"],
            "message": "Blockchain account generated successfully"
        }
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        通过用户名获取用户信息
        
        Args:
            username: 用户名
            
        Returns:
            user: 用户信息，如果不存在则返回None
        """
        # 获取用户
        user = self.user_crud.get_by_username(username)
        
        if not user:
            return None
        
        # 返回用户信息（不包含密码哈希）
        user_dict = user.__dict__.copy()
        user_dict.pop("password_hash", None)
        
        return user_dict
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        通过电子邮件获取用户信息
        
        Args:
            email: 电子邮件
            
        Returns:
            user: 用户信息，如果不存在则返回None
        """
        # 获取用户
        user = self.user_crud.get_by_email(email)
        
        if not user:
            return None
        
        # 返回用户信息（不包含密码哈希）
        user_dict = user.__dict__.copy()
        user_dict.pop("password_hash", None)
        
        return user_dict
    
    def get_user_list(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """
        获取用户列表
        
        Args:
            skip: 跳过的数量
            limit: 限制的数量
            
        Returns:
            users: 用户列表
        """
        # 获取用户列表
        users = self.user_crud.get_multi(skip=skip, limit=limit)
        
        # 转换为字典列表（不包含密码哈希）
        result = []
        for user in users:
            user_dict = user.__dict__.copy()
            user_dict.pop("password_hash", None)
            result.append(user_dict)
        
        return result