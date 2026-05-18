"""
Agent API 控制器 - MVC Controller 层 (FastAPI Router)
"""
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import json

from app.models.request import ChatRequest
from app.models.response import ErrorResponse
from app.services.agent_service import AgentService
from app.config import get_settings, Settings

logger = logging.getLogger(__name__)


def get_agent_service(settings: Settings = Depends(get_settings)) -> AgentService:
    """依赖注入：获取 Agent 服务实例"""
    return AgentService(settings)

router = APIRouter(
    prefix="/api/v1",
    tags=["agent"],
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        401: {"model": ErrorResponse, "description": "认证失败"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)

async def agent_stream_generator(agent_service: AgentService, request: ChatRequest) -> AsyncGenerator[bytes, None]:
    """
    Agent 流式响应生成器

    Args:
        agent_service: Agent 服务
        request: 聊天请求

    Yields:
        SSE 格式的字节数据
    """
    try:
        messages = [msg.model_dump() for msg in request.messages]

        # process_agent_request 在流式模式下直接返回异步生成器对象（不是协程）
        async_gen = agent_service.process_agent_request(
            messages=messages,
            stream=True,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            model_name=request.model_name
        )

        async for chunk in async_gen:
            yield chunk.encode("utf-8") if isinstance(chunk, str) else chunk

    except Exception as e:
        logger.error(f"Agent 流式响应错误: {str(e)}", exc_info=True)
        error_data = json.dumps({
            "error": str(e),
            "success": False
        })
        yield f"data: {error_data}\n\n".encode("utf-8")


@router.post("/agent/stream")
async def agent_stream(
    request: ChatRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Agent 流式接口（空实现）

    使用 Server-Sent Events (SSE) 返回流式响应

    - **messages**: 消息历史列表
    - **stream**: 必须为 true
    - **temperature**: 温度参数 (0.0-2.0)
    - **max_tokens**: 最大token数 (1-8192)
    - **model_name**: 模型名称
    """
    if not request.stream:
        raise HTTPException(
            status_code=400,
            detail="Agent 流式接口需要将 stream 设置为 true"
        )

    return StreamingResponse(
        agent_stream_generator(agent_service, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )
