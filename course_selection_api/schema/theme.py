from typing import Optional, List
from pydantic import BaseModel, Field


class ThemeCreateRequest(BaseModel):
    """創建主題的請求模型"""
    theme_code: str = Field(..., description="主題代碼", example="A101")
    theme_name: str = Field(..., description="主題名稱", example="聯合國全球永續發展目標")
    theme_short_name: str = Field(..., description="主題簡稱", example="SDGs")
    theme_english_name: str = Field(..., description="主題英文名稱", example="SDGs")
    chinese_link: Optional[str] = Field(None, description="中文說明連結網址", example="https://globalgoals.tw/")
    english_link: Optional[str] = Field(None, description="英文說明連結網址")
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class ThemeUpdateRequest(BaseModel):
    """更新主題的請求模型"""
    theme_code: Optional[str] = Field(None, description="主題代碼（可修改）", example="A101")
    theme_name: Optional[str] = Field(None, description="主題名稱", example="聯合國全球永續發展目標")
    theme_short_name: Optional[str] = Field(None, description="主題簡稱", example="SDGs")
    theme_english_name: Optional[str] = Field(None, description="主題英文名稱", example="SDGs")
    chinese_link: Optional[str] = Field(None, description="中文說明連結網址", example="https://globalgoals.tw/")
    english_link: Optional[str] = Field(None, description="英文說明連結網址")
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class ThemeResponse(BaseModel):
    """主題回應模型"""
    id: str = Field(..., description="主題ID (UUID)")
    theme_code: str = Field(..., description="主題代碼")
    theme_name: str = Field(..., description="主題名稱")
    theme_short_name: str = Field(..., description="主題簡稱")
    theme_english_name: str = Field(..., description="主題英文名稱")
    chinese_link: Optional[str] = Field(None, description="中文說明連結網址")
    english_link: Optional[str] = Field(None, description="英文說明連結網址")
    created_at: Optional[str] = Field(None, description="創建時間")
    updated_at: Optional[str] = Field(None, description="更新時間")
    created_by: Optional[str] = Field(None, description="建立者")
    updated_by: Optional[str] = Field(None, description="最後更新者")


class ThemeListResponse(BaseModel):
    """主題列表回應模型"""
    themes: List[ThemeResponse]


class ThemeCreateResponse(BaseModel):
    """創建主題回應模型"""
    id: str
    theme_code: str
    theme_name: str
    message: str


class ThemeUpdateResponse(BaseModel):
    """更新主題回應模型"""
    id: str
    theme_code: str
    theme_name: str
    message: str


class ThemeDeleteResponse(BaseModel):
    """刪除主題回應模型"""
    id: str
    theme_code: str
    message: str


class SubThemeCreateRequest(BaseModel):
    """創建細項主題的請求模型"""
    coures_themes_id: str = Field(..., description="主題ID (UUID)", example="550e8400-e29b-41d4-a716-446655440000")
    sub_theme_code: str = Field(..., description="細項主題代碼", example="01")
    sub_theme_name: str = Field(..., description="細項主題名稱", example="消除貧窮")
    sub_theme_english_name: str = Field(..., description="細項主題英文名稱", example="No Poverty")
    sub_theme_content: Optional[str] = Field(None, description="細項主題中文內容說明", example="消除各地一切形式的貧窮")
    sub_theme_english_content: Optional[str] = Field(None, description="細項主題英文內容說明", example="End poverty in all its forms everywhere")
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class SubThemeUpdateRequest(BaseModel):
    """更新細項主題的請求模型"""
    coures_themes_id: Optional[str] = Field(None, description="主題ID (UUID)（可修改）", example="550e8400-e29b-41d4-a716-446655440000")
    sub_theme_code: Optional[str] = Field(None, description="細項主題代碼（可修改）", example="01")
    sub_theme_name: Optional[str] = Field(None, description="細項主題名稱", example="消除貧窮")
    sub_theme_english_name: Optional[str] = Field(None, description="細項主題英文名稱", example="No Poverty")
    sub_theme_content: Optional[str] = Field(None, description="細項主題中文內容說明", example="消除各地一切形式的貧窮")
    sub_theme_english_content: Optional[str] = Field(None, description="細項主題英文內容說明", example="End poverty in all its forms everywhere")
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class SubThemeResponse(BaseModel):
    """細項主題回應模型"""
    id: str = Field(..., description="細項主題ID (UUID)")
    coures_themes_id: str = Field(..., description="主題ID (UUID)")
    theme_code: str = Field(..., description="主題代碼")
    sub_theme_code: str = Field(..., description="細項主題代碼")
    sub_theme_name: str = Field(..., description="細項主題名稱")
    sub_theme_english_name: str = Field(..., description="細項主題英文名稱")
    sub_theme_content: Optional[str] = Field(None, description="細項主題中文內容說明")
    sub_theme_english_content: Optional[str] = Field(None, description="細項主題英文內容說明")
    created_at: Optional[str] = Field(None, description="創建時間")
    updated_at: Optional[str] = Field(None, description="更新時間")
    created_by: Optional[str] = Field(None, description="建立者")
    updated_by: Optional[str] = Field(None, description="最後更新者")


class SubThemeListResponse(BaseModel):
    """細項主題列表回應模型"""
    sub_themes: List[SubThemeResponse]


class SubThemeCreateResponse(BaseModel):
    """創建細項主題回應模型"""
    id: str
    theme_code: str
    sub_theme_code: str
    sub_theme_name: str
    message: str


class SubThemeUpdateResponse(BaseModel):
    """更新細項主題回應模型"""
    id: str
    theme_code: str
    sub_theme_code: str
    sub_theme_name: str
    message: str


class SubThemeDeleteResponse(BaseModel):
    """刪除細項主題回應模型"""
    id: str
    sub_theme_code: str
    message: str


class ThemeDeleteRequest(BaseModel):
    """刪除主題的請求模型"""
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")


class SubThemeDeleteRequest(BaseModel):
    """刪除細項主題的請求模型"""
    user_id: str = Field(..., description="用戶 ID", example="user123")
    token: str = Field(..., description="認證 token")
