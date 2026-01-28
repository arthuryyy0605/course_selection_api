from typing import Dict, Any, List
from fastapi import HTTPException, status
from course_selection_api.data_access_object.school_year_settings_dao import (
    SchoolYearThemeSettingsDAO,
    SchoolYearSubThemeSettingsDAO
)
from course_selection_api.lib.auth_library.simple_token import SimpleTokenAuth


def format_datetime_fields(data: Dict) -> Dict:
    """格式化資料字典中的日期時間欄位"""
    if 'created_at' in data and data['created_at']:
        data['created_at'] = data['created_at'].isoformat()
    if 'updated_at' in data and data['updated_at']:
        data['updated_at'] = data['updated_at'].isoformat()
    return data


class SchoolYearThemeSettingsBusiness:
    """學年期主題設定業務邏輯"""

    @staticmethod
    async def create_school_year_theme_setting(conn, data: Dict[str, Any]) -> Dict[str, Any]:
        """創建學年期主題設定"""
        # 驗證 token
        SimpleTokenAuth.verify_token(data['token'], data['user_id'])

        try:
            result = await SchoolYearThemeSettingsDAO.create_school_year_theme_setting(
                conn,
                data['academic_year'],
                data['academic_term'],
                data['theme_code'],
                data['fill_in_week_enabled'],
                data.get('scale_max', 3),
                data.get('select_most_relevant_sub_theme_enabled', False),
                created_by=data['user_id']
            )
            # 格式化時間
            return format_datetime_fields(dict(result)) if result else {}
        except Exception as e:
            if 'unique constraint' in str(e).lower() or 'duplicate' in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"學年 {data['academic_year']} 學期 {data['academic_term']} 的主題 {data['theme_code']} 設定已存在"
                )
            raise

    @staticmethod
    async def get_school_year_theme_setting_by_id(conn, setting_id: str) -> Dict[str, Any]:
        """獲取特定學年期主題設定（通過 ID，包含 sub_themes）"""
        result = await SchoolYearThemeSettingsDAO.get_school_year_theme_setting_by_id(conn, setting_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到設定ID '{setting_id}'"
            )
        # 格式化 sub_themes 中的時間欄位
        if 'sub_themes' in result and result['sub_themes']:
            for sub_theme in result['sub_themes']:
                if 'created_at' in sub_theme and sub_theme['created_at']:
                    sub_theme['created_at'] = sub_theme['created_at'].isoformat() if hasattr(sub_theme['created_at'],
                                                                                             'isoformat') else \
                    sub_theme['created_at']
                if 'updated_at' in sub_theme and sub_theme['updated_at']:
                    sub_theme['updated_at'] = sub_theme['updated_at'].isoformat() if hasattr(sub_theme['updated_at'],
                                                                                             'isoformat') else \
                    sub_theme['updated_at']
        return format_datetime_fields(dict(result))

    @staticmethod
    async def get_school_year_theme_setting(conn, academic_year: int, academic_term: int, theme_code: str) -> Dict[
        str, Any]:
        """獲取特定學年期主題設定（通過 CODE，用於向後兼容，包含 sub_themes）"""
        result = await SchoolYearThemeSettingsDAO.get_school_year_theme_setting_by_code(
            conn, academic_year, academic_term, theme_code
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到學年 {academic_year} 學期 {academic_term} 的主題 {theme_code} 設定"
            )
        # 格式化 sub_themes 中的時間欄位
        if 'sub_themes' in result and result['sub_themes']:
            for sub_theme in result['sub_themes']:
                if 'created_at' in sub_theme and sub_theme['created_at']:
                    sub_theme['created_at'] = sub_theme['created_at'].isoformat() if hasattr(sub_theme['created_at'],
                                                                                             'isoformat') else \
                    sub_theme['created_at']
                if 'updated_at' in sub_theme and sub_theme['updated_at']:
                    sub_theme['updated_at'] = sub_theme['updated_at'].isoformat() if hasattr(sub_theme['updated_at'],
                                                                                             'isoformat') else \
                    sub_theme['updated_at']
        return format_datetime_fields(dict(result))

    @staticmethod
    async def get_school_year_theme_settings_by_year(conn, academic_year: int, academic_term: int) -> List[
        Dict[str, Any]]:
        """獲取某學年期的所有主題設定（包含 sub_themes）"""
        results = await SchoolYearThemeSettingsDAO.get_school_year_theme_settings_by_year(
            conn, academic_year, academic_term
        )
        formatted_results = []
        for row in results:
            formatted_row = format_datetime_fields(dict(row))
            # 格式化 sub_themes 中的時間欄位
            if 'sub_themes' in formatted_row and formatted_row['sub_themes']:
                for sub_theme in formatted_row['sub_themes']:
                    if 'created_at' in sub_theme and sub_theme['created_at']:
                        sub_theme['created_at'] = sub_theme['created_at'].isoformat() if hasattr(
                            sub_theme['created_at'], 'isoformat') else sub_theme['created_at']
                    if 'updated_at' in sub_theme and sub_theme['updated_at']:
                        sub_theme['updated_at'] = sub_theme['updated_at'].isoformat() if hasattr(
                            sub_theme['updated_at'], 'isoformat') else sub_theme['updated_at']
            formatted_results.append(formatted_row)
        return formatted_results

    @staticmethod
    async def update_school_year_theme_setting(
            conn,
            setting_id: str,
            data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新學年期主題設定（通過 ID）"""
        # 驗證 token
        SimpleTokenAuth.verify_token(data['token'], data['user_id'])

        result = await SchoolYearThemeSettingsDAO.update_school_year_theme_setting(
            conn,
            setting_id,
            data.get('fill_in_week_enabled'),
            data.get('scale_max'),
            data.get('select_most_relevant_sub_theme_enabled'),
            updated_by=data['user_id']
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到設定ID '{setting_id}'"
            )
        return format_datetime_fields(dict(result))

    @staticmethod
    async def update_school_year_theme_setting_by_code(
            conn,
            academic_year: int,
            academic_term: int,
            theme_code: str,
            data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新學年期主題設定（通過 CODE，用於向後兼容）"""
        # 驗證 token
        SimpleTokenAuth.verify_token(data['token'], data['user_id'])

        result = await SchoolYearThemeSettingsDAO.update_school_year_theme_setting_by_code(
            conn,
            academic_year,
            academic_term,
            theme_code,
            data.get('fill_in_week_enabled'),
            data.get('scale_max'),
            data.get('select_most_relevant_sub_theme_enabled'),
            updated_by=data['user_id']
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到學年 {academic_year} 學期 {academic_term} 的主題 {theme_code} 設定"
            )
        return format_datetime_fields(dict(result))

    @staticmethod
    async def delete_school_year_theme_setting(conn, setting_id: str, data: Dict[str, Any]) -> Dict[str, str]:
        """刪除學年期主題設定（通過 ID）"""
        # 驗證 token
        SimpleTokenAuth.verify_token(data['token'], data['user_id'])

        result = await SchoolYearThemeSettingsDAO.delete_school_year_theme_setting(conn, setting_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到設定ID '{setting_id}'"
            )
        theme_code = result.get('theme_code', '')
        return {
            "message": f"成功刪除設定ID '{setting_id}' (主題: {theme_code})"
        }

    @staticmethod
    async def delete_school_year_theme_setting_by_code(conn, academic_year: int, academic_term: int, theme_code: str,
                                               data: Dict[str, Any]) -> Dict[str, str]:
        """刪除學年期主題設定（通過 CODE，用於向後兼容）"""
        # 驗證 token
        SimpleTokenAuth.verify_token(data['token'], data['user_id'])

        result = await SchoolYearThemeSettingsDAO.delete_school_year_theme_setting_by_code(
            conn, academic_year, academic_term, theme_code
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到學年 {academic_year} 學期 {academic_term} 的主題 {theme_code} 設定"
            )
        return {
            "message": f"成功刪除學年 {academic_year} 學期 {academic_term} 的主題 {theme_code} 設定"
        }


class SchoolYearSubThemeSettingsBusiness:
    """學年期細項主題設定業務邏輯"""

    @staticmethod
    async def create_school_year_sub_theme_setting(conn, data: Dict[str, Any]) -> Dict[str, Any]:
        """創建學年期細項主題設定"""
        # 驗證 token
        SimpleTokenAuth.verify_token(data['token'], data['user_id'])

        try:
            await SchoolYearSubThemeSettingsDAO.create_school_year_sub_theme_setting(
                conn,
                data['academic_year'],
                data['academic_term'],
                data['theme_code'],
                data['sub_theme_code'],
                data.get('enabled', True),
                created_by=data['user_id']
            )
            # 獲取完整資訊（包含 sub_theme_name）
            result = await SchoolYearSubThemeSettingsDAO.get_school_year_sub_theme_setting_by_code(
                conn, data['academic_year'], data['academic_term'], data['theme_code'], data['sub_theme_code']
            )
            if not result:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="創建後無法查詢到記錄")
            return format_datetime_fields(dict(result))
        except HTTPException:
            raise
        except Exception as e:
            if 'unique constraint' in str(e).lower() or 'duplicate' in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"學年 {data['academic_year']} 學期 {data['academic_term']} 的主題 {data['theme_code']} 細項 {data['sub_theme_code']} 設定已存在"
                )
            raise

    @staticmethod
    async def get_school_year_sub_theme_setting_by_id(conn, setting_id: str) -> Dict[str, Any]:
        """獲取特定學年期細項主題設定（通過 ID）"""
        result = await SchoolYearSubThemeSettingsDAO.get_school_year_sub_theme_setting_by_id(conn, setting_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到設定ID '{setting_id}'"
            )
        return format_datetime_fields(dict(result))

    @staticmethod
    async def get_school_year_sub_theme_settings_by_theme(
            conn,
            academic_year: int,
            academic_term: int,
            theme_code: str
    ) -> List[Dict[str, Any]]:
        """獲取某學年期某主題的所有細項設定"""
        results = await SchoolYearSubThemeSettingsDAO.get_school_year_sub_theme_settings_by_year_and_theme(
            conn, academic_year, academic_term, theme_code
        )
        return [format_datetime_fields(dict(row)) for row in results]

    @staticmethod
    async def update_school_year_sub_theme_setting(
            conn,
            setting_id: str,
            data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新學年期細項主題設定（通過 ID）
        
        如果記錄不存在，會自動創建
        """
        # 驗證 token
        SimpleTokenAuth.verify_token(data['token'], data['user_id'])

        result = await SchoolYearSubThemeSettingsDAO.update_school_year_sub_theme_setting(
            conn,
            setting_id,
            data['enabled'],
            updated_by=data['user_id'],
            academic_year=data.get('academic_year'),
            academic_term=data.get('academic_term')
        )
        if not result:
            # 提供更詳細的錯誤訊息
            if data.get('academic_year') and data.get('academic_term'):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"找不到設定ID '{setting_id}'，且該 ID 也不是有效的 sub_theme_id，無法自動創建記錄"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"找不到設定ID '{setting_id}'。如需自動創建記錄，請提供 academic_year 和 academic_term 參數"
                )
        return format_datetime_fields(dict(result))

    @staticmethod
    async def update_school_year_sub_theme_setting_by_code(
            conn,
            academic_year: int,
            academic_term: int,
            theme_code: str,
            sub_theme_code: str,
            data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新學年期細項主題設定（通過 CODE，用於向後兼容）
        
        如果記錄不存在，會自動創建
        """
        # 驗證 token
        SimpleTokenAuth.verify_token(data['token'], data['user_id'])

        result = await SchoolYearSubThemeSettingsDAO.update_school_year_sub_theme_setting_by_code(
            conn,
            academic_year,
            academic_term,
            theme_code,
            sub_theme_code,
            data['enabled'],
            updated_by=data['user_id']
        )
        if not result:
            # 如果結果為 None，可能是細項主題不存在
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到主題 {theme_code} 的細項 {sub_theme_code}，請先創建細項主題"
            )
        return format_datetime_fields(dict(result))

    @staticmethod
    async def delete_school_year_sub_theme_setting(
            conn,
            setting_id: str,
            data: Dict[str, Any]
    ) -> Dict[str, str]:
        """刪除學年期細項主題設定（通過 ID）"""
        # 驗證 token
        SimpleTokenAuth.verify_token(data['token'], data['user_id'])

        result = await SchoolYearSubThemeSettingsDAO.delete_school_year_sub_theme_setting(conn, setting_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到設定ID '{setting_id}'"
            )
        return {
            "message": f"成功刪除設定ID '{setting_id}'"
        }

    @staticmethod
    async def delete_school_year_sub_theme_setting_by_code(
            conn,
            academic_year: int,
            academic_term: int,
            theme_code: str,
            sub_theme_code: str,
            data: Dict[str, Any]
    ) -> Dict[str, str]:
        """刪除學年期細項主題設定（通過 CODE，用於向後兼容）"""
        # 驗證 token
        SimpleTokenAuth.verify_token(data['token'], data['user_id'])

        result = await SchoolYearSubThemeSettingsDAO.delete_school_year_sub_theme_setting_by_code(
            conn, academic_year, academic_term, theme_code, sub_theme_code
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到學年 {academic_year} 學期 {academic_term} 的主題 {theme_code} 細項 {sub_theme_code} 設定"
            )
        return {
            "message": f"成功刪除學年 {academic_year} 學期 {academic_term} 的主題 {theme_code} 細項 {sub_theme_code} 設定"
        }


