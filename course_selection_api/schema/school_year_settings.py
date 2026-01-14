from typing import Optional, List
from pydantic import BaseModel, Field


# 學年期細項主題資訊（需要在其他 Schema 之前定義）
class SchoolYearSubThemeInfo(BaseModel):
    """學年期細項主題資訊"""
    sub_theme_id: Optional[str] = Field(None, description="細項主題ID (UUID)")
    sub_theme_code: str = Field(..., description="細項主題代碼")
    sub_theme_name: str = Field(..., description="細項主題名稱")
    sub_theme_english_name: str = Field(..., description="細項主題英文名稱")
    sub_theme_content: Optional[str] = Field(None, description="細項主題中文內容說明")
    sub_theme_english_content: Optional[str] = Field(None, description="細項主題英文內容說明")
    enabled: bool = Field(False, description="是否啟用（在該學年期設定中）")


# 學年期主題設定相關 Schema
class SchoolYearThemeSettingCreateRequest(BaseModel):
    """創建學年期主題設定的請求模型"""
    academic_year: int = Field(..., description="學年", example=114)
    academic_term: int = Field(..., description="學期", example=1)
    theme_code: str = Field(..., description="主題代碼", example="A101")
    fill_in_week_enabled: bool = Field(True, description="是否需要填寫週次", example=True)
    scale_max: int = Field(..., description="該主題指標數量(該主題下所有細項共用)", example=3, ge=1, le=10)
    select_most_relevant_sub_theme_enabled: bool = Field(False, description="是否需要讓使用者勾選最相關科目", example=False)
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class SchoolYearThemeSettingUpdateRequest(BaseModel):
    """更新學年期主題設定的請求模型"""
    fill_in_week_enabled: Optional[bool] = Field(None, description="是否需要填寫週次", example=True)
    scale_max: Optional[int] = Field(None, description="該主題指標數量(該主題下所有細項共用)", example=3, ge=1, le=10)
    select_most_relevant_sub_theme_enabled: Optional[bool] = Field(None, description="是否需要讓使用者勾選最相關科目", example=False)
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class SchoolYearThemeSettingResponse(BaseModel):
    """學年期主題設定回應模型"""
    id: Optional[str] = Field(None, description="設定ID (UUID)")
    academic_year: int = Field(..., description="學年")
    academic_term: int = Field(..., description="學期")
    coures_themes_id: Optional[str] = Field(None, description="主題ID (UUID)")
    theme_id: Optional[str] = Field(None, description="主題ID (UUID)")
    theme_code: str = Field(..., description="主題代碼")
    theme_name: str = Field(..., description="主題名稱")
    fill_in_week_enabled: bool = Field(..., description="是否需要填寫週次")
    scale_max: int = Field(..., description="該主題指標數量")
    select_most_relevant_sub_theme_enabled: bool = Field(..., description="是否需要讓使用者勾選最相關科目")
    sub_themes: List[SchoolYearSubThemeInfo] = Field(default_factory=list, description="細項主題列表")
    created_at: Optional[str] = Field(None, description="創建時間")
    updated_at: Optional[str] = Field(None, description="更新時間")


class SchoolYearThemeSettingListResponse(BaseModel):
    """學年期主題設定列表回應模型"""
    settings: List[SchoolYearThemeSettingResponse]


