"""
测试 API 控制器 - MVC Controller 层 (FastAPI Router)
"""
import logging
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.response import ErrorResponse

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["test"],
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        401: {"model": ErrorResponse, "description": "认证失败"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)

def get_weather(city: str) -> str:
    """获取指定城市的天气。"""
    return f"{city}总是阳光明媚！"


@router.get("/test")
def test():
    # 创建 LLM 实例
    llm = ChatOpenAI(
        temperature=0.7,
        model="glm-5.1",
        openai_api_key="cf2cf3ac12154cc48fa83a821ac4208f.2a2n5gPScA24QKtY",
        openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
    )

    # 创建消息
    messages = [
        SystemMessage(content="你是一个有用的 AI 助手"),
        HumanMessage(content="请介绍一下人工智能的发展历程")
    ]

    # 流式生成器函数
    async def generate_stream():
        try:
            # 使用 stream() 方法进行流式调用
            for chunk in llm.stream(messages):
                # 提取内容并格式化为 SSE 格式
                if hasattr(chunk, 'content') and chunk.content:
                    data = {"content": chunk.content}
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            
            # 发送结束标记
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_data = {"error": str(e)}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    # 返回流式响应
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )
