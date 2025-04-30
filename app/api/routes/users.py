from typing import List, Optional
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.api.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    TokenResponse,
    UserAttributeResponse
)
from app.config import settings
from core.services.user_service import UserService
from core.services.attribute_service import AttributeService
from app.dependencies import get_user_service, get_attribute_service, get_current_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/users/token")

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    创建新用户
    """
    try:
        user = user_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service)
):
    """
    获取访问令牌（登录）
    """
    user = user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = user_service.create_access_token(
        user_id=user["id"],
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户信息
    """
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    更新当前用户信息
    """
    try:
        user = user_service.update_user(
            user_id=current_user["id"],
            full_name=user_data.full_name,
            email=user_data.email,
            password=user_data.password
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    获取指定用户信息（仅管理员可访问）
    """
    if not current_user.get("is_admin") and current_user.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    更新指定用户信息（仅管理员可访问）
    """
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        user = user_service.update_user(
            user_id=user_id,
            full_name=user_data.full_name,
            email=user_data.email,
            password=user_data.password,
            is_active=user_data.is_active,
            role=user_data.role
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{user_id}/blockchain-account", status_code=status.HTTP_201_CREATED)
async def generate_blockchain_account(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    为用户生成区块链账户（仅管理员或本人可访问）
    """
    if not current_user.get("is_admin") and current_user.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        account = user_service.generate_blockchain_account(user_id)
        return account
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{user_id}/attributes", response_model=List[UserAttributeResponse])
async def get_user_attributes(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    attribute_service: AttributeService = Depends(get_attribute_service)
):
    """
    获取用户属性列表（管理员可查看所有用户，用户只能查看自己）
    """
    if not current_user.get("is_admin") and current_user.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        attributes = attribute_service.get_user_attributes(user_id)
        return attributes
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{user_id}/valid-attributes", response_model=List[UserAttributeResponse])
async def get_valid_user_attributes(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    attribute_service: AttributeService = Depends(get_attribute_service)
):
    """
    获取用户有效属性列表（管理员可查看所有用户，用户只能查看自己）
    """
    if not current_user.get("is_admin") and current_user.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        attributes = attribute_service.get_valid_user_attributes(user_id)
        return attributes
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))