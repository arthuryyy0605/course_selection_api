from fastapi import FastAPI

# Import all router modules
from .auth import router as auth_router
from .theme import router as theme_router, sub_router as sub_theme_router
from .school_year import router as school_year_router
from .school_year_settings import router as school_year_settings_router
from .token_auth import router as token_auth_router


def register_routers(app: FastAPI):
    """Register all API routers with the FastAPI app"""
    # app.include_router(auth_router)
    # 所有路由都添加 /api 前綴
    app.include_router(theme_router, prefix="/api")
    app.include_router(sub_theme_router, prefix="/api")
    app.include_router(school_year_router, prefix="/api")
    app.include_router(school_year_settings_router, prefix="/api")
    app.include_router(token_auth_router, prefix="/api")
