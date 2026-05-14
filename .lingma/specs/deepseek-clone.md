# DeepSeek Chat 克隆项目实施方案

## Context

用户希望创建一个类似 https://chat.deepseek.com/ 的 AI 聊天网站，采用以下技术栈：
- **前端**: React
- **后端**: Python + LangChain
- **核心功能**: 基础对话 + 代码高亮
- **AI 模型**: 智谱AI GLM-4 (BigModel)
- **UI 风格**: 简洁现代风

---

## 推荐方案

### 技术栈选型

**前端**:
- React 18+ (Vite 构建)
- Tailwind CSS + shadcn/ui (简洁现代 UI)
- react-markdown + rehype-prism-plus (Markdown 渲染和代码高亮)
- Vercel AI SDK 或自定义 SSE Hook (流式响应处理)
- Zustand (状态管理)
- Lucide React (图标)

**后端**:
- FastAPI (异步 Web 框架)
- LangChain + langchain-glm (智谱AI LLM 集成)
- ChatZhipuAI 模型 (glm-4 默认)
- pydantic-settings (配置管理)
- uvicorn (ASGI 服务器)

### 智谱AI集成要点

**安装依赖**:
```bash
pip install langchain-glm
# 或
pip install langchain_zhipu
```

**环境变量配置**:
```env
ZHIPUAI_API_KEY=your-api-key-from-bigmodel
ZHIPUAI_API_BASE=https://open.bigmodel.cn/api/paas/v4/
```

**模型初始化示例**:
```python
from langchain_glm import ChatZhipuAI

llm = ChatZhipuAI(
    model="glm-4",
    temperature=0.7,
    max_tokens=2048,
    streaming=True
)
```

**可用模型**:
- `glm-4`: 通用对话模型（128K上下文，推荐）
- `glm-4v`: 多模态视觉模型（支持图片理解）
- `glm-3-turbo`: 快速响应模型
- `glm-4-alltools`: 支持AllTools功能

---

## 实施步骤

### Phase 1: 项目初始化

1. **创建项目结构**
   ```
   deepseek-clone/
   ├── frontend/          # React 前端
   └── backend/           # Python 后端
   ```

2. **前端初始化**
   - 使用 Vite 创建 React + TypeScript 项目
   - 安装 Tailwind CSS 并配置
   - 安装 shadcn/ui 及必要依赖

3. **后端初始化**
   - 创建 Python 虚拟环境
   - 安装 FastAPI、LangChain、uvicorn 等依赖
   - 配置项目结构和环境变量

### Phase 2: 后端开发

4. **配置管理** (`backend/app/config.py`)
   - 使用 pydantic-settings 管理环境变量
   - 配置智谱AI API Key (ZHIPUAI_API_KEY)、CORS、服务器参数

5. **数据模型定义** (`backend/app/models/`)
   - 请求模型: ChatRequest (messages, stream, temperature)
   - 响应模型: ChatResponse, ErrorResponse

6. **LLM 服务层** (`backend/app/services/llm_service.py`)
   - 封装 LangChain ChatZhipuAI (智谱AI GLM-4)
   - 实现流式和非流式两种调用方式
   - 消息格式转换 (LangChain Message 格式)
   - 支持模型选择: glm-4, glm-4v, glm-3-turbo

7. **聊天业务逻辑** (`backend/app/services/chat_service.py`)
   - 消息验证
   - 调用 LLM 服务
   - 错误处理

8. **API 路由** (`backend/app/routers/chat.py`)
   - POST `/api/v1/chat` - 非流式接口
   - POST `/api/v1/chat/stream` - 流式接口 (SSE)
   - GET `/health` - 健康检查

9. **主应用配置** (`backend/app/main.py`)
   - CORS 中间件配置
   - 全局异常处理
   - 路由注册

### Phase 3: 前端开发

10. **UI 组件库设置**
    - 配置 shadcn/ui 主题（简洁现代风格）
    - 创建基础组件: Button, Input, ScrollArea

11. **聊天核心组件**
    - `ChatContainer.tsx` - 主聊天容器（侧边栏 + 主区域）
    - `MessageList.tsx` - 消息列表（虚拟滚动优化）
    - `MessageBubble.tsx` - 单条消息气泡（区分用户/AI）
    - `ChatInput.tsx` - 输入框组件（多行、自动高度）
    - `TypingIndicator.tsx` - 打字指示器动画

12. **Markdown 渲染组件**
    - `MarkdownRenderer.tsx` - 配置 react-markdown
    - `CodeBlock.tsx` - 代码块组件（Prism.js 高亮 + 复制按钮）
    - 支持 GFM、数学公式、表格等

13. **状态管理** (`frontend/src/stores/chatStore.ts`)
    - Zustand store: messages, currentSession, isLoading
    - Actions: addMessage, updateLastMessage, clearChat
    - 持久化到 localStorage (使用 zustand/middleware persist)
    - 会话历史列表管理（创建、删除、切换）

14. **流式聊天 Hook** (`frontend/src/hooks/useChat.ts`)
    - 使用 Vercel AI SDK 的 useChat Hook
    - 配置 API 端点指向后端流式接口
    - 支持中断生成、错误处理
    - 自动管理消息状态

15. **样式和主题**
    - 配置 Tailwind 主题色（简洁现代风，白色为主）
    - 暗色模式支持
    - 响应式设计（移动端侧边栏抽屉式）

### Phase 4: 集成与测试

16. **前后端联调**
    - 配置前端代理指向后端 API
    - 测试流式响应是否正常
    - 验证代码高亮效果

17. **错误处理优化**
    - 前端: API 错误提示、加载状态
    - 后端: 完善的错误码和日志

18. **性能优化**
    - 虚拟滚动长对话列表
    - 代码分割懒加载
    - 防抖输入

---

## 关键文件清单

### 后端
- `backend/app/config.py` - 配置管理
- `backend/app/models/request.py` - 请求模型
- `backend/app/models/response.py` - 响应模型
- `backend/app/services/llm_service.py` - LLM 服务 (ChatZhipuAI)
- `backend/app/services/chat_service.py` - 聊天业务
- `backend/app/routers/chat.py` - API 路由
- `backend/app/main.py` - 应用入口
- `backend/.env.example` - 环境变量模板 (ZHIPUAI_API_KEY)
- `backend/requirements.txt` - Python 依赖 (langchain-glm)

### 前端
- `frontend/src/components/chat/ChatContainer.tsx` - 主容器
- `frontend/src/components/chat/MessageList.tsx` - 消息列表
- `frontend/src/components/chat/MessageBubble.tsx` - 消息气泡
- `frontend/src/components/chat/ChatInput.tsx` - 输入框
- `frontend/src/components/chat/TypingIndicator.tsx` - 打字指示器
- `frontend/src/components/chat/CodeBlock.tsx` - 代码块
- `frontend/src/components/chat/MarkdownRenderer.tsx` - Markdown 渲染
- `frontend/src/hooks/useChat.ts` - 聊天 Hook
- `frontend/src/stores/chatStore.ts` - 状态管理
- `frontend/src/App.tsx` - 应用根组件
- `frontend/tailwind.config.js` - Tailwind 配置

---

## 后端依赖 (requirements.txt)

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
langchain==0.1.0
langchain-glm==0.1.0
python-dotenv==1.0.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-multipart==0.0.6
```

## 前端依赖 (package.json 关键部分)

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "ai": "^3.0.0",
    "@ai-sdk/react": "^0.0.0",
    "zustand": "^4.5.0",
    "react-markdown": "^9.0.0",
    "rehype-prism-plus": "^2.0.0",
    "remark-gfm": "^4.0.0",
    "remark-math": "^6.0.0",
    "rehype-katex": "^7.0.0",
    "lucide-react": "^0.300.0",
    "tailwindcss": "^3.4.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0"
  }
}
```

## 环境变量模板 (.env.example)

```bash
# 智谱AI API Key (从 https://open.bigmodel.cn/ 获取)
ZHIPUAI_API_KEY=your-api-key-here

# API 基础 URL (可选，默认使用官方地址)
ZHIPUAI_API_BASE=https://open.bigmodel.cn/api/paas/v4/

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=false

# CORS 配置
ALLOWED_ORIGINS=http://localhost:5173,https://yourdomain.com

# 日志级别
LOG_LEVEL=INFO

# 模型配置
MODEL_NAME=glm-4
TEMPERATURE=0.7
MAX_TOKENS=2048
```

---

## 验证方法

### 后端测试
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 ZHIPUAI_API_KEY (从 https://open.bigmodel.cn/ 获取)
uvicorn app.main:app --reload
# 访问 http://localhost:8000/docs 查看 API 文档
# 访问 http://localhost:8000/health 检查健康状态
```

### 前端测试
```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
# 测试发送消息、流式响应、代码高亮等功能
```

### 端到端测试
1. 启动后端服务
2. 启动前端开发服务器
3. 在浏览器中发送测试消息
4. 验证流式输出效果
5. 发送包含代码块的消息，验证高亮效果
6. 检查响应式布局（移动端适配）

---

## 注意事项

1. **API Key 安全**: 永远不要在前端暴露智谱AI API Key，所有 LLM 调用必须通过后端
2. **CORS 配置**: 开发环境允许 localhost，生产环境指定具体域名
3. **流式响应**: 确保禁用 Nginx 缓冲 (X-Accel-Buffering: no)
4. **错误处理**: 完善的错误提示和日志记录
5. **性能**: 长对话使用虚拟滚动，避免 DOM 节点过多
6. **智谱AI模型选择**: 
   - `glm-4`: 通用对话模型（推荐）
   - `glm-4v`: 多模态视觉模型（支持图片理解）
   - `glm-3-turbo`: 快速响应模型
7. **API Key 获取**: 访问 https://open.bigmodel.cn/ 注册并获取 API Key
