import logging
import time
import json
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

from utils.logger import get_logger

logger = get_logger("api")


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件"""

    async def dispatch(self, request: Request, call_next):
        # 生成请求ID
        request_id = str(uuid.uuid4())
        
        # 设置请求ID
        request.state.request_id = request_id
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # 记录请求日志
        logger.info(
            f"Request started: {method} {url}",
            extra={
                "request_id": request_id,
                "method": method,
                "url": url,
                "client_host": client_host,
                "user_agent": user_agent
            }
        )
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应日志
            logger.info(
                f"Request completed: {method} {url} {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "status_code": response.status_code,
                    "process_time": process_time
                }
            )
            
            # 添加请求ID到响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.6f}"
            
            return response
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录错误日志
            logger.exception(
                f"Request failed: {method} {url}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "error": str(e),
                    "process_time": process_time
                }
            )
            
            # 重新抛出异常
            raise


class RequestBodyLogMiddleware(BaseHTTPMiddleware):
    """请求体日志中间件，只在DEBUG模式下启用"""

    async def dispatch(self, request: Request, call_next):
        # 判断是否启用DEBUG模式
        from app.config import settings
        if not settings.DEBUG:
            return await call_next(request)
        
        # 获取请求ID
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        # 日志记录请求体
        try:
            body = await request.body()
            if body:
                # 尝试解析JSON
                try:
                    body_text = body.decode()
                    body_json = json.loads(body_text)
                    # 如果有密码字段，进行脱敏
                    if isinstance(body_json, dict) and "password" in body_json:
                        body_json["password"] = "****"
                    logger.debug(
                        f"Request body: {json.dumps(body_json)}",
                        extra={"request_id": request_id}
                    )
                except:
                    # 如果不是JSON，记录长度
                    logger.debug(
                        f"Request body (non-JSON): {len(body)} bytes",
                        extra={"request_id": request_id}
                    )
        except Exception as e:
            logger.warning(
                f"Failed to log request body: {str(e)}",
                extra={"request_id": request_id}
            )
        
        # 必须重新创建body迭代器
        async def get_body():
            return body
        
        request._body = get_body
        
        # 处理请求
        return await call_next(request)