from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    """用户基本信息"""
    username: str = Field(..., description="用户名")
    email: EmailStr = Field(..., description="电子邮件")
    full_name: Optional[str] = Field(None, description="全名")


class UserCreate(UserBase):
    """创建用户请求模式"""
    password: str = Field(..., min_length=8, description="密码，至少8个字符")
    role: Optional[str] = Field("user", description="角色，可选值: user, admin, issuer")

    @validator('role')
    def validate_role(cls, v):
        allowed_roles = ["user", "admin", "issuer"]
        if v not in allowed_roles:
            raise ValueError(f"角色必须是以下值之一: {', '.join(allowed_roles)}")
        return v


class UserUpdate(BaseModel):
    """更新用户请求模式"""
    email: Optional[EmailStr] = Field(None, description="电子邮件")
    full_name: Optional[str] = Field(None, description="全名")
    password: Optional[str] = Field(None, min_length=8, description="密码，至少8个字符")
    is_active: Optional[bool] = Field(None, description="是否活跃")
    role: Optional[str] = Field(None, description="角色，可选值: user, admin, issuer")

    @validator('role')
    def validate_role(cls, v):
        if v is not None:
            allowed_roles = ["user", "admin", "issuer"]
            if v not in allowed_roles:
                raise ValueError(f"角色必须是以下值之一: {', '.join(allowed_roles)}")
        return v


class UserResponse(UserBase):
    """用户响应模式"""
    id: int = Field(..., description="用户ID")
    is_active: bool = Field(..., description="是否活跃")
    is_admin: bool = Field(..., description="是否管理员")
    is_issuer: bool = Field(..., description="是否属性颁发者")
    role: str = Field(..., description="角色")
    blockchain_address: Optional[str] = Field(None, description="区块链地址")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")

    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    """Token响应模式"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(..., description="令牌类型")


class UserAttributeResponse(BaseModel):
    """用户属性响应模式"""
    id: Optional[int] = Field(None, description="属性ID")
    name: str = Field(..., description="属性名称")
    value: str = Field(..., description="属性值")
    description: Optional[str] = Field(None, description="属性描述")
    issued_at: Optional[str] = Field(None, description="颁发时间")
    expires_at: Optional[str] = Field(None, description="过期时间")
    is_revoked: bool = Field(False, description="是否已撤销")
    is_expired: bool = Field(False, description="是否已过期")
    blockchain_attribute_id: Optional[str] = Field(None, description="区块链属性ID")
    source: Optional[str] = Field("database", description="属性来源")

    class Config:
        orm_mode = True