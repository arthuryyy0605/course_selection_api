from fastapi import APIRouter, Depends, status
from course_selection_api.lib.response import ExceptionResponse, SingleResponse, to_json_response
from course_selection_api.schema.theme import (
    ThemeCreateRequest, ThemeCreateResponse, ThemeUpdateRequest, ThemeUpdateResponse,
    ThemeDeleteResponse, ThemeListResponse, ThemeDeleteRequest, ThemeResponse,
    SubThemeCreateRequest, SubThemeCreateResponse, SubThemeUpdateRequest, SubThemeUpdateResponse,
    SubThemeDeleteResponse, SubThemeListResponse, SubThemeDeleteRequest, SubThemeResponse
)
from course_selection_api.data_access_object.db import get_db_connection
from course_selection_api.business_model.theme_business import ThemeBusiness, SubThemeBusiness

router = APIRouter(prefix="/themes", tags=["themes"])
sub_router = APIRouter(prefix="/sub_themes", tags=["sub_themes"])


# 主題相關 API
@router.post("/", response_model=SingleResponse[ThemeCreateResponse], status_code=status.HTTP_201_CREATED)
async def create_theme(request: ThemeCreateRequest, conn=Depends(get_db_connection)):
    """創建新主題"""
    result = await ThemeBusiness.create_theme(conn, request)
    return to_json_response(SingleResponse(result=result))


@router.get("/", response_model=SingleResponse[ThemeListResponse])
async def get_all_themes(conn=Depends(get_db_connection)):
    """獲取所有主題列表"""
    result = await ThemeBusiness.get_all_themes(conn)
    return to_json_response(SingleResponse(result=result))


@router.get("/{theme_id}", response_model=SingleResponse[ThemeResponse])
async def get_theme_by_id(theme_id: str, conn=Depends(get_db_connection)):
    """根據主題ID獲取主題"""
    from course_selection_api.data_access_object.theme_dao import ThemeDAO
    from fastapi import HTTPException
    
    theme = await ThemeDAO.get_theme_by_id(conn, theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail=f"主題ID '{theme_id}' 不存在")
    
    return to_json_response(SingleResponse(result=theme))


@router.put("/{theme_id}", response_model=SingleResponse[ThemeUpdateResponse])
async def update_theme(
    theme_id: str,
    request: ThemeUpdateRequest,
    conn=Depends(get_db_connection)
):
    """根據主題ID更新主題資訊"""
    result = await ThemeBusiness.update_theme(conn, theme_id, request)
    return to_json_response(SingleResponse(result=result))


@router.delete("/{theme_id}", 
              responses={400: {'model': ExceptionResponse}, 404: {'model': ExceptionResponse}},
              response_model=SingleResponse[ThemeDeleteResponse])
async def delete_theme(
    theme_id: str,
    request: ThemeDeleteRequest,
    conn=Depends(get_db_connection)
):
    """根據主題ID刪除主題"""
    result = await ThemeBusiness.delete_theme(conn, theme_id, request)
    return to_json_response(SingleResponse(result=result))


# 細項主題相關 API
@sub_router.get("/", response_model=SingleResponse[SubThemeListResponse])
async def get_all_sub_themes(conn=Depends(get_db_connection)):
    """獲取所有細項主題列表"""
    result = await SubThemeBusiness.get_all_sub_themes(conn)
    return to_json_response(SingleResponse(result=result))


@sub_router.get("/by_theme/{theme_id}", response_model=SingleResponse[SubThemeListResponse])
async def get_sub_themes_by_theme_id(
    theme_id: str,
    conn=Depends(get_db_connection)
):
    """根據主題ID查詢細項主題列表"""
    from course_selection_api.data_access_object.theme_dao import SubThemeDAO
    sub_themes = await SubThemeDAO.get_sub_themes_by_theme_id(conn, theme_id)
    result = {"sub_themes": sub_themes}
    return to_json_response(SingleResponse(result=result))


@sub_router.get("/{sub_theme_id}", response_model=SingleResponse[SubThemeResponse])
async def get_sub_theme_by_id(sub_theme_id: str, conn=Depends(get_db_connection)):
    """根據細項主題ID獲取細項主題"""
    from course_selection_api.data_access_object.theme_dao import SubThemeDAO
    from fastapi import HTTPException
    
    sub_theme = await SubThemeDAO.get_sub_theme_by_id(conn, sub_theme_id)
    if not sub_theme:
        raise HTTPException(status_code=404, detail=f"細項主題ID '{sub_theme_id}' 不存在")
    
    return to_json_response(SingleResponse(result=sub_theme))


@sub_router.post("/", response_model=SingleResponse[SubThemeCreateResponse], status_code=status.HTTP_201_CREATED)
async def create_sub_theme(request: SubThemeCreateRequest, conn=Depends(get_db_connection)):
    """創建新細項主題"""
    result = await SubThemeBusiness.create_sub_theme(conn, request)
    return to_json_response(SingleResponse(result=result))


@sub_router.put("/{sub_theme_id}", response_model=SingleResponse[SubThemeUpdateResponse])
async def update_sub_theme(
    sub_theme_id: str,
    request: SubThemeUpdateRequest,
    conn=Depends(get_db_connection)
):
    """根據細項主題ID更新細項主題資訊"""
    result = await SubThemeBusiness.update_sub_theme(conn, sub_theme_id, request)
    return to_json_response(SingleResponse(result=result))


@sub_router.delete("/{sub_theme_id}",
                  responses={400: {'model': ExceptionResponse}, 404: {'model': ExceptionResponse}},
                  response_model=SingleResponse[SubThemeDeleteResponse])
async def delete_sub_theme(
    sub_theme_id: str,
    request: SubThemeDeleteRequest,
    conn=Depends(get_db_connection)
):
    """根據細項主題ID刪除細項主題"""
    result = await SubThemeBusiness.delete_sub_theme(conn, sub_theme_id, request)
    return to_json_response(SingleResponse(result=result))