# 學年期細項主題設定相關 Schema
class SchoolYearSubThemeSettingCreateRequest(BaseModel):
    """創建學年期細項主題設定的請求模型"""
    academic_year: int = Field(..., description="學年", example=114)
    academic_term: int = Field(..., description="學期", example=1)
    theme_code: str = Field(..., description="主題代碼", example="A101")
    sub_theme_code: str = Field(..., description="細項主題代碼", example="01")
    enabled: bool = Field(True, description="是否啟用", example=True)
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class SchoolYearSubThemeSettingUpdateRequest(BaseModel):
    """更新學年期細項主題設定的請求模型"""
    enabled: bool = Field(..., description="是否啟用", example=True)
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class SchoolYearSubThemeSettingResponse(BaseModel):
    """學年期細項主題設定回應模型"""
    id: Optional[str] = Field(None, description="設定ID (UUID)")
    academic_year: int = Field(..., description="學年")
    academic_term: int = Field(..., description="學期")
    coures_sub_themes_id: Optional[str] = Field(None, description="細項主題ID (UUID)")
    sub_theme_id: Optional[str] = Field(None, description="細項主題ID (UUID)")
    coures_themes_id: Optional[str] = Field(None, description="主題ID (UUID)")
    theme_code: str = Field(..., description="主題代碼")
    sub_theme_code: str = Field(..., description="細項主題代碼")
    sub_theme_name: str = Field(..., description="細項主題名稱")
    enabled: bool = Field(..., description="是否啟用")
    created_at: Optional[str] = Field(None, description="創建時間")
    updated_at: Optional[str] = Field(None, description="更新時間")


class SchoolYearSubThemeSettingListResponse(BaseModel):
    """學年期細項主題設定列表回應模型"""
    settings: List[SchoolYearSubThemeSettingResponse]


# 教師填寫表單相關 Schema (給前端顯示用)
class TeacherFormSubThemeOption(BaseModel):
    """教師填寫表單的細項選項"""
    sub_theme_id: Optional[str] = Field(None, description="細項主題ID (UUID)")
    sub_theme_code: str = Field(..., description="細項主題代碼")
    sub_theme_name: str = Field(..., description="細項主題名稱")
    sub_theme_english_name: str = Field(..., description="細項主題英文名稱")
    sub_theme_content: Optional[str] = Field(None, description="細項主題中文內容說明")
    sub_theme_english_content: Optional[str] = Field(None, description="細項主題英文內容說明")
    current_value: Optional[str] = Field(None, description="目前填寫的值")
    week_numbers: Optional[List[int]] = Field(None, description="目前填寫的週次列表")
    is_most_relevant: Optional[bool] = Field(None, description="是否為最相關科目")
    entry_id: Optional[str] = Field(None, description="記錄ID (UUID)，用於更新操作")


class TeacherFormThemeGroup(BaseModel):
    """教師填寫表單的主題群組"""
    theme_id: Optional[str] = Field(None, description="主題ID (UUID)")
    theme_code: str = Field(..., description="主題代碼")
    theme_name: str = Field(..., description="主題名稱")
    fill_in_week_enabled: bool = Field(..., description="是否需要填寫週次")
    scale_max: int = Field(..., description="該主題指標數量(所有細項共用)")
    select_most_relevant_sub_theme_enabled: bool = Field(..., description="是否需要讓使用者勾選最相關科目")
    sub_themes: List[TeacherFormSubThemeOption] = Field(..., description="細項主題選項")


class TeacherFormResponse(BaseModel):
    """教師填寫表單回應模型"""
    school_year_semester: str = Field(..., description="學年期")
    course_id: str = Field(..., description="課程ID")
    themes: List[TeacherFormThemeGroup] = Field(..., description="主題群組")


# 通用回應模型
class SettingCreateResponse(BaseModel):
    """設定創建回應模型"""
    message: str = Field(..., description="回應訊息")


class SettingUpdateResponse(BaseModel):
    """設定更新回應模型"""
    message: str = Field(..., description="回應訊息")


class SettingDeleteResponse(BaseModel):
    """設定刪除回應模型"""
    message: str = Field(..., description="回應訊息")


# 學年期完整資訊相關 Schema
class SchoolYearThemeInfo(BaseModel):
    """學年期主題資訊"""
    theme_id: Optional[str] = Field(None, description="主題ID (UUID)")
    theme_code: str = Field(..., description="主題代碼")
    theme_name: str = Field(..., description="主題名稱")
    theme_short_name: str = Field(..., description="主題簡稱")
    theme_english_name: str = Field(..., description="主題英文名稱")
    fill_in_week_enabled: bool = Field(..., description="是否需要填寫週次")
    scale_max: int = Field(..., description="指標數量")
    select_most_relevant_sub_theme_enabled: bool = Field(..., description="是否需要讓使用者勾選最相關科目")
    sub_themes: List[SchoolYearSubThemeInfo] = Field(..., description="細項主題列表")


class SchoolYearSummaryStats(BaseModel):
    """學年期統計摘要"""
    total_themes: int = Field(..., description="總主題數量")
    total_sub_themes: int = Field(..., description="總細項數量")
    enabled_sub_themes: int = Field(..., description="啟用的細項數量")


class SchoolYearThemeSummary(BaseModel):
    """主題摘要資訊"""
    theme_code: str = Field(..., description="主題代碼")
    theme_name: str = Field(..., description="主題名稱")
    scale_max: int = Field(..., description="指標數量")
    sub_themes_count: int = Field(..., description="細項數量")
    enabled_sub_themes_count: int = Field(..., description="啟用的細項數量")


class SchoolYearCompleteInfoResponse(BaseModel):
    """學年期完整資訊回應模型"""
    academic_year: int = Field(..., description="學年")
    academic_term: int = Field(..., description="學期")
    summary: SchoolYearSummaryStats = Field(..., description="統計摘要")
    themes_summary: List[SchoolYearThemeSummary] = Field(..., description="主題摘要列表")
    themes: List[SchoolYearThemeInfo] = Field(..., description="詳細主題列表")


# 教師填寫相關 Schema
class CourseEntryCreateRequest(BaseModel):
    """課程填寫創建請求"""
    subj_no: str = Field(..., description="課程代碼 (SUBJ_NO，對應 COFSUBJ.SUBJ_NO)")
    ps_class_nbr: str = Field(..., description="課程流水號 (PS_CLASS_NBR，對應 SCHOOL.COFOPMS.PS_CLASS_NBR)")
    academic_year: int = Field(..., description="學年", example=113)
    academic_term: int = Field(..., description="學期", example=1)
    sub_theme_code: str = Field(..., description="細項主題代碼")
    indicator_value: str = Field(..., description="指標值")
    week_numbers: Optional[List[int]] = Field(None, description="週次列表")
    is_most_relevant: Optional[bool] = Field(False, description="是否為最相關科目", example=False)
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class CourseEntriesBatchCreateRequest(BaseModel):
    """課程填寫批量創建請求"""
    entries: List[CourseEntryCreateRequest] = Field(..., description="填寫記錄列表")
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class CourseEntryUpdateRequest(BaseModel):
    """課程填寫更新請求"""
    indicator_value: str = Field(..., description="指標值")
    week_numbers: Optional[List[int]] = Field(None, description="週次列表")
    is_most_relevant: Optional[bool] = Field(None, description="是否為最相關科目")
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class CourseEntryDeleteRequest(BaseModel):
    """課程填寫刪除請求"""
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class CourseEntryResponse(BaseModel):
    """課程填寫回應"""
    id: Optional[str] = Field(None, description="記錄ID (UUID)")
    subj_no: str = Field(..., description="課程代碼")
    ps_class_nbr: str = Field(..., description="課程流水號")
    academic_year: int = Field(..., description="學年")
    academic_term: int = Field(..., description="學期")
    coures_sub_themes_id: Optional[str] = Field(None, description="細項主題ID (UUID)")
    sub_theme_id: Optional[str] = Field(None, description="細項主題ID (UUID)")
    theme_code: str = Field(..., description="主題代碼")
    sub_theme_code: str = Field(..., description="細項主題代碼")
    indicator_value: str = Field(..., description="指標值")
    week_numbers: Optional[List[int]] = Field(None, description="週次列表")
    is_most_relevant: bool = Field(..., description="是否為最相關科目")
    created_at: str = Field(..., description="創建時間")
    updated_at: str = Field(..., description="更新時間")


class CourseEntryListResponse(BaseModel):
    """課程填寫記錄列表回應模型"""
    entries: List[CourseEntryResponse]


class CourseIdListResponse(BaseModel):
    """課程 ID 列表回應"""
    course_ids: List[str] = Field(..., description="課程ID列表")


class TeacherFormDataResponse(BaseModel):
    """教師表單數據回應"""
    course_id: str = Field(..., description="課程代碼 (即 SUBJ_NO)")
    ps_class_nbr: str = Field(..., description="課程流水號 (PS_CLASS_NBR)")
    course_chinese_name: str = Field(..., description="課程中文名稱")
    course_english_name: str = Field(..., description="課程英文名稱")
    academic_year: int = Field(..., description="學年")
    academic_term: int = Field(..., description="學期")
    themes: List[TeacherFormThemeGroup] = Field(..., description="主題組列表")


class SchoolYearThemeSettingDeleteRequest(BaseModel):
    """刪除學年期主題設定的請求模型"""
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class SchoolYearSubThemeSettingDeleteRequest(BaseModel):
    """刪除學年期細項主題設定的請求模型"""
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class CourseEntriesCopyRequest(BaseModel):
    """複製課程記錄到新學年期的請求模型"""
    source_academic_year: int = Field(..., description="來源學年", example=113)
    source_academic_term: int = Field(..., description="來源學期", example=1)
    target_academic_year: int = Field(..., description="目標學年", example=113)
    target_academic_term: int = Field(..., description="目標學期", example=2)
    subj_no: str = Field(..., description="課程代碼 (SUBJ_NO)", example="SUBJ001")
    ps_class_nbr: str = Field(..., description="課程流水號 (PS_CLASS_NBR)", example="12345")
    user_id: str = Field(..., description="操作用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class CourseEntriesCopyResponse(BaseModel):
    """複製課程記錄回應模型"""
    message: str = Field(..., description="操作結果訊息")
    copied_count: int = Field(..., description="成功複製的記錄數")
    skipped_count: int = Field(..., description="跳過的記錄數（目標學年期無此設定）")
    deleted_count: int = Field(..., description="刪除的記錄數（目標學年期原有記錄）")


class SchoolYearThemeSettingsCopyRequest(BaseModel):
    """複製學年期主題設定請求模型"""
    source_academic_year: int = Field(..., description="來源學年", example=113)
    source_academic_term: int = Field(..., description="來源學期", example=1)
    target_academic_year: int = Field(..., description="目標學年", example=114)
    target_academic_term: int = Field(..., description="目標學期", example=1)
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class SchoolYearThemeSettingsCopyResponse(BaseModel):
    """複製學年期主題設定回應模型"""
    message: str = Field(..., description="操作結果訊息")
    themes_count: int = Field(..., description="複製的主題數量")
    sub_themes_count: int = Field(..., description="複製的子主題數量")


# CSV 匯出篩選相關 Schema
class CourseExportFilterRequest(BaseModel):
    """課程匯出篩選請求模型"""
    academic_year_start: int = Field(..., description="學年期起（學年）", example=114)
    academic_term_start: int = Field(..., description="學年期起（學期）", example=1)
    academic_year_end: int = Field(..., description="學年期訖（學年）", example=114)
    academic_term_end: int = Field(..., description="學年期訖（學期）", example=1)
    department: Optional[str] = Field(None, description="開課單位代碼（可選）", example="U36")
    has_class: Optional[str] = Field(None, description="成班與否 Y/N（可選）", example="Y")
    theme_code: Optional[str] = Field(None, description="主題代碼（可選，過濾有填寫該主題的課程）", example="A101")
    sub_theme_code: Optional[str] = Field(None, description="細項主題代碼（可選，過濾有填寫該細項的課程）", example="01")
