"""
聊天 API 控制器 - MVC Controller 层 (FastAPI Router)
"""
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import json

from app.models.request import ChatRequest
from app.models.response import ChatResponse, ErrorResponse
from app.services.chat_service import ChatService
from app.config import get_settings, Settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["chat"],
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        401: {"model": ErrorResponse, "description": "认证失败"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)


def get_chat_service(settings: Settings = Depends(get_settings)) -> ChatService:
    """依赖注入：获取聊天服务实例"""
    return ChatService(settings)


async def stream_generator(chat_service: ChatService,
                           request: ChatRequest) -> AsyncGenerator[bytes, None]:
    """
    流式响应生成器

    Args:
        chat_service: 聊天服务
        request: 聊天请求

    Yields:
        SSE 格式的字节数据
    """
    try:
        messages = [msg.model_dump() for msg in request.messages]

        # process_chat 在流式模式下直接返回异步生成器对象（不是协程）
        async_gen = chat_service.process_chat(
            messages=messages,
            stream=True,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            model_name=request.model_name
        )

        async for chunk in async_gen:
            yield chunk.encode("utf-8")

    except Exception as e:
        logger.error(f"流式响应错误: {str(e)}", exc_info=True)
        error_data = json.dumps({
            "error": str(e),
            "success": False
        })
        yield f"data: {error_data}\n\n".encode("utf-8")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    聊天接口（非流式）

    - **messages**: 消息历史列表
    - **stream**: 是否启用流式响应（此端点为非流式）
    - **temperature**: 温度参数 (0.0-2.0)
    - **max_tokens**: 最大token数 (1-8192)
    - **model_name**: 模型名称 (glm-4, glm-4v, glm-3-turbo)
    """
    try:
        messages = [msg.model_dump() for msg in request.messages]

        # process_chat 返回一个 Task，需要 await
        result = await chat_service.process_chat(
            messages=messages,
            stream=False,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            model_name=request.model_name
        )

        return ChatResponse(
            success=True,
            message=result["message"],
            model=result["model"],
            usage=result.get("usage")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理请求时发生错误: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    流式聊天接口

    使用 Server-Sent Events (SSE) 返回流式响应

    - **messages**: 消息历史列表
    - **stream**: 必须为 true
    - **temperature**: 温度参数 (0.0-2.0)
    - **max_tokens**: 最大token数 (1-8192)
    - **model_name**: 模型名称 (glm-4, glm-4v, glm-3-turbo)
    """
    if not request.stream:
        raise HTTPException(
            status_code=400,
            detail="流式接口需要将 stream 设置为 true"
        )

    return StreamingResponse(
        stream_generator(chat_service, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )

