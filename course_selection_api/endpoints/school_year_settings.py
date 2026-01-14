from fastapi import APIRouter, HTTPException, status, Depends
from course_selection_api.schema.school_year_settings import (
    SchoolYearThemeSettingCreateRequest,
    SchoolYearThemeSettingUpdateRequest,
    SchoolYearThemeSettingResponse,
    SchoolYearThemeSettingListResponse,
    SchoolYearThemeSettingDeleteRequest,
    SchoolYearSubThemeSettingCreateRequest,
    SchoolYearSubThemeSettingUpdateRequest,
    SchoolYearSubThemeSettingResponse,
    SchoolYearSubThemeSettingListResponse,
    SchoolYearSubThemeSettingDeleteRequest,
)
from course_selection_api.business_model.school_year_settings_business import (
    SchoolYearThemeSettingsBusiness,
    SchoolYearSubThemeSettingsBusiness
)
from course_selection_api.data_access_object.db import get_db_connection

# 創建路由器
router = APIRouter(tags=["學年期設定管理"])


# ========== 學年期主題設定 API ==========

@router.post(
    "/school-year-theme-settings",
    response_model=SchoolYearThemeSettingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="創建學年期主題設定",
    description="為指定學年期創建主題設定，包含週次填寫設定和指標數量"
)
async def create_school_year_theme_setting(request: SchoolYearThemeSettingCreateRequest, conn=Depends(get_db_connection)):
    """
    創建學年期主題設定
    
    建立某學年期需要哪些主題及其設定
    """
    try:
        result = await SchoolYearThemeSettingsBusiness.create_school_year_theme_setting(
            conn,
            request.dict()
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建學年期主題設定失敗: {str(e)}"
        )


@router.get(
    "/school-year-theme-settings/{setting_id}",
    response_model=SchoolYearThemeSettingResponse,
    summary="查詢單一學年期主題設定",
    description="查詢特定設定ID的主題設定"
)
async def get_school_year_theme_setting(setting_id: str, conn=Depends(get_db_connection)):
    """
    查詢單一學年期主題設定
    
    獲取特定設定ID的詳細設定
    
    Args:
        setting_id: 設定ID (UUID)
    """
    try:
        result = await SchoolYearThemeSettingsBusiness.get_school_year_theme_setting_by_id(conn, setting_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢學年期主題設定失敗: {str(e)}"
        )


@router.get(
    "/school-year-theme-settings/{academic_year}/{academic_term}",
    response_model=SchoolYearThemeSettingListResponse,
    summary="查詢學年期所有主題設定",
    description="查詢特定學年期的所有主題設定"
)
async def get_school_year_theme_settings(academic_year: int, academic_term: int, conn=Depends(get_db_connection)):
    """
    查詢學年期所有主題設定
    
    獲取特定學年期的所有主題設定列表
    
    Args:
        academic_year: 學年 (例: 113)
        academic_term: 學期 (例: 1=上學期, 2=下學期)
    """
    try:
        results = await SchoolYearThemeSettingsBusiness.get_school_year_theme_settings_by_year(
            conn, academic_year, academic_term
        )
        return {"settings": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢學年期主題設定列表失敗: {str(e)}"
        )


@router.put(
    "/school-year-theme-settings/{setting_id}",
    response_model=SchoolYearThemeSettingResponse,
    summary="更新學年期主題設定",
    description="更新特定設定ID的主題設定"
)
async def update_school_year_theme_setting(
    setting_id: str,
    request: SchoolYearThemeSettingUpdateRequest,
    conn=Depends(get_db_connection)
):
    """
    更新學年期主題設定
    
    修改學年期主題的設定（週次填寫、指標數量等）
    
    Args:
        setting_id: 設定ID (UUID)
    """
    try:
        result = await SchoolYearThemeSettingsBusiness.update_school_year_theme_setting(
            conn, setting_id, request.dict(exclude_unset=True)
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新學年期主題設定失敗: {str(e)}"
        )


@router.delete(
    "/school-year-theme-settings/{setting_id}",
    summary="刪除學年期主題設定",
    description="刪除特定設定ID的主題設定（會自動刪除該主題下的所有子主題設定）"
)
async def delete_school_year_theme_setting(
    setting_id: str,
    request: SchoolYearThemeSettingDeleteRequest,
    conn=Depends(get_db_connection)
):
    """
    刪除學年期主題設定
    
    移除學年期主題設定，會先自動刪除該主題下的所有子主題設定，再刪除主題設定本身。
    這是為了避免外鍵約束錯誤。
    
    Args:
        setting_id: 設定ID (UUID)
    """
    try:
        result = await SchoolYearThemeSettingsBusiness.delete_school_year_theme_setting(
            conn, setting_id, request.dict()
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除學年期主題設定失敗: {str(e)}"
        )


