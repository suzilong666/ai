"""
应用配置管理 - MVC Config
使用 pydantic-settings 进行类型安全的环境变量管理
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    # LLM 提供商配置
    LLM_PROVIDER: str = "zhipuai"  # 可选: zhipuai, openai, anthropic, etc.
    
    # 智谱AI 配置
    ZHIPUAI_API_KEY: str = ""
    ZHIPUAI_API_BASE: str = "https://open.bigmodel.cn/api/paas/v4/"
    
    # OpenAI 配置（示例）
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    
    # Anthropic 配置（示例）
    ANTHROPIC_API_KEY: str = ""

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # CORS 配置
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    # 日志配置
    LOG_LEVEL: str = "INFO"

    # 模型配置
    MODEL_NAME: str = "glm-4"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 2048

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        """将逗号分隔的字符串转换为列表"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例（带缓存）"""
    return Settings()
