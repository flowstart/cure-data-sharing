from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text, JSON, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from db.session import Base


class Data(Base):
    """数据资产数据模型"""
    __tablename__ = "data_assets"

    id = Column(Integer, primary_key=True, index=True)
    data_id = Column(String, unique=True, index=True, nullable=False)  # UUID
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 基本信息
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    data_type = Column(String, nullable=False)
    
    # 存储相关
    ipfs_cid = Column(String, nullable=False)  # IPFS内容标识符
    
    # 加密相关
    access_policy = Column(Text, nullable=False)  # CP-ABE策略表达式
    
    # 区块链相关
    blockchain_data_id = Column(String, nullable=True)  # 区块链上的数据ID
    blockchain_tx_hash = Column(String, nullable=True)  # 交易哈希
    
    # 分类信息
    tags = Column(JSON, default=list, nullable=True)  # 标签列表
    data_metadata = Column(JSON, default=dict, nullable=True)  # 元数据
    
    # 状态
    is_revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    owner = relationship("User", back_populates="data_assets", foreign_keys=[owner_id])
    revoker = relationship("User", foreign_keys=[revoked_by])
    access_logs = relationship("DataAccessLog", back_populates="data_asset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Data(id={self.id}, data_id={self.data_id}, title={self.title})>"


class DataAccessLog(Base):
    """数据访问日志数据模型"""
    __tablename__ = "data_access_logs"

    id = Column(Integer, primary_key=True, index=True)
    data_id = Column(String, ForeignKey("data_assets.data_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 访问信息
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    purpose = Column(String, nullable=True)
    is_successful = Column(Boolean, default=True, nullable=False)
    error_message = Column(String, nullable=True)
    
    # 客户端信息
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # 区块链相关
    blockchain_tx_hash = Column(String, nullable=True)  # 访问记录交易哈希
    
    # 关系
    data_asset = relationship("Data", back_populates="access_logs")
    user = relationship("User")
    
    def __repr__(self):
        return f"<DataAccessLog(id={self.id}, data_id={self.data_id}, user_id={self.user_id})>"