from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator


class DataPublishRequest(BaseModel):
    """发布数据请求模式"""
    title: str = Field(..., description="数据标题")
    description: str = Field(..., description="数据描述")
    data_type: str = Field(..., description="数据类型")
    data: Any = Field(..., description="数据内容")
    access_policy: str = Field(..., description="访问策略(CP-ABE策略表达式)")
    tags: Optional[List[str]] = Field([], description="标签列表")
    metadata: Optional[Dict[str, Any]] = Field({}, description="元数据")

    @validator('access_policy')
    def validate_access_policy(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("访问策略不能为空")
        return v


class DataResponse(BaseModel):
    """数据响应模式"""
    id: str = Field(..., description="数据ID")
    title: str = Field(..., description="数据标题")
    description: str = Field(..., description="数据描述")
    data_type: str = Field(..., description="数据类型")
    ipfs_cid: str = Field(..., description="IPFS内容标识符")
    access_policy: str = Field(..., description="访问策略")
    blockchain_data_id: Optional[str] = Field(None, description="区块链数据ID")
    blockchain_tx_hash: Optional[str] = Field(None, description="区块链交易哈希")
    tags: List[str] = Field([], description="标签列表")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    is_revoked: Optional[bool] = Field(False, description="是否已撤销")
    revoked_at: Optional[str] = Field(None, description="撤销时间")
    
    class Config:
        orm_mode = True


class DataAccessRequest(BaseModel):
    """访问数据请求模式"""
    purpose: Optional[str] = Field(None, description="访问目的")


class DataAccessResponse(BaseModel):
    """数据访问响应模式"""
    data: Any = Field(..., description="数据内容")
    metadata: Optional[Dict[str, Any]] = Field({}, description="元数据")
    data_id: str = Field(..., description="数据ID")
    accessed_at: str = Field(..., description="访问时间")
    is_json: bool = Field(False, description="数据是否为JSON格式")


class DataUpdateRequest(BaseModel):
    """更新数据请求模式"""
    title: Optional[str] = Field(None, description="数据标题")
    description: Optional[str] = Field(None, description="数据描述")
    data: Optional[Any] = Field(None, description="数据内容")
    access_policy: Optional[str] = Field(None, description="访问策略")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

    @validator('access_policy')
    def validate_access_policy(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("访问策略不能为空")
        return v


class DataRevokeRequest(BaseModel):
    """撤销数据请求模式"""
    reason: Optional[str] = Field(None, description="撤销原因")


class DataSearchRequest(BaseModel):
    """搜索数据请求模式"""
    query: Optional[str] = Field(None, description="搜索查询")
    data_type: Optional[str] = Field(None, description="数据类型")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    owner_id: Optional[int] = Field(None, description="所有者ID")