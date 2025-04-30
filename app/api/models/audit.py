from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from db.session import Base


class AuditLog(Base):
    """审计日志数据模型"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 操作信息
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    action_type = Column(String, nullable=False)  # 例如: create, read, update, delete
    resource_type = Column(String, nullable=False)  # 例如: user, data, attribute
    resource_id = Column(String, nullable=True)
    
    # 详细信息
    details = Column(JSON, default=dict, nullable=True)
    
    # 客户端信息
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    request_id = Column(String, nullable=True)
    
    # 关系
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action_type={self.action_type})>"