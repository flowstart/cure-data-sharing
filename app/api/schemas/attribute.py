from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class AttributeIssueRequest(BaseModel):
    """颁发属性请求模式"""
    user_id: int = Field(..., description="用户ID")
    name: str = Field(..., description="属性名称")
    value: str = Field(..., description="属性值")
    expiration_days: Optional[int] = Field(0, ge=0, description="过期天数，0表示永不过期")
    description: Optional[str] = Field(None, description="属性描述")

    @validator('name', 'value')
    def validate_not_empty(cls, v, field):
        if not v or len(v.strip()) == 0:
            raise ValueError(f"{field.name}不能为空")
        return v


class AttributeResponse(BaseModel):
    """属性响应模式"""
    id: int = Field(..., description="属性ID")
    user_id: int = Field(..., description="用户ID")
    issuer_id: int = Field(..., description="颁发者ID")
    name: str = Field(..., description="属性名称")
    value: str = Field(..., description="属性值")
    description: Optional[str] = Field(None, description="属性描述")
    issued_at: str = Field(..., description="颁发时间")
    expires_at: Optional[str] = Field(None, description="过期时间")
    is_revoked: bool = Field(False, description="是否已撤销")
    revoked_at: Optional[str] = Field(None, description="撤销时间")
    revoked_by: Optional[int] = Field(None, description="撤销者ID")
    blockchain_attribute_id: Optional[str] = Field(None, description="区块链属性ID")
    blockchain_tx_hash: Optional[str] = Field(None, description="区块链交易哈希")
    
    class Config:
        orm_mode = True


class AttributeValidateRequest(BaseModel):
    """验证属性请求模式"""
    user_id: int = Field(..., description="用户ID")
    name: str = Field(..., description="属性名称")
    value: Optional[str] = Field(None, description="属性值，如果为None则只检查属性名")


class AttributeValidateResponse(BaseModel):
    """属性验证响应模式"""
    valid: bool = Field(..., description="是否有效")
    message: Optional[str] = Field(None, description="消息")
    source: Optional[str] = Field(None, description="验证来源")
    attributes: Optional[List[Dict[str, Any]]] = Field(None, description="匹配的属性列表")


class AttributeRevokeRequest(BaseModel):
    """撤销属性请求模式"""
    reason: Optional[str] = Field(None, description="撤销原因")