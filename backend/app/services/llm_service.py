"""
LLM 服务层 - MVC Service 层
封装大模型的调用逻辑，使用 LangChain 统一接口，支持多厂商切换
"""
import logging
from typing import AsyncGenerator, List, Dict, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.config import Settings

logger = logging.getLogger(__name__)


class LLMService:
    """LLM 服务类 - 负责与大模型 API 交互（支持多厂商）"""

    def __init__(self, settings: Settings):
        self.settings = settings

    def _create_llm(self, model_name: str = None, temperature: float = None,
                    max_tokens: int = None, streaming: bool = False) -> BaseChatModel:
        """
        创建 LLM 实例（使用 LangChain 统一接口，支持多厂商）

        Args:
            model_name: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            streaming: 是否启用流式输出

        Returns:
            BaseChatModel 实例（LangChain 统一接口）
        """
        provider = self.settings.LLM_PROVIDER.lower()
        
        # 根据配置动态选择 LLM 提供商
        if provider == "zhipuai":
            return self._create_zhipuai_llm(model_name, temperature, max_tokens, streaming)
        elif provider == "openai":
            return self._create_openai_llm(model_name, temperature, max_tokens, streaming)
        elif provider == "anthropic":
            return self._create_anthropic_llm(model_name, temperature, max_tokens, streaming)
        else:
            raise ValueError(f"不支持的 LLM 提供商: {provider}")
    
    def _create_zhipuai_llm(self, model_name: str, temperature: float,
                           max_tokens: int, streaming: bool) -> BaseChatModel:
        """创建智谱AI LLM 实例"""
        from langchain_community.chat_models import ChatZhipuAI
        
        if not self.settings.ZHIPUAI_API_KEY:
            raise ValueError("ZHIPUAI_API_KEY 未配置")
        
        return ChatZhipuAI(
            api_key=self.settings.ZHIPUAI_API_KEY,
            model=model_name or self.settings.MODEL_NAME,
            temperature=temperature or self.settings.TEMPERATURE,
            max_tokens=max_tokens or self.settings.MAX_TOKENS,
            streaming=streaming,
        )
    
    def _create_openai_llm(self, model_name: str, temperature: float,
                          max_tokens: int, streaming: bool) -> BaseChatModel:
        """创建 OpenAI LLM 实例"""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError("请安装 langchain-openai: pip install langchain-openai")
        
        if not self.settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未配置")
        
        return ChatOpenAI(
            api_key=self.settings.OPENAI_API_KEY,
            base_url=self.settings.OPENAI_API_BASE,
            model=model_name or "gpt-3.5-turbo",
            temperature=temperature or self.settings.TEMPERATURE,
            max_tokens=max_tokens or self.settings.MAX_TOKENS,
            streaming=streaming,
        )
    
    def _create_anthropic_llm(self, model_name: str, temperature: float,
                             max_tokens: int, streaming: bool) -> BaseChatModel:
        """创建 Anthropic LLM 实例"""
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError("请安装 langchain-anthropic: pip install langchain-anthropic")
        
        if not self.settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY 未配置")
        
        return ChatAnthropic(
            api_key=self.settings.ANTHROPIC_API_KEY,
            model=model_name or "claude-3-sonnet-20240229",
            temperature=temperature or self.settings.TEMPERATURE,
            max_tokens_to_sample=max_tokens or self.settings.MAX_TOKENS,
            streaming=streaming,
        )

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List:
        """
        转换消息格式为 LangChain 格式

        Args:
            messages: 原始消息列表 [{"role": "...", "content": "..."}]

        Returns:
            LangChain Message 列表
        """
        langchain_messages = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))

        return langchain_messages

    async def chat_non_stream(self, messages: List[Dict[str, str]],
                              temperature: float = None,
                              max_tokens: int = None,
                              model_name: str = None) -> Dict[str, Any]:
        """
        非流式聊天

        Args:
            messages: 消息历史
            temperature: 温度参数
            max_tokens: 最大token数
            model_name: 模型名称

        Returns:
            包含回复和用量的字典
        """
        try:
            langchain_messages = self._convert_messages(messages)

            llm = self._create_llm(
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=False
            )

            response = await llm.ainvoke(langchain_messages)

            # 记录响应内容用于调试
            logger.debug(f"LLM non-stream response: {repr(response.content)}")

            # 提取 token 使用信息
            usage = {}
            if hasattr(response, 'response_metadata') and response.response_metadata:
                token_usage = response.response_metadata.get('token_usage', {})
                usage = {
                    "prompt_tokens": token_usage.get('prompt_tokens', 0),
                    "completion_tokens": token_usage.get('completion_tokens', 0),
                    "total_tokens": token_usage.get('total_tokens', 0)
                }

            return {
                "message": response.content,
                "model": model_name or self.settings.MODEL_NAME,
                "usage": usage
            }

        except Exception as e:
            logger.error(f"LLM 调用失败: {str(e)}", exc_info=True)
            raise

    async def chat_stream(self, messages: List[Dict[str, str]],
                          temperature: float = None,
                          max_tokens: int = None,
                          model_name: str = None) -> AsyncGenerator[str, None]:
        """
        流式聊天 - 生成器模式

        Args:
            messages: 消息历史
            temperature: 温度参数
            max_tokens: 最大token数
            model_name: 模型名称

        Yields:
            SSE 格式的 token 数据
        """
        try:
            langchain_messages = self._convert_messages(messages)

            llm = self._create_llm(
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=True
            )

            content = ""

            # 使用 astream 方法进行流式调用
            async for chunk in llm.astream(langchain_messages):
                if chunk.content:
                    content += chunk.content
                    # 返回 SSE 格式的数据
                    yield f"{chunk.content}"

            yield ""

            logger.debug(f"LLM stream completed, total content: {repr(content)}")

        except Exception as e:
            logger.error(f"流式 LLM 调用失败: {str(e)}", exc_info=True)
            import json
            error_data = json.dumps({"error": str(e)})
            yield f"data: {error_data}\n\n"
            yield "data: [DONE]\n\n"
