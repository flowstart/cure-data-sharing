from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime

from app.api.models.attribute import Attribute

class AttributeCrud:
    """属性CRUD操作类"""
    
    def __init__(self, db: Session):
        """
        初始化
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def get(self, attribute_id: int) -> Optional[Attribute]:
        """
        通过ID获取属性
        
        Args:
            attribute_id: 属性ID
            
        Returns:
            Attribute: 属性对象，如果不存在则为None
        """
        return self.db.query(Attribute).filter(Attribute.id == attribute_id).first()
    
    def get_by_user(self, user_id: int) -> List[Attribute]:
        """
        获取用户的所有属性
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Attribute]: 属性对象列表
        """
        return self.db.query(Attribute).filter(Attribute.user_id == user_id).all()
    
    def get_by_issuer(self, issuer_id: int) -> List[Attribute]:
        """
        获取颁发者颁发的所有属性
        
        Args:
            issuer_id: 颁发者ID
            
        Returns:
            List[Attribute]: 属性对象列表
        """
        return self.db.query(Attribute).filter(Attribute.issuer_id == issuer_id).all()
    
    def get_by_user_and_name(self, user_id: int, name: str) -> List[Attribute]:
        """
        获取用户的特定名称的属性
        
        Args:
            user_id: 用户ID
            name: 属性名称
            
        Returns:
            List[Attribute]: 属性对象列表
        """
        return self.db.query(Attribute).filter(
            Attribute.user_id == user_id,
            Attribute.name == name
        ).all()
    
    def get_by_user_and_value(self, user_id: int, name: str, value: str) -> Optional[Attribute]:
        """
        获取用户的特定名称和值的属性
        
        Args:
            user_id: 用户ID
            name: 属性名称
            value: 属性值
            
        Returns:
            Attribute: 属性对象，如果不存在则为None
        """
        return self.db.query(Attribute).filter(
            Attribute.user_id == user_id,
            Attribute.name == name,
            Attribute.value == value
        ).first()
    
    def get_valid_attributes(self, user_id: int) -> List[Attribute]:
        """
        获取用户的所有有效属性（未撤销且未过期）
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Attribute]: 属性对象列表
        """
        now = datetime.now()
        return self.db.query(Attribute).filter(
            Attribute.user_id == user_id,
            Attribute.is_revoked == False,
            and_(
                Attribute.expires_at == None,
                Attribute.expires_at > now
            )
        ).all()
    
    def create(self, attribute_data: Dict[str, Any]) -> Attribute:
        """
        创建属性
        
        Args:
            attribute_data: 属性数据
            
        Returns:
            Attribute: 创建的属性对象
        """
        db_attribute = Attribute(**attribute_data)
        self.db.add(db_attribute)
        self.db.commit()
        self.db.refresh(db_attribute)
        return db_attribute
    
    def update(self, attribute_id: int, attribute_data: Dict[str, Any]) -> Attribute:
        """
        更新属性
        
        Args:
            attribute_id: 属性ID
            attribute_data: 属性数据
            
        Returns:
            Attribute: 更新后的属性对象
        """
        attribute = self.get(attribute_id)
        if not attribute:
            raise ValueError(f"Attribute with ID {attribute_id} not found")
        
        for key, value in attribute_data.items():
            setattr(attribute, key, value)
        
        self.db.commit()
        self.db.refresh(attribute)
        return attribute
    
    def delete(self, attribute_id: int) -> bool:
        """
        删除属性
        
        Args:
            attribute_id: 属性ID
            
        Returns:
            bool: 是否成功删除
        """
        attribute = self.get(attribute_id)
        if not attribute:
            return False
        
        self.db.delete(attribute)
        self.db.commit()
        return True
    
    def revoke(self, attribute_id: int, revoker_id: int) -> Optional[Attribute]:
        """
        撤销属性
        
        Args:
            attribute_id: 属性ID
            revoker_id: 撤销者ID
            
        Returns:
            Attribute: 更新后的属性对象，如果不存在则为None
        """
        attribute = self.get(attribute_id)
        if not attribute:
            return None
        
        attribute.is_revoked = True
        attribute.revoked_at = datetime.now()
        attribute.revoked_by = revoker_id
        
        self.db.commit()
        self.db.refresh(attribute)
        return attribute
    
    def check_attribute_validity(self, attribute_id: int) -> Dict[str, Any]:
        """
        检查属性是否有效
        
        Args:
            attribute_id: 属性ID
            
        Returns:
            Dict: 属性有效性信息
        """
        attribute = self.get(attribute_id)
        if not attribute:
            return {
                "valid": False,
                "message": "Attribute not found"
            }
        
        # 检查是否撤销
        if attribute.is_revoked:
            return {
                "valid": False,
                "message": "Attribute has been revoked",
                "revoked_at": attribute.revoked_at,
                "revoked_by": attribute.revoked_by
            }
        
        # 检查是否过期
        now = datetime.now()
        if attribute.expires_at and attribute.expires_at < now:
            return {
                "valid": False,
                "message": "Attribute has expired",
                "expires_at": attribute.expires_at
            }
        
        return {
            "valid": True,
            "attribute": {
                "id": attribute.id,
                "name": attribute.name,
                "value": attribute.value,
                "issued_at": attribute.issued_at,
                "expires_at": attribute.expires_at
            }
        }
    
    def get_attributes_by_blockchain_id(self, blockchain_attribute_id: str) -> List[Attribute]:
        """
        通过区块链属性ID获取属性
        
        Args:
            blockchain_attribute_id: 区块链属性ID
            
        Returns:
            List[Attribute]: 属性对象列表
        """
        return self.db.query(Attribute).filter(
            Attribute.blockchain_attribute_id == blockchain_attribute_id
        ).all()
    
    def count_by_user(self, user_id: int) -> int:
        """
        统计用户属性数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 属性数量
        """
        return self.db.query(Attribute).filter(Attribute.user_id == user_id).count()
    
    def count_by_issuer(self, issuer_id: int) -> int:
        """
        统计颁发者颁发的属性数量
        
        Args:
            issuer_id: 颁发者ID
            
        Returns:
            int: 属性数量
        """
        return self.db.query(Attribute).filter(Attribute.issuer_id == issuer_id).count()