from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Query, Depends
from fastapi.responses import StreamingResponse
from course_selection_api.schema.school_year_settings import (
    SchoolYearCompleteInfoResponse,
    CourseEntryCreateRequest,
    CourseEntriesBatchCreateRequest,
    CourseEntryUpdateRequest,
    CourseEntryDeleteRequest,
    CourseEntryResponse,
    CourseIdListResponse,
    TeacherFormDataResponse,
    CourseEntriesCopyRequest,
    CourseEntriesCopyResponse,
    SchoolYearThemeSettingsCopyRequest,
    SchoolYearThemeSettingsCopyResponse,
    CourseExportFilterRequest
)
from course_selection_api.business_model.school_year_business import SchoolYearBusiness
from course_selection_api.data_access_object.db import get_db_connection

# 創建路由器
router = APIRouter(tags=["學年期與課程管理"])


@router.get(
    "/school-years/{academic_year}/{academic_term}",
    response_model=SchoolYearCompleteInfoResponse,
    summary="獲取學年期完整資訊",
    description="獲取指定學年期的所有主題、細項、指標設定等完整資訊，包含統計摘要"
)
async def get_school_year_info(academic_year: int, academic_term: int, conn=Depends(get_db_connection)):
    """
    獲取學年期完整資訊
    
    包含：
    - 統計摘要（主題數量、細項數量等）
    - 主題摘要列表
    - 詳細主題和細項列表
    - 每個主題的指標類型和數量設定
    - 是否需要填寫週次
    
    Args:
        academic_year: 學年 (例: 113)
        academic_term: 學期 (例: 1=上學期, 2=下學期)
    """
    try:
        result = await SchoolYearBusiness.get_school_year_complete_info(conn, academic_year, academic_term)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取學年期完整資訊失敗: {str(e)}"
        )


@router.get(
    "/courses/{course_id}/form-data/{academic_year}/{academic_term}",
    response_model=TeacherFormDataResponse,
    summary="獲取教師表單資料",
    description="獲取指定課程的表單資料（包含課程中英文名稱），用於教師填寫"
)
async def get_teacher_form_data(
    course_id: str, 
    academic_year: int, 
    academic_term: int,
    ps_class_nbr: str = Query(..., description="課程流水號 (PS_CLASS_NBR)"),
    conn=Depends(get_db_connection)
):
    """
    獲取教師表單資料
    
    包含：
    - 課程中文名稱 (course_chinese_name)
    - 課程英文名稱 (course_english_name)
    - 學年 (academic_year)
    - 學期 (academic_term)
    - 該學年期該課程可填寫的主題和細項
    - 每個細項的當前填寫狀態
    - 指標類型和選項
    
    Args:
        course_id: 課程代碼 (SUBJ_NO)
        ps_class_nbr: 課程流水號 (PS_CLASS_NBR)
        academic_year: 學年 (例: 113)
        academic_term: 學期 (例: 1=上學期, 2=下學期)
    """
    try:
        result = await SchoolYearBusiness.get_teacher_form_data(conn, course_id, ps_class_nbr, academic_year, academic_term)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取教師表單資料失敗: {str(e)}"
        )


@router.post(
    "/course-entries",
    response_model=List[CourseEntryResponse],
    summary="批量創建課程填寫記錄",
    description="教師一次填寫多個課程指標記錄"
)
async def create_course_entries_batch(batch_request: CourseEntriesBatchCreateRequest, conn=Depends(get_db_connection)):
    """
    批量創建課程填寫記錄
    
    支援一次創建多個填寫記錄，提高效率
    """
    try:
        entries_data = [entry.dict() for entry in batch_request.entries]
        results = await SchoolYearBusiness.create_course_entries_batch(
            conn,
            entries_data,
            batch_request.user_id,
            batch_request.token
        )
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量創建課程填寫記錄失敗: {str(e)}"
        )


@router.post(
    "/course-entries/single",
    response_model=CourseEntryResponse,
    summary="創建單一課程填寫記錄",
    description="創建單一課程指標記錄"
)
async def create_course_entry_single(entry: CourseEntryCreateRequest, conn=Depends(get_db_connection)):
    """
    創建單一課程填寫記錄
    
    教師填寫指定課程的主題細項指標值
    """
    try:
        result = await SchoolYearBusiness.create_course_entry(conn, entry.dict())
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建課程填寫記錄失敗: {str(e)}"
        )


@router.put(
    "/course-entries/{entry_id}",
    response_model=CourseEntryResponse,
    summary="更新課程填寫記錄",
    description="更新已存在的課程填寫記錄"
)
async def update_course_entry(entry_id: str, entry: CourseEntryUpdateRequest, conn=Depends(get_db_connection)):
    """
    更新課程填寫記錄
    
    修改已填寫的指標值或週次
    """
    try:
        result = await SchoolYearBusiness.update_course_entry_by_id(conn, entry_id, entry.dict())
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新課程填寫記錄失敗: {str(e)}"
        )


@router.delete(
    "/course-entries/{entry_id}",
    response_model=CourseEntryResponse,
    summary="刪除課程填寫記錄",
    description="刪除指定 ID 的課程填寫記錄"
)
async def delete_course_entry(entry_id: str, delete_request: CourseEntryDeleteRequest, conn=Depends(get_db_connection)):
    """
    刪除課程填寫記錄
    
    透過 entry_id 刪除指定的課程填寫記錄，需要提供 user_id 和 token 進行驗證
    """
    try:
        result = await SchoolYearBusiness.delete_course_entry_by_id(conn, entry_id, delete_request.dict())
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除課程填寫記錄失敗: {str(e)}"
        )


@router.get(
    "/school-years/{academic_year}/{academic_term}/themes/{theme_id}/sub-themes/{sub_theme_id}/courses",
    response_model=CourseIdListResponse,
    summary="查詢已填寫指定細項的課程列表",
    description="根據學年期、主題ID和細項ID，查詢已填寫該細項的所有課程"
)
async def get_courses_by_sub_theme(
        academic_year: int,
        academic_term: int,
        theme_id: str,
        sub_theme_id: str,
        conn=Depends(get_db_connection)
):
    """
    查詢已填寫指定細項的課程列表
    
    返回已經填寫了指定學年期、主題和細項的所有課程ID
    
    Args:
        academic_year: 學年 (例: 113)
        academic_term: 學期 (例: 1=上學期, 2=下學期)
        theme_id: 主題ID (UUID)
        sub_theme_id: 細項主題ID (UUID)
    """
    try:
        # 通過 ID 獲取 code（用於業務邏輯層）
        from course_selection_api.data_access_object.theme_dao import ThemeDAO, SubThemeDAO
        theme = await ThemeDAO.get_theme_by_id(conn, theme_id)
        sub_theme = await SubThemeDAO.get_sub_theme_by_id(conn, sub_theme_id)
        
        if not theme:
            raise HTTPException(status_code=404, detail=f"主題ID '{theme_id}' 不存在")
        if not sub_theme:
            raise HTTPException(status_code=404, detail=f"細項主題ID '{sub_theme_id}' 不存在")
        
        course_ids = await SchoolYearBusiness.get_courses_by_sub_theme(
            conn, academic_year, academic_term, theme['theme_code'], sub_theme['sub_theme_code']
        )
        return {"course_ids": course_ids}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢課程列表失敗: {str(e)}"
        )


@router.get(
    "/course-entries/exists",
    summary="檢查課程記錄是否存在",
    description="檢查指定課程是否已有填寫記錄"
)
async def check_course_entries_exist(
        course_id: str = Query(..., description="課程代碼 (SUBJ_NO)"),
        ps_class_nbr: str = Query(..., description="課程流水號 (PS_CLASS_NBR)"),
        academic_year: int = Query(..., description="學年 (例: 113)"),
        academic_term: int = Query(..., description="學期 (例: 1=上學期, 2=下學期)"),
        conn=Depends(get_db_connection)
):
    """
    檢查課程記錄是否存在
    
    前端可透過此 API 確認課程是否已有填寫記錄
    
    Args:
        course_id: 課程代碼 (SUBJ_NO)
        ps_class_nbr: 課程流水號 (PS_CLASS_NBR)
        academic_year: 學年 (例: 113)
        academic_term: 學期 (例: 1=上學期, 2=下學期)
    """
    try:
        exists = await SchoolYearBusiness.check_course_entries_exist(conn, course_id, ps_class_nbr, academic_year, academic_term)
        return {"exists": exists}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"檢查課程記錄失敗: {str(e)}"
        )


@router.post(
    "/school-years/copy-settings",
    response_model=SchoolYearThemeSettingsCopyResponse,
    status_code=status.HTTP_200_OK,
    summary="複製學年期主題設定",
    description="從來源學年期複製所有主題設定和細項主題設定到目標學年期"
)
async def copy_school_year_settings(
    request: SchoolYearThemeSettingsCopyRequest,
    conn=Depends(get_db_connection)
):
    """
    複製學年期主題設定
    
    從來源學年期複製所有主題設定（academic_year_coures_themes_setting）
    和細項主題設定（academic_year_coures_sub_theme_settings）到目標學年期。
    
    邏輯：
    1. 驗證 token
    2. 檢查來源學年期是否存在主題設定
    3. 檢查目標學年期是否已存在主題設定（如果存在則返回錯誤）
    4. 複製所有主題設定到目標學年期
    5. 複製所有細項主題設定到目標學年期
    6. 更新 created_by 和 updated_by 為當前用戶
    
    返回：
    - themes_count: 成功複製的主題設定數
    - sub_themes_count: 成功複製的細項主題設定數
    """
    try:
        # 調用複製主題設定的業務邏輯
        from course_selection_api.business_model.school_year_settings_business import \
            SchoolYearThemeSettingsCopyBusiness
        result = await SchoolYearThemeSettingsCopyBusiness.copy_school_year_theme_settings(conn, request.dict())
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"複製課程記錄失敗: {str(e)}"
        )


@router.get(
    "/school-years/{academic_year}/{academic_term}/export-csv",
    summary="匯出課程資料為 CSV（簡易版）",
    description="匯出指定學年期的所有課程資料為 CSV 格式檔案（不含 COFOPMS 完整欄位）"
)
async def export_course_entries_csv(
    academic_year: int,
    academic_term: int,
    conn=Depends(get_db_connection)
):
    """
    匯出課程資料為 CSV（簡易版）
    
    根據指定的學年期，匯出所有課程的填寫記錄為 CSV 格式。
    CSV 包含課程基本資訊（學年期、課程代碼、流水號）以及按主題分組的資料
    （最相關子主題、子主題指標值、週次等）。
    
    注意：此為舊版 API，建議使用 POST /school-years/export-csv 獲取完整欄位。
    
    Args:
        academic_year: 學年 (例: 114)
        academic_term: 學期 (例: 1=上學期, 2=下學期)
    
    Returns:
        CSV 檔案（使用 StreamingResponse）
    """
    try:
        csv_content = await SchoolYearBusiness.export_course_entries_to_csv(
            conn, academic_year, academic_term
        )
        
        # 將 CSV 內容轉換為 bytes（UTF-8-sig 編碼）
        csv_bytes = csv_content.encode('utf-8-sig')
        
        # 建立檔名
        filename = f"course_entries_{academic_year}_{academic_term}.csv"
        
        # 使用 StreamingResponse 回傳 CSV
        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv; charset=utf-8-sig",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"匯出 CSV 失敗: {str(e)}"
        )


@router.post(
    "/school-years/export-csv",
    summary="匯出課程資料為 CSV（含篩選條件）",
    description="""
    匯出課程資料為 CSV 格式檔案，支援篩選條件。
    
    匯出欄位包含：
    - 序號、學年期、選課號碼、開課系所、科目內碼、課程名稱
    - 教師姓名、學分、選課人數、開課人數、成班與否
    - 必選修、全/半年、是否合班、授課群、英文EMI、課程含自主學習
    - 主題勾選欄位（主題簡稱-細項主題名稱）
    """
)
async def export_course_entries_csv_with_filters(
    filter_request: CourseExportFilterRequest,
    conn=Depends(get_db_connection)
):
    """
    匯出課程資料為 CSV（含篩選條件）
    
    支援以下篩選條件：
    - 學年期起/訖（必填）
    - 開課單位（可選）
    - 成班與否（可選）
    - 主題代碼（可選，過濾有填寫該主題的課程）
    - 細項主題代碼（可選，過濾有填寫該細項的課程）
    
    Returns:
        CSV 檔案（使用 StreamingResponse）
    """
    try:
        csv_content = await SchoolYearBusiness.export_course_entries_to_csv_with_filters(
            conn,
            filter_request.academic_year_start,
            filter_request.academic_term_start,
            filter_request.academic_year_end,
            filter_request.academic_term_end,
            filter_request.department,
            filter_request.has_class,
            filter_request.theme_code,
            filter_request.sub_theme_code
        )
        
        # 將 CSV 內容轉換為 bytes（UTF-8-sig 編碼）
        csv_bytes = csv_content.encode('utf-8-sig')
        
        # 建立檔名
        filename = f"course_entries_{filter_request.academic_year_start}{filter_request.academic_term_start}_{filter_request.academic_year_end}{filter_request.academic_term_end}.csv"
        
        # 使用 StreamingResponse 回傳 CSV
        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv; charset=utf-8-sig",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"匯出 CSV 失敗: {str(e)}"
        )
