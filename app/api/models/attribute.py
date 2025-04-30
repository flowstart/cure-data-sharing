from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from db.session import Base


class Attribute(Base):
    """用户属性数据模型"""
    __tablename__ = "attributes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    issuer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 属性信息
    name = Column(String, nullable=False)
    value = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # 时间信息
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # NULL表示永不过期
    
    # 撤销信息
    is_revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 区块链相关
    blockchain_attribute_id = Column(String, nullable=True)  # 区块链上的属性ID
    blockchain_tx_hash = Column(String, nullable=True)  # 交易哈希
    
    # 关系
    user = relationship("User", back_populates="attributes", foreign_keys=[user_id])
    issuer = relationship("User", foreign_keys=[issuer_id])
    revoker = relationship("User", foreign_keys=[revoked_by])
    
    def __repr__(self):
        return f"<Attribute(id={self.id}, user_id={self.user_id}, name={self.name}, value={self.value})>"