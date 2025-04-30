from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AuditLogBase(BaseModel):
    """审计日志基本信息"""
    user_id: int = Field(..., description="用户ID")
    action_type: str = Field(..., description="操作类型")
    resource_type: str = Field(..., description="资源类型")
    resource_id: Optional[str] = Field(None, description="资源ID")
    details: Optional[Dict[str, Any]] = Field({}, description="详情")


class AuditLogCreate(AuditLogBase):
    """创建审计日志请求模式"""
    pass


class AuditLogResponse(AuditLogBase):
    """审计日志响应模式"""
    id: int = Field(..., description="日志ID")
    timestamp: str = Field(..., description="时间戳")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    username: Optional[str] = Field(None, description="用户名")
    
    class Config:
        orm_mode = True


class DataAccessLogBase(BaseModel):
    """数据访问日志基本信息"""
    data_id: str = Field(..., description="数据ID")
    user_id: int = Field(..., description="用户ID")
    purpose: Optional[str] = Field(None, description="访问目的")
    is_successful: bool = Field(..., description="是否成功")
    error_message: Optional[str] = Field(None, description="错误消息")


class DataAccessLogCreate(DataAccessLogBase):
    """创建数据访问日志请求模式"""
    pass


class DataAccessLogResponse(DataAccessLogBase):
    """数据访问日志响应模式"""
    id: int = Field(..., description="日志ID")
    timestamp: str = Field(..., description="时间戳")
    ip_address: Optional[str] = Field(None, description="IP地址")
    username: Optional[str] = Field(None, description="用户名")
    blockchain_tx_hash: Optional[str] = Field(None, description="区块链交易哈希")
    
    class Config:
        orm_mode = True