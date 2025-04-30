from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.attribute import (
    AttributeIssueRequest,
    AttributeResponse,
    AttributeValidateRequest,
    AttributeValidateResponse
)
from app.config import settings
from core.services.attribute_service import AttributeService
from app.dependencies import get_attribute_service, get_current_user

router = APIRouter(
    prefix="/attributes",
    tags=["attributes"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=AttributeResponse, status_code=status.HTTP_201_CREATED)
async def issue_attribute(
    attribute_request: AttributeIssueRequest,
    current_user: dict = Depends(get_current_user),
    attribute_service: AttributeService = Depends(get_attribute_service)
):
    """
    颁发属性给用户（仅管理员和颁发者可访问）
    """
    if not current_user.get("is_admin") and not current_user.get("is_issuer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        attribute = attribute_service.issue_attribute(
            issuer_id=current_user["id"],
            user_id=attribute_request.user_id,
            name=attribute_request.name,
            value=attribute_request.value,
            expiration_days=attribute_request.expiration_days,
            description=attribute_request.description
        )
        return attribute
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{attribute_id}", status_code=status.HTTP_200_OK)
async def revoke_attribute(
    attribute_id: int,
    current_user: dict = Depends(get_current_user),
    attribute_service: AttributeService = Depends(get_attribute_service)
):
    """
    撤销用户属性（仅管理员和颁发者可访问）
    """
    if not current_user.get("is_admin") and not current_user.get("is_issuer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        result = attribute_service.revoke_attribute(
            revoker_id=current_user["id"],
            attribute_id=attribute_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/validate", response_model=AttributeValidateResponse)
async def validate_attribute(
    validate_request: AttributeValidateRequest,
    current_user: dict = Depends(get_current_user),
    attribute_service: AttributeService = Depends(get_attribute_service)
):
    """
    验证用户是否拥有特定属性
    """
    try:
        result = attribute_service.validate_attribute(
            user_id=validate_request.user_id,
            name=validate_request.name,
            value=validate_request.value
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=List[AttributeResponse])
async def get_attributes(
    user_id: Optional[int] = None,
    name: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    attribute_service: AttributeService = Depends(get_attribute_service)
):
    """
    获取属性列表
    - 如果提供user_id，则获取该用户的属性
    - 如果同时提供name，则筛选指定名称的属性
    - 如果不提供user_id，则获取当前用户的属性
    """
    # 如果未提供user_id，则使用当前用户ID
    target_user_id = user_id or current_user["id"]
    
    # 如果查询其他用户，检查权限
    if target_user_id != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        # 获取属性列表
        attributes = attribute_service.get_user_attributes(target_user_id)
        
        # 如果提供了name，筛选属性
        if name:
            attributes = [attr for attr in attributes if attr["name"] == name]
        
        return attributes
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))