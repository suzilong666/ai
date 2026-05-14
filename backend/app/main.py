"""
FastAPI 应用主入口 - MVC Application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import get_settings
import os
import glob
import importlib
from pathlib import Path

# 配置日志
import os
from logging.handlers import RotatingFileHandler

settings = get_settings()
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

# 创建日志目录
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 配置根日志记录器
logger = logging.getLogger()
logger.setLevel(log_level)

# 清除现有的handler（避免重复）
logger.handlers.clear()

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)

# 文件处理器（带轮转，最大10MB，保留5个备份）
file_handler = RotatingFileHandler(
    os.path.join(log_dir, 'app.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(log_level)
file_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s")
file_handler.setFormatter(file_format)
logger.addHandler(file_handler)

# 获取当前模块的logger
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    settings = get_settings()
    logger.info(f"应用启动 - 环境: {'development' if settings.DEBUG else 'production'}")
    logger.info(f"允许的来源: {settings.allowed_origins_list}")
    logger.info(f"使用模型: {settings.MODEL_NAME}")

    yield

    # 关闭时执行
    logger.info("应用关闭")


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用工厂

    Returns:
        FastAPI 应用实例
    """
    settings = get_settings()

    app = FastAPI(
        title="DeepSeek Clone Chat API",
        description="基于 LangChain 和智谱AI GLM的聊天 API",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )

    # ==================== CORS 配置 ====================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )

    # ==================== 注册路由 (Controllers) ====================
    # 自动发现并注册所有控制器
    controllers_dir = Path(__file__).parent / "controllers"
    controller_files = glob.glob(str(controllers_dir / "*_controller.py"))
    
    for controller_file in controller_files:
        # 获取模块名（不包含 .py 扩展名）
        module_name = Path(controller_file).stem
        
        try:
            # 动态导入模块
            module = importlib.import_module(f"app.controllers.{module_name}")
            
            # 查找名为 'router' 的属性
            if hasattr(module, 'router'):
                router = getattr(module, 'router')
                app.include_router(router)
                logger.info(f"已注册路由: {module_name}")
            else:
                logger.warning(f"控制器 {module_name} 中未找到 'router' 属性")
                
        except Exception as e:
            logger.error(f"注册控制器 {module_name} 时出错: {str(e)}")

    # ==================== 全局异常处理 ====================

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """请求验证错误处理"""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"]
            })

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": "请求参数验证失败",
                "details": errors
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """通用异常处理"""
        logger.error(f"未处理的异常: {str(exc)}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "服务器内部错误",
                "details": str(exc) if settings.DEBUG else None
            }
        )

    return app


# 创建应用实例
app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
