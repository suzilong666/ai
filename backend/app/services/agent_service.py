"""
Agent 业务逻辑层 - MVC Service 层
"""
import logging
from typing import List, Dict, Any
from fastapi import HTTPException

from app.config import Settings
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class AgentService:
    """Agent 服务类 - 负责 Agent 业务逻辑"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm_service = LLMService(settings)

    def process_agent_request(self, messages: List[Dict[str, str]],
                              stream: bool = False,
                              temperature: float = None,
                              max_tokens: int = None,
                              model_name: str = None) -> Any:
        """
        处理 Agent 请求

        Args:
            messages: 消息历史
            stream: 是否流式响应
            temperature: 温度参数
            max_tokens: 最大token数
            model_name: 模型名称

        Returns:
            Agent 响应或流式生成器
        """
        # 验证消息
        self._validate_messages(messages)

        if stream:
            # 返回异步生成器（注意：这里不调用 await，直接返回协程）
            return self.llm_service.agent_stream(
                messages, temperature, max_tokens, model_name
            )
        else:
            # TODO: 非流式模式需要 await（目前 llm_service 未实现 agent_non_stream）
            import asyncio
            raise NotImplementedError("非流式 Agent 功能尚未实现")

    def _validate_messages(self, messages: List[Dict[str, str]]) -> None:
        """
        验证消息格式

        Args:
            messages: 待验证的消息列表

        Raises:
            HTTPException: 当消息格式无效时
        """
        if not messages:
            raise HTTPException(
                status_code=400,
                detail="消息列表不能为空"
            )

        valid_roles = {"user", "assistant", "system"}

        for i, msg in enumerate(messages):
            if "role" not in msg or "content" not in msg:
                raise HTTPException(
                    status_code=400,
                    detail=f"第 {i+1} 条消息缺少 role 或 content 字段"
                )

            if msg["role"] not in valid_roles:
                raise HTTPException(
                    status_code=400,
                    detail=f"第 {i+1} 条消息的 role 必须是 user、assistant 或 system"
                )

            # 允许空内容，但在实际处理时可能需要特殊处理
            # 这里暂时保留警告日志，但不抛出异常
            if not msg["content"].strip():
                logger.warning(f"第 {i+1} 条消息的内容为空")
