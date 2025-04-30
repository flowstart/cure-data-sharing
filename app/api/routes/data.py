from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Query
import json

from app.api.schemas.data import (
    DataPublishRequest,
    DataResponse,
    DataAccessRequest,
    DataUpdateRequest,
    DataSearchRequest
)
from app.config import settings
from core.services.data_service import DataService
from app.dependencies import get_data_service, get_current_user

router = APIRouter(
    prefix="/data",
    tags=["data"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=DataResponse, status_code=status.HTTP_201_CREATED)
async def publish_data(
    data_request: DataPublishRequest,
    current_user: dict = Depends(get_current_user),
    data_service: DataService = Depends(get_data_service)
):
    """
    发布数据
    """
    try:
        data_record = data_service.publish_data(
            owner_id=current_user["id"],
            data=data_request.data,
            title=data_request.title,
            description=data_request.description,
            data_type=data_request.data_type,
            access_policy=data_request.access_policy,
            tags=data_request.tags,
            metadata=data_request.metadata
        )
        return data_record
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/file", response_model=DataResponse, status_code=status.HTTP_201_CREATED)
async def publish_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(...),
    data_type: str = Form(...),
    access_policy: str = Form(...),
    tags: str = Form("[]"),
    metadata: str = Form("{}")
):
    """
    上传并发布文件数据
    """
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 解析标签和元数据
        tags_list = json.loads(tags)
        metadata_dict = json.loads(metadata)
        
        # 发布数据
        data_record = data_service.publish_data(
            owner_id=current_user["id"],
            data=file_content,
            title=title,
            description=description,
            data_type=data_type,
            access_policy=access_policy,
            tags=tags_list,
            metadata=metadata_dict
        )
        return data_record
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON format in tags or metadata")

@router.get("/my", response_model=List[DataResponse])
async def get_my_data(
    current_user: dict = Depends(get_current_user),
    data_service: DataService = Depends(get_data_service)
):
    """
    获取当前用户发布的数据列表
    """
    try:
        data_list = data_service.get_user_data(current_user["id"])
        return data_list
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{data_id}", response_model=Dict[str, Any])
async def access_data(
    data_id: str,
    purpose: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    data_service: DataService = Depends(get_data_service)
):
    """
    访问数据
    """
    try:
        data = data_service.access_data(
            user_id=current_user["id"],
            data_id=data_id,
            purpose=purpose
        )
        return data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{data_id}", response_model=DataResponse)
async def update_data(
    data_id: str,
    data_request: DataUpdateRequest,
    current_user: dict = Depends(get_current_user),
    data_service: DataService = Depends(get_data_service)
):
    """
    更新数据
    """
    try:
        data_record = data_service.update_data(
            owner_id=current_user["id"],
            data_id=data_id,
            data=data_request.data,
            title=data_request.title,
            description=data_request.description,
            access_policy=data_request.access_policy,
            tags=data_request.tags,
            metadata=data_request.metadata
        )
        return data_record
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{data_id}", status_code=status.HTTP_200_OK)
async def revoke_data(
    data_id: str,
    current_user: dict = Depends(get_current_user),
    data_service: DataService = Depends(get_data_service)
):
    """
    撤销数据
    """
    try:
        result = data_service.revoke_data(
            owner_id=current_user["id"],
            data_id=data_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/search", response_model=List[DataResponse])
async def search_data(
    search_request: DataSearchRequest,
    current_user: dict = Depends(get_current_user),
    data_service: DataService = Depends(get_data_service)
):
    """
    搜索数据
    """
    try:
        data_list = data_service.search_data(
            user_id=current_user["id"],
            query=search_request.query,
            data_type=search_request.data_type,
            tags=search_request.tags,
            owner_id=search_request.owner_id
        )
        return data_list
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))