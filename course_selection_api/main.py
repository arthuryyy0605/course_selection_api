import os
from fastapi import FastAPI
from course_selection_api.lib.base_exception import UniqueViolationException, ParameterViolationException, \
    hy_exception_to_json_response, add_exception_handler, use_route_names_as_operation_ids
from course_selection_api.lib.logger import get_prefix_logger_adapter
from course_selection_api.config import get_settings
from starlette.middleware.cors import CORSMiddleware

from course_selection_api.endpoints import register_routers

# 匯入 oracledb
try:
    import oracledb
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False
    oracledb = None

setting = get_settings()
logger = get_prefix_logger_adapter(__name__)

# Security: Disable API documentation in production
# Set ENABLE_API_DOCS=true in development environment to enable docs
enable_docs = setting.ENABLE_API_DOCS

if enable_docs:
    logger.info("API documentation is ENABLED - suitable for development only")
    app = FastAPI(
        title="課程選擇系統 API", 
        description="課程主題維護與管理系統",
        version="1.0.0", 
        openapi_url="/api/spec/swagger.json",
        docs_url="/api/spec/doc",
        redoc_url="/api/spec/redoc"
    )
else:
    logger.info("API documentation is DISABLED - production security mode")
    app = FastAPI(
        title="課程選擇系統 API", 
        description="課程主題維護與管理系統",
        version="1.0.0", 
        openapi_url=None,
        docs_url=None, 
        redoc_url=None
    )
app.add_middleware(CORSMiddleware,
                   allow_origins='*',
                   allow_credentials=True,
                   allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                   allow_headers=["*"]
                   )

add_exception_handler(app)

# 註冊 Oracle 資料庫異常處理器
if ORACLE_AVAILABLE:
    @app.exception_handler(oracledb.IntegrityError)
    async def db_integrity_exception_handler(request, exc: oracledb.IntegrityError):
        error_str = str(exc)
        # 檢查是否為唯一約束錯誤
        if 'ORA-00001' in error_str or 'unique constraint' in error_str.lower():
            return hy_exception_to_json_response(UniqueViolationException(message=error_str))
        # 檢查是否為外鍵約束錯誤
        elif 'ORA-02291' in error_str or 'ORA-02292' in error_str or 'foreign key constraint' in error_str.lower():
            return hy_exception_to_json_response(ParameterViolationException(message=error_str))
        else:
            return hy_exception_to_json_response(ParameterViolationException(message=error_str))


# Register all API routers
register_routers(app)

# 添加健康檢查端點
@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "service": "course-selection-api"}

use_route_names_as_operation_ids(app)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run('course_selection_api.main:app', host="0.0.0.0", port=8000, reload=True)
