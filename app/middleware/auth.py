import logging
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.responses import JSONResponse
from jose import jwt, JWTError
import time

from app.config import settings

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件"""

    async def dispatch(self, request: Request, call_next):
        # 记录请求开始时间
        start_time = time.time()
        
        # 排除不需要认证的路径
        excluded_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            f"{settings.API_V1_PREFIX}/users/token",
            "/",
            "/health",
            "/static",
        ]
        
        # 检查路径是否需要认证
        path = request.url.path
        needs_auth = True
        for excluded_path in excluded_paths:
            if path.startswith(excluded_path):
                needs_auth = False
                break
        
        # 如果是OPTIONS请求，不需要认证
        if request.method == "OPTIONS":
            needs_auth = False
        
        token = None
        
        # 处理认证
        if needs_auth:
            # 从请求头获取令牌
            authorization = request.headers.get("Authorization")
            if not authorization:
                return JSONResponse(
                    status_code=HTTP_401_UNAUTHORIZED,
                    content={"detail": "Not authenticated"}
                )
            
            try:
                # 解析令牌
                scheme, token = authorization.split()
                if scheme.lower() != "bearer":
                    return JSONResponse(
                        status_code=HTTP_401_UNAUTHORIZED,
                        content={"detail": "Invalid authentication scheme"}
                    )
                
                # 验证令牌
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM]
                )
                
                # 将用户信息添加到请求状态
                request.state.user = payload
                request.state.token = token
                
            except JWTError as e:
                logger.warning(f"JWT error: {str(e)}")
                return JSONResponse(
                    status_code=HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication credentials"}
                )
            except Exception as e:
                logger.error(f"Authentication error: {str(e)}")
                return JSONResponse(
                    status_code=HTTP_401_UNAUTHORIZED,
                    content={"detail": "Authentication error"}
                )
        
        # 继续处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response