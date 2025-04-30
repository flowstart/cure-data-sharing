from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.models.user import User

class UserCrud:
    """用户CRUD操作类"""
    
    def __init__(self, db: Session):
        """
        初始化
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def get(self, user_id: int) -> Optional[User]:
        """
        通过ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            User: 用户对象，如果不存在则为None
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        通过用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            User: 用户对象，如果不存在则为None
        """
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        通过电子邮件获取用户
        
        Args:
            email: 电子邮件
            
        Returns:
            User: 用户对象，如果不存在则为None
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_multi(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        获取用户列表
        
        Args:
            skip: 跳过的数量
            limit: 限制的数量
            
        Returns:
            List[User]: 用户对象列表
        """
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def create(self, user_data: Dict[str, Any]) -> User:
        """
        创建用户
        
        Args:
            user_data: 用户数据
            
        Returns:
            User: 创建的用户对象
        """
        db_user = User(**user_data)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update(self, user_id: int, user_data: Dict[str, Any]) -> User:
        """
        更新用户
        
        Args:
            user_id: 用户ID
            user_data: 用户数据
            
        Returns:
            User: 更新后的用户对象
        """
        user = self.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        for key, value in user_data.items():
            setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user_id: int) -> bool:
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否成功删除
        """
        user = self.get(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True
    
    def get_by_blockchain_address(self, blockchain_address: str) -> Optional[User]:
        """
        通过区块链地址获取用户
        
        Args:
            blockchain_address: 区块链地址
            
        Returns:
            User: 用户对象，如果不存在则为None
        """
        return self.db.query(User).filter(User.blockchain_address == blockchain_address).first()
    
    def get_admins(self) -> List[User]:
        """
        获取所有管理员用户
        
        Returns:
            List[User]: 管理员用户对象列表
        """
        return self.db.query(User).filter(User.is_admin == True).all()
    
    def get_issuers(self) -> List[User]:
        """
        获取所有属性颁发者用户
        
        Returns:
            List[User]: 属性颁发者用户对象列表
        """
        return self.db.query(User).filter(User.is_issuer == True).all()
    
    def count(self) -> int:
        """
        获取用户总数
        
        Returns:
            int: 用户总数
        """
        return self.db.query(User).count()
    
    def count_active(self) -> int:
        """
        获取活跃用户总数
        
        Returns:
            int: 活跃用户总数
        """
        return self.db.query(User).filter(User.is_active == True).count()