# ========== 學年期細項主題設定 API ==========

@router.post(
    "/school-year-sub-theme-settings",
    response_model=SchoolYearSubThemeSettingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="創建學年期細項設定",
    description="為指定學年期主題創建細項設定"
)
async def create_school_year_sub_theme_setting(request: SchoolYearSubThemeSettingCreateRequest, conn=Depends(get_db_connection)):
    """
    創建學年期細項設定
    
    建立某學年期某主題下需要哪些細項及其啟用狀態
    """
    try:
        result = await SchoolYearSubThemeSettingsBusiness.create_school_year_sub_theme_setting(
            conn,
            request.dict()
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建學年期細項設定失敗: {str(e)}"
        )


@router.get(
    "/school-year-sub-theme-settings/{setting_id}",
    response_model=SchoolYearSubThemeSettingResponse,
    summary="查詢單一學年期細項設定",
    description="查詢特定設定ID的細項設定"
)
async def get_school_year_sub_theme_setting(setting_id: str, conn=Depends(get_db_connection)):
    """
    查詢單一學年期細項設定
    
    獲取特定設定ID的詳細設定
    
    Args:
        setting_id: 設定ID (UUID)
    """
    try:
        result = await SchoolYearSubThemeSettingsBusiness.get_school_year_sub_theme_setting_by_id(conn, setting_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢學年期細項設定失敗: {str(e)}"
        )


@router.get(
    "/school-year-sub-theme-settings/{academic_year}/{academic_term}/{theme_id}",
    response_model=SchoolYearSubThemeSettingListResponse,
    summary="查詢學年期主題下所有細項設定",
    description="查詢特定學年期特定主題下的所有細項設定"
)
async def get_school_year_sub_theme_settings(academic_year: int, academic_term: int, theme_id: str, conn=Depends(get_db_connection)):
    """
    查詢學年期主題下所有細項設定
    
    獲取特定學年期特定主題下的所有細項設定列表
    
    Args:
        academic_year: 學年 (例: 113)
        academic_term: 學期 (例: 1=上學期, 2=下學期)
        theme_id: 主題ID (UUID)
    """
    try:
        # 先通過 theme_id 獲取 theme_code（用於業務邏輯層）
        from course_selection_api.data_access_object.theme_dao import ThemeDAO
        theme = await ThemeDAO.get_theme_by_id(conn, theme_id)
        if not theme:
            raise HTTPException(status_code=404, detail=f"主題ID '{theme_id}' 不存在")
        
        results = await SchoolYearSubThemeSettingsBusiness.get_school_year_sub_theme_settings_by_theme(
            conn, academic_year, academic_term, theme['theme_code']
        )
        return {"settings": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢學年期細項設定列表失敗: {str(e)}"
        )


@router.put(
    "/school-year-sub-theme-settings/{setting_id}",
    response_model=SchoolYearSubThemeSettingResponse,
    summary="更新學年期細項設定",
    description="更新特定設定ID的細項設定"
)
async def update_school_year_sub_theme_setting(
    setting_id: str,
    request: SchoolYearSubThemeSettingUpdateRequest,
    conn=Depends(get_db_connection)
):
    """
    更新學年期細項設定
    
    修改學年期細項的啟用狀態
    
    Args:
        setting_id: 設定ID (UUID)
    """
    try:
        result = await SchoolYearSubThemeSettingsBusiness.update_school_year_sub_theme_setting(
            conn, setting_id, request.dict()
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新學年期細項設定失敗: {str(e)}"
        )


@router.delete(
    "/school-year-sub-theme-settings/{setting_id}",
    summary="刪除學年期細項設定",
    description="刪除特定設定ID的細項設定"
)
async def delete_school_year_sub_theme_setting(
    setting_id: str,
    request: SchoolYearSubThemeSettingDeleteRequest,
    conn=Depends(get_db_connection)
):
    """
    刪除學年期細項設定
    
    移除學年期細項設定
    
    Args:
        setting_id: 設定ID (UUID)
    """
    try:
        result = await SchoolYearSubThemeSettingsBusiness.delete_school_year_sub_theme_setting(
            conn, setting_id, request.dict()
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除學年期細項設定失敗: {str(e)}"
        )