class SchoolYearThemeSettingsCopyBusiness:
    """學年期主題設定複製業務邏輯"""

    @staticmethod
    async def copy_school_year_theme_settings(conn, data: Dict[str, Any]) -> Dict[str, Any]:
        """複製學年期主題設定"""
        # 驗證 token
        SimpleTokenAuth.verify_token(data['token'], data['user_id'])

        try:
            result = await SchoolYearThemeSettingsDAO.copy_school_year_theme_settings(
                conn,
                data['source_academic_year'],
                data['source_academic_term'],
                data['target_academic_year'],
                data['target_academic_term'],
                created_by=data['user_id']
            )
            
            # 組合回應訊息
            deleted_info = ""
            if result.get('deleted_themes_count', 0) > 0 or result.get('deleted_sub_themes_count', 0) > 0:
                deleted_info = f"（已刪除舊設定：{result.get('deleted_themes_count', 0)} 個主題、{result.get('deleted_sub_themes_count', 0)} 個子主題）"
            
            return {
                "message": f"成功從學年 {data['source_academic_year']} 學期 {data['source_academic_term']} 複製到學年 {data['target_academic_year']} 學期 {data['target_academic_term']}{deleted_info}",
                "themes_count": result['themes_count'],
                "sub_themes_count": result['sub_themes_count'],
                "deleted_themes_count": result.get('deleted_themes_count', 0),
                "deleted_sub_themes_count": result.get('deleted_sub_themes_count', 0)
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"複製學年期主題設定失敗: {str(e)}"
            )
