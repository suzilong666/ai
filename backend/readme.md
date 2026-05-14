## 启动服务
```
cd backend;python -m uvicorn app.main:app --reload
```

## LLM 提供商配置

本项目使用 LangChain 统一接口，支持多种大模型提供商。通过修改 `.env` 文件中的 `LLM_PROVIDER` 配置即可切换。

### 当前支持的提供商

1. **智谱AI (zhipuai)** - 默认
   - 需要安装: `zhipuai` (已包含在 requirements.txt)
   - 配置项: `ZHIPUAI_API_KEY`
   
2. **OpenAI**
   - 需要安装: `pip install langchain-openai`
   - 配置项: `OPENAI_API_KEY`, `OPENAI_API_BASE`
   
3. **Anthropic (Claude)**
   - 需要安装: `pip install langchain-anthropic`
   - 配置项: `ANTHROPIC_API_KEY`

### 切换示例

#### 切换到 OpenAI

1. 安装依赖:
```bash
pip install langchain-openai
```

2. 修改 `.env` 文件:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-3.5-turbo
```

#### 切换到 Anthropic Claude

1. 安装依赖:
```bash
pip install langchain-anthropic
```

2. 修改 `.env` 文件:
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key
MODEL_NAME=claude-3-sonnet-20240229
```

### 添加新的提供商

如需添加其他提供商（如 Google Gemini、Azure OpenAI 等），只需：

1. 在 `app/config.py` 中添加相应的 API Key 配置
2. 在 `app/services/llm_service.py` 中添加对应的 `_create_xxx_llm()` 方法
3. 在 `_create_llm()` 方法中添加分支判断

无需修改其他业务逻辑代码！