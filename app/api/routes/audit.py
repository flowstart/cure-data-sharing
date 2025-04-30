from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.api.schemas.audit import (
    AuditLogResponse,
    DataAccessLogResponse
)
from app.config import settings
from core.services.audit_service import AuditService
from app.dependencies import get_audit_service, get_current_user

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    responses={404: {"description": "Not found"}},
)

@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    获取审计日志
    - 仅管理员可查看所有日志，普通用户只能查看自己的日志
    - 可按时间范围、用户ID、操作类型、资源类型、资源ID过滤
    - 支持分页
    """
    # 检查权限
    if not current_user.get("is_admin"):
        # 普通用户只能查看自己的日志
        user_id = current_user["id"]
    
    try:
        logs = audit_service.get_audit_logs(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            page=page,
            page_size=page_size
        )
        return logs
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/data-access/{data_id}", response_model=List[DataAccessLogResponse])
async def get_data_access_logs(
    data_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    获取特定数据的访问日志
    - 数据拥有者和管理员可以查看
    """
    # 检查是否是数据拥有者或管理员
    is_owner = audit_service.check_data_ownership(data_id, current_user["id"])
    
    if not is_owner and not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        logs = audit_service.get_data_access_logs(
            data_id=data_id,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            page=page,
            page_size=page_size
        )
        return logs
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/blockchain/{data_id}", response_model=List[Dict[str, Any]])
async def get_blockchain_access_logs(
    data_id: str,
    current_user: dict = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    获取区块链上记录的数据访问日志
    - 数据拥有者和管理员可以查看
    """
    # 检查是否是数据拥有者或管理员
    is_owner = audit_service.check_data_ownership(data_id, current_user["id"])
    
    if not is_owner and not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        logs = audit_service.get_blockchain_access_logs(data_id)
        return logs
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/user-activity/{user_id}", response_model=List[AuditLogResponse])
async def get_user_activity(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    action_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    获取用户活动日志
    - 用户可以查看自己的活动
    - 管理员可以查看所有用户的活动
    """
    # 检查权限
    if current_user["id"] != user_id and not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        logs = audit_service.get_audit_logs(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            action_type=action_type,
            page=page,
            page_size=page_size
        )
        return logs
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))