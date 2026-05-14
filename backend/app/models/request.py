"""
请求数据模型定义 - MVC Model 层
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    """单条消息模型"""
    role: str = Field(..., description="消息角色: user, assistant, system")
    content: str = Field(default="", description="消息内容")


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[Message] = Field(..., min_length=1, description="消息历史")
    stream: bool = Field(False, description="是否启用流式响应")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(2048, ge=1, le=8192, description="最大token数")
    model_name: Optional[str] = Field("glm-4", description="模型名称")

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "system", "content": "你是一个有用的助手"},
                    {"role": "user", "content": "你好！"}
                ],
                "stream": True,
                "temperature": 0.7,
                "model_name": "glm-4"
            }
        }
