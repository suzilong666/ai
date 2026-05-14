"""
响应数据模型定义 - MVC Model 层
"""
from typing import Optional
from pydantic import BaseModel


class ChatResponse(BaseModel):
    """非流式聊天响应模型"""
    success: bool = True
    message: str
    model: str
    usage: Optional[dict] = None


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error_code: str
    message: str
    details: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    version: str
