from typing import List, Optional
import json
from datetime import datetime
import uuid
from .db import Database
from .theme_dao import SubThemeDAO, ThemeDAO


class SchoolYearThemeSettingsDAO:
    """學年期主題設定數據訪問對象"""

    @staticmethod
    async def create_school_year_theme_setting(conn, academic_year: int, academic_term: int, theme_code: str,
                                             fill_in_week_enabled: bool, scale_max: int = 3,
                                             select_most_relevant_sub_theme_enabled: bool = False,
                                             created_by: Optional[str] = None):
        """創建學年期主題設定，並自動創建該主題的所有 sub_themes 設定（預設啟用）"""
        # 通過 theme_code 獲取 theme_id
        theme = await ThemeDAO.get_theme_by_code(conn, theme_code)
        if not theme:
            raise ValueError(f"主題代碼 '{theme_code}' 不存在")
        
        setting_id = str(uuid.uuid4())
        fill_week_char = 'Y' if fill_in_week_enabled else 'N'
        select_most_relevant_char = 'Y' if select_most_relevant_sub_theme_enabled else 'N'
        current_time = datetime.now()
        
        query = """
        INSERT INTO academic_year_coures_themes_setting 
        (id, academic_year, academic_term, coures_themes_id, fill_in_week_enabled, scale_max, 
         select_most_relevant_sub_theme_enabled, created_by, updated_by, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """
        await Database.execute(conn, query, setting_id, academic_year, academic_term, theme['id'], 
                              fill_week_char, scale_max, select_most_relevant_char, 
                              created_by, created_by, current_time, current_time)
        
        # Oracle 不支持 RETURNING，需要再次查詢
        result = await SchoolYearThemeSettingsDAO.get_school_year_theme_setting_by_code(conn, academic_year, academic_term, theme_code)
        if result:
            result['fill_in_week_enabled'] = fill_in_week_enabled
            
            # 查詢該主題的所有 sub_themes
            sub_themes = await SubThemeDAO.get_sub_themes_by_theme_id(conn, theme['id'])
            
            # 批量插入所有 sub_themes 到 academic_year_coures_sub_theme_settings，預設啟用
            if sub_themes:
                for sub_theme in sub_themes:
                    try:
                        sub_setting_id = str(uuid.uuid4())
                        sub_theme_query = """
                        INSERT INTO academic_year_coures_sub_theme_settings 
                        (id, academic_year, academic_term, coures_sub_themes_id, enabled, 
                         created_by, updated_by, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, 'Y', $5, $6, $7, $8)
                        """
                        await Database.execute(conn, sub_theme_query, sub_setting_id, academic_year, academic_term, 
                                             sub_theme['id'], created_by, created_by, current_time, current_time)
                    except Exception as e:
                        # 如果已存在（唯一約束錯誤），則跳過
                        error_str = str(e).lower()
                        if 'unique constraint' in error_str or 'duplicate' in error_str or 'ora-00001' in error_str:
                            continue
                        raise
        
        return result

    @staticmethod
    async def get_school_year_theme_setting_by_id(conn, setting_id: str):
        """根據設定ID獲取學年期主題設定"""
        query = """
        SELECT syts.id, syts.academic_year, syts.academic_term, syts.coures_themes_id, 
               t.id as theme_id, t.theme_code, t.theme_name, 
               syts.fill_in_week_enabled, syts.scale_max, syts.select_most_relevant_sub_theme_enabled,
               syts.created_at, syts.updated_at
        FROM academic_year_coures_themes_setting syts
        JOIN coures_themes t ON syts.coures_themes_id = t.id
        WHERE syts.id = $1
        """
        theme_result = await Database.fetchrow(conn, query, setting_id)
        if not theme_result:
            return None
        
        theme_dict = dict(theme_result)
        theme_dict['fill_in_week_enabled'] = theme_dict['fill_in_week_enabled'] == 'Y'
        theme_dict['select_most_relevant_sub_theme_enabled'] = theme_dict.get('select_most_relevant_sub_theme_enabled', 'N') == 'Y'
        
        # 使用 LEFT JOIN 獲取該主題的所有 sub_themes
        sub_themes_query = """
        SELECT 
            st.id as sub_theme_id,
            st.sub_theme_code,
            st.sub_theme_name,
            st.sub_theme_english_name,
            st.sub_theme_content,
            st.sub_theme_english_content,
            COALESCE(systs.enabled, 'N') as enabled
        FROM coures_sub_themes st
        LEFT JOIN academic_year_coures_sub_theme_settings systs 
            ON st.id = systs.coures_sub_themes_id
            AND systs.academic_year = $1 
            AND systs.academic_term = $2
        WHERE st.coures_themes_id = $3
        ORDER BY st.sub_theme_code
        """
        sub_themes_results = await Database.fetch(conn, sub_themes_query, theme_dict['academic_year'], theme_dict['academic_term'], theme_dict['coures_themes_id'])
        
        sub_themes_list = []
        for sub_theme_row in sub_themes_results:
            sub_theme_dict = dict(sub_theme_row)
            sub_theme_dict['enabled'] = sub_theme_dict['enabled'] == 'Y'
            sub_themes_list.append(sub_theme_dict)
        
        theme_dict['sub_themes'] = sub_themes_list
        return theme_dict

    @staticmethod
    async def get_school_year_theme_setting_by_code(conn, academic_year: int, academic_term: int, theme_code: str):
        """獲取特定學年期主題設定（通過 theme_code），包含所有 sub_themes"""
        # 先獲取主題基本資訊
        theme_query = """
        SELECT syts.id, syts.academic_year, syts.academic_term, syts.coures_themes_id, 
               t.id as theme_id, t.theme_code, t.theme_name, 
               syts.fill_in_week_enabled, syts.scale_max, syts.select_most_relevant_sub_theme_enabled,
               syts.created_at, syts.updated_at
        FROM academic_year_coures_themes_setting syts
        JOIN coures_themes t ON syts.coures_themes_id = t.id
        WHERE syts.academic_year = $1 AND syts.academic_term = $2 AND t.theme_code = $3
        """
        theme_result = await Database.fetchrow(conn, theme_query, academic_year, academic_term, theme_code)
        if not theme_result:
            return None
        
        theme_dict = dict(theme_result)
        theme_dict['fill_in_week_enabled'] = theme_dict['fill_in_week_enabled'] == 'Y'
        theme_dict['select_most_relevant_sub_theme_enabled'] = theme_dict.get('select_most_relevant_sub_theme_enabled', 'N') == 'Y'
        
        # 使用 LEFT JOIN 獲取該主題的所有 sub_themes
        sub_themes_query = """
        SELECT 
            st.id as sub_theme_id,
            st.sub_theme_code,
            st.sub_theme_name,
            st.sub_theme_english_name,
            st.sub_theme_content,
            st.sub_theme_english_content,
            COALESCE(systs.enabled, 'N') as enabled
        FROM coures_sub_themes st
        LEFT JOIN academic_year_coures_sub_theme_settings systs 
            ON st.id = systs.coures_sub_themes_id
            AND systs.academic_year = $1 
            AND systs.academic_term = $2
        WHERE st.coures_themes_id = $3
        ORDER BY st.sub_theme_code
        """
        sub_themes_results = await Database.fetch(conn, sub_themes_query, academic_year, academic_term, theme_dict['coures_themes_id'])
        
        sub_themes_list = []
        for sub_theme_row in sub_themes_results:
            sub_theme_dict = dict(sub_theme_row)
            sub_theme_dict['enabled'] = sub_theme_dict['enabled'] == 'Y'
            sub_themes_list.append(sub_theme_dict)
        
        theme_dict['sub_themes'] = sub_themes_list
        return theme_dict

    @staticmethod
    async def get_school_year_theme_settings_by_year(conn, academic_year: int, academic_term: int) -> List:
        """獲取某學年期的所有主題設定，包含所有 sub_themes（使用 LEFT JOIN）"""
        # 先獲取所有主題基本資訊
        themes_query = """
        SELECT syts.id, syts.academic_year, syts.academic_term, syts.coures_themes_id, 
               t.id as theme_id, t.theme_code, t.theme_name, 
               syts.fill_in_week_enabled, syts.scale_max, syts.select_most_relevant_sub_theme_enabled,
               syts.created_at, syts.updated_at
        FROM academic_year_coures_themes_setting syts
        JOIN coures_themes t ON syts.coures_themes_id = t.id
        WHERE syts.academic_year = $1 AND syts.academic_term = $2
        ORDER BY t.theme_code
        """
        themes_results = await Database.fetch(conn, themes_query, academic_year, academic_term)
        
        results_list = []
        for theme_row in themes_results:
            theme_dict = dict(theme_row)
            theme_dict['fill_in_week_enabled'] = theme_dict['fill_in_week_enabled'] == 'Y'
            theme_dict['select_most_relevant_sub_theme_enabled'] = theme_dict.get('select_most_relevant_sub_theme_enabled', 'N') == 'Y'
            coures_themes_id = theme_dict['coures_themes_id']
            
            # 使用 LEFT JOIN 獲取該主題的所有 sub_themes
            sub_themes_query = """
            SELECT 
                st.id as sub_theme_id,
                st.sub_theme_code,
                st.sub_theme_name,
                st.sub_theme_english_name,
                st.sub_theme_content,
                st.sub_theme_english_content,
                COALESCE(systs.enabled, 'N') as enabled
            FROM coures_sub_themes st
            LEFT JOIN academic_year_coures_sub_theme_settings systs 
                ON st.id = systs.coures_sub_themes_id
                AND systs.academic_year = $1 
                AND systs.academic_term = $2
            WHERE st.coures_themes_id = $3
            ORDER BY st.sub_theme_code
            """
            sub_themes_results = await Database.fetch(conn, sub_themes_query, academic_year, academic_term, coures_themes_id)
            
            sub_themes_list = []
            for sub_theme_row in sub_themes_results:
                sub_theme_dict = dict(sub_theme_row)
                sub_theme_dict['enabled'] = sub_theme_dict['enabled'] == 'Y'
                sub_themes_list.append(sub_theme_dict)
            
            theme_dict['sub_themes'] = sub_themes_list
            results_list.append(theme_dict)
        
        return results_list

    @staticmethod
    async def update_school_year_theme_setting(conn, setting_id: str,
                                             fill_in_week_enabled: Optional[bool] = None, 
                                             scale_max: Optional[int] = None,
                                             select_most_relevant_sub_theme_enabled: Optional[bool] = None,
                                             updated_by: Optional[str] = None):
        """更新學年期主題設定（通過 ID）"""
        update_fields = []
        values = []
        param_idx = 1

        if fill_in_week_enabled is not None:
            fill_week_char = 'Y' if fill_in_week_enabled else 'N'
            update_fields.append(f"fill_in_week_enabled = ${param_idx}")
            values.append(fill_week_char)
            param_idx += 1

        if scale_max is not None:
            update_fields.append(f"scale_max = ${param_idx}")
            values.append(scale_max)
            param_idx += 1

        if select_most_relevant_sub_theme_enabled is not None:
            select_most_relevant_char = 'Y' if select_most_relevant_sub_theme_enabled else 'N'
            update_fields.append(f"select_most_relevant_sub_theme_enabled = ${param_idx}")
            values.append(select_most_relevant_char)
            param_idx += 1

        if not update_fields:
            setting = await SchoolYearThemeSettingsDAO.get_school_year_theme_setting_by_id(conn, setting_id)
            if setting:
                theme_code = setting.get('theme_code')
                return await SchoolYearThemeSettingsDAO.get_school_year_theme_setting_by_code(
                    conn, setting['academic_year'], setting['academic_term'], theme_code)
            return None

        if updated_by is not None:
            update_fields.append(f"updated_by = ${param_idx}")
            values.append(updated_by)
            param_idx += 1

        # Oracle 需要手動更新 updated_at
        update_fields.append(f"updated_at = ${param_idx}")
        values.append(datetime.now())
        param_idx += 1
        
        values.append(setting_id)
        
        query = f"""
        UPDATE academic_year_coures_themes_setting 
        SET {', '.join(update_fields)}
        WHERE id = ${param_idx}
        """
        
        await Database.execute(conn, query, *values)
        setting = await SchoolYearThemeSettingsDAO.get_school_year_theme_setting_by_id(conn, setting_id)
        if setting:
            theme_code = setting.get('theme_code')
            return await SchoolYearThemeSettingsDAO.get_school_year_theme_setting_by_code(
                conn, setting['academic_year'], setting['academic_term'], theme_code)
        return None

    @staticmethod
    async def update_school_year_theme_setting_by_code(conn, academic_year: int, academic_term: int, theme_code: str,
                                             fill_in_week_enabled: Optional[bool] = None, 
                                             scale_max: Optional[int] = None,
                                             select_most_relevant_sub_theme_enabled: Optional[bool] = None,
                                             updated_by: Optional[str] = None):
        """更新學年期主題設定（通過 CODE，用於向後兼容）"""
        setting = await SchoolYearThemeSettingsDAO.get_school_year_theme_setting_by_code(conn, academic_year, academic_term, theme_code)
        if not setting:
            return None
        return await SchoolYearThemeSettingsDAO.update_school_year_theme_setting(
            conn, setting['id'], fill_in_week_enabled, scale_max, select_most_relevant_sub_theme_enabled, updated_by)

    @staticmethod
    async def delete_school_year_theme_setting(conn, setting_id: str):
        """刪除學年期主題設定（通過 ID，會先刪除相關的子主題設定）"""
        setting = await SchoolYearThemeSettingsDAO.get_school_year_theme_setting_by_id(conn, setting_id)
        if setting:
            # 先刪除所有相關的子主題設定
            sub_theme_query = """
            DELETE FROM academic_year_coures_sub_theme_settings systs
            WHERE systs.academic_year = $1 
              AND systs.academic_term = $2
              AND EXISTS (
                  SELECT 1 FROM coures_sub_themes st
                  WHERE st.id = systs.coures_sub_themes_id
                    AND st.coures_themes_id = $3
              )
            """
            await Database.execute(conn, sub_theme_query, setting['academic_year'], setting['academic_term'], setting['coures_themes_id'])
            
            # 再刪除主題設定
            query = "DELETE FROM academic_year_coures_themes_setting WHERE id = $1"
            await Database.execute(conn, query, setting_id)
        return setting

    @staticmethod
    async def delete_school_year_theme_setting_by_code(conn, academic_year: int, academic_term: int, theme_code: str):
        """刪除學年期主題設定（通過 CODE，用於向後兼容）"""
        setting = await SchoolYearThemeSettingsDAO.get_school_year_theme_setting_by_code(conn, academic_year, academic_term, theme_code)
        if setting:
            return await SchoolYearThemeSettingsDAO.delete_school_year_theme_setting(conn, setting['id'])
        return None

    @staticmethod
    async def copy_school_year_theme_settings(conn, source_academic_year: int, source_academic_term: int,
                                             target_academic_year: int, target_academic_term: int,
                                             created_by: Optional[str] = None) -> dict:
        """複製學年期主題設定和子主題設定到目標學年期
        
        會複製所有主題設定，並為每個主題的所有子主題創建設定記錄。
        子主題的 enabled 狀態會從來源學年期取得，如果來源沒有設定則預設為 'N'。
        如果目標學年期已有設定，會先刪除舊設定再複製。
        """
        # 檢查來源學年期是否存在主題設定
        check_source_query = """
        SELECT COUNT(*) FROM academic_year_coures_themes_setting 
        WHERE academic_year = $1 AND academic_term = $2
        """
        source_count = await Database.fetchval(conn, check_source_query, source_academic_year, source_academic_term)
        if not source_count or source_count == 0:
            raise ValueError(f"來源學年 {source_academic_year} 學期 {source_academic_term} 不存在主題設定")
        
        # 檢查目標學年期是否已存在設定，如果有則先刪除
        check_target_query = """
        SELECT COUNT(*) FROM academic_year_coures_themes_setting 
        WHERE academic_year = $1 AND academic_term = $2
        """
        target_count = await Database.fetchval(conn, check_target_query, target_academic_year, target_academic_term)
        
        deleted_themes_count = 0
        deleted_sub_themes_count = 0
        
        if target_count and target_count > 0:
            # 先刪除目標學年期的子主題設定
            delete_sub_themes_query = """
            DELETE FROM academic_year_coures_sub_theme_settings 
            WHERE academic_year = $1 AND academic_term = $2
            """
            # 先計算要刪除的數量
            count_sub_themes_query = """
            SELECT COUNT(*) FROM academic_year_coures_sub_theme_settings 
            WHERE academic_year = $1 AND academic_term = $2
            """
            deleted_sub_themes_count = await Database.fetchval(conn, count_sub_themes_query, target_academic_year, target_academic_term) or 0
            await Database.execute(conn, delete_sub_themes_query, target_academic_year, target_academic_term)
            
            # 再刪除目標學年期的主題設定
            delete_themes_query = """
            DELETE FROM academic_year_coures_themes_setting 
            WHERE academic_year = $1 AND academic_term = $2
            """
            deleted_themes_count = target_count
            await Database.execute(conn, delete_themes_query, target_academic_year, target_academic_term)
        
        # 查詢來源學年期的所有主題設定
        themes_query = """
        SELECT syts.coures_themes_id, syts.fill_in_week_enabled, syts.scale_max, syts.select_most_relevant_sub_theme_enabled
        FROM academic_year_coures_themes_setting syts
        WHERE syts.academic_year = $1 AND syts.academic_term = $2
        """
        themes_results = await Database.fetch(conn, themes_query, source_academic_year, source_academic_term)
        
        current_time = datetime.now()
        themes_count = 0
        sub_themes_count = 0
        
        # 為每個主題複製設定，並複製其所有子主題設定
        for theme_row in themes_results:
            theme_dict = dict(theme_row)
            coures_themes_id = theme_dict['coures_themes_id']
            
            # 插入主題設定
            fill_week_char = theme_dict['fill_in_week_enabled'] if isinstance(theme_dict.get('fill_in_week_enabled'), str) else ('Y' if theme_dict.get('fill_in_week_enabled') else 'N')
            select_most_relevant_char = theme_dict.get('select_most_relevant_sub_theme_enabled', 'N') if isinstance(theme_dict.get('select_most_relevant_sub_theme_enabled'), str) else ('Y' if theme_dict.get('select_most_relevant_sub_theme_enabled') else 'N')
            setting_id = str(uuid.uuid4())
            insert_theme_query = """
            INSERT INTO academic_year_coures_themes_setting 
            (id, academic_year, academic_term, coures_themes_id, fill_in_week_enabled, scale_max, 
             select_most_relevant_sub_theme_enabled, created_by, updated_by, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """
            await Database.execute(conn, insert_theme_query, setting_id, target_academic_year, target_academic_term,
                                 coures_themes_id, fill_week_char, theme_dict['scale_max'], select_most_relevant_char,
                                 created_by, created_by, current_time, current_time)
            themes_count += 1
            
            # 查詢該主題的所有子主題，並取得來源學年期的 enabled 狀態
            sub_themes_query = """
            SELECT 
                st.id as sub_theme_id,
                COALESCE(systs.enabled, 'N') as enabled
            FROM coures_sub_themes st
            LEFT JOIN academic_year_coures_sub_theme_settings systs 
                ON st.id = systs.coures_sub_themes_id
                AND systs.academic_year = $1 
                AND systs.academic_term = $2
            WHERE st.coures_themes_id = $3
            """
            sub_themes_results = await Database.fetch(conn, sub_themes_query, 
                                                      source_academic_year, source_academic_term, coures_themes_id)
            
            # 為每個子主題創建設定記錄
            for sub_theme_row in sub_themes_results:
                sub_theme_dict = dict(sub_theme_row)
                enabled_char = sub_theme_dict['enabled'] if isinstance(sub_theme_dict.get('enabled'), str) else ('Y' if sub_theme_dict.get('enabled') else 'N')
                sub_setting_id = str(uuid.uuid4())
                insert_sub_theme_query = """
                INSERT INTO academic_year_coures_sub_theme_settings 
                (id, academic_year, academic_term, coures_sub_themes_id, enabled, 
                 created_by, updated_by, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """
                try:
                    await Database.execute(conn, insert_sub_theme_query, sub_setting_id, target_academic_year, target_academic_term,
                                          sub_theme_dict['sub_theme_id'], enabled_char, created_by, created_by, current_time, current_time)
                    sub_themes_count += 1
                except Exception as e:
                    # 如果已存在（唯一約束錯誤），則跳過
                    error_str = str(e).lower()
                    if 'unique constraint' in error_str or 'duplicate' in error_str or 'ora-00001' in error_str:
                        continue
                    raise
        
        return {
            'themes_count': themes_count,
            'sub_themes_count': sub_themes_count,
            'deleted_themes_count': deleted_themes_count,
            'deleted_sub_themes_count': deleted_sub_themes_count
        }


class SchoolYearSubThemeSettingsDAO:
    """學年期細項主題設定數據訪問對象"""

    @staticmethod
    async def create_school_year_sub_theme_setting(conn, academic_year: int, academic_term: int, theme_code: str,
                                                 sub_theme_code: str, enabled: bool,
                                                 created_by: Optional[str] = None):
        """創建學年期細項主題設定
        
        注意：theme_code 用於驗證 sub_theme_code 是否屬於該 theme
        """
        # 驗證 sub_theme_code 是否屬於該 theme_code
        sub_theme = await SubThemeDAO.get_sub_theme_by_code(conn, theme_code, sub_theme_code)
        if not sub_theme:
            raise ValueError(f"sub_theme_code '{sub_theme_code}' 不屬於 theme_code '{theme_code}'")
        
        setting_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        query = """
        INSERT INTO academic_year_coures_sub_theme_settings 
        (id, academic_year, academic_term, coures_sub_themes_id, enabled, 
         created_by, updated_by, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        enabled_char = 'Y' if enabled else 'N'
        await Database.execute(conn, query, setting_id, academic_year, academic_term, 
                              sub_theme['id'], enabled_char, created_by, created_by, current_time, current_time)
        
        # Oracle 不支持 RETURNING，需要再次查詢
        result = await SchoolYearSubThemeSettingsDAO.get_school_year_sub_theme_setting_by_code(
            conn, academic_year, academic_term, theme_code, sub_theme_code)
        return result

    @staticmethod
    async def get_school_year_sub_theme_setting_by_id(conn, setting_id: str):
        """獲取特定學年期細項主題設定（通過 ID）"""
        query = """
        SELECT systs.id, systs.academic_year, systs.academic_term, systs.coures_sub_themes_id,
               st.id as sub_theme_id, st.coures_themes_id, t.theme_code, st.sub_theme_code,
               st.sub_theme_name, systs.enabled, systs.created_at, systs.updated_at
        FROM academic_year_coures_sub_theme_settings systs
        JOIN coures_sub_themes st ON systs.coures_sub_themes_id = st.id
        JOIN coures_themes t ON st.coures_themes_id = t.id
        WHERE systs.id = $1
        """
        result = await Database.fetchrow(conn, query, setting_id)
        if result:
            result = dict(result)
            result['enabled'] = result['enabled'] == 'Y'
        return result

    @staticmethod
    async def get_school_year_sub_theme_setting_by_code(conn, academic_year: int, academic_term: int, 
                                                theme_code: str, sub_theme_code: str):
        """獲取特定學年期細項主題設定（通過 CODE）"""
        query = """
        SELECT systs.id, systs.academic_year, systs.academic_term, systs.coures_sub_themes_id,
               st.id as sub_theme_id, st.coures_themes_id, t.theme_code, systs.coures_sub_themes_id as sub_theme_code_check,
               st.sub_theme_code, st.sub_theme_name, systs.enabled, systs.created_at, systs.updated_at
        FROM academic_year_coures_sub_theme_settings systs
        JOIN coures_sub_themes st ON systs.coures_sub_themes_id = st.id
        JOIN coures_themes t ON st.coures_themes_id = t.id
        WHERE systs.academic_year = $1 AND systs.academic_term = $2 
          AND t.theme_code = $3 AND st.sub_theme_code = $4
        """
        result = await Database.fetchrow(conn, query, academic_year, academic_term, theme_code, sub_theme_code)
        if result:
            result = dict(result)
            result['enabled'] = result['enabled'] == 'Y'
        return result

    @staticmethod
    async def get_school_year_sub_theme_settings_by_year_and_theme(conn, academic_year: int, academic_term: int, theme_code: str) -> List:
        """獲取某學年期某主題的所有細項設定
        
        回傳該主題的所有細項（不論是否啟用），並標記 enabled 狀態
        """
        # 先獲取 theme_id
        theme = await ThemeDAO.get_theme_by_code(conn, theme_code)
        if not theme:
            return []
        
        query = """
        SELECT 
            st.id as sub_theme_id,
            st.coures_themes_id,
            t.theme_code,
            st.sub_theme_code,
            st.sub_theme_name,
            COALESCE(systs.enabled, 'N') as enabled,
            systs.created_at,
            systs.updated_at
        FROM coures_sub_themes st
        JOIN coures_themes t ON st.coures_themes_id = t.id
        LEFT JOIN academic_year_coures_sub_theme_settings systs 
            ON st.id = systs.coures_sub_themes_id
            AND systs.academic_year = $1 
            AND systs.academic_term = $2
        WHERE st.coures_themes_id = $3
        ORDER BY st.sub_theme_code
        """
        results = await Database.fetch(conn, query, academic_year, academic_term, theme['id'])
        results_list = []
        for result in results:
            result_dict = dict(result)
            # 添加 academic_year 和 academic_term
            result_dict['academic_year'] = academic_year
            result_dict['academic_term'] = academic_term
            result_dict['enabled'] = result_dict['enabled'] == 'Y'
            results_list.append(result_dict)
        return results_list

    @staticmethod
    async def get_school_year_sub_theme_settings_by_year(conn, academic_year: int, academic_term: int) -> List:
        """獲取某學年期的所有細項設定"""
        query = """
        SELECT systs.id, systs.academic_year, systs.academic_term, systs.coures_sub_themes_id,
               st.id as sub_theme_id, st.coures_themes_id, t.theme_code, systs.coures_sub_themes_id as sub_theme_code_check,
               st.sub_theme_code, st.sub_theme_name, systs.enabled, systs.created_at, systs.updated_at
        FROM academic_year_coures_sub_theme_settings systs
        JOIN coures_sub_themes st ON systs.coures_sub_themes_id = st.id
        JOIN coures_themes t ON st.coures_themes_id = t.id
        WHERE systs.academic_year = $1 AND systs.academic_term = $2
        ORDER BY t.theme_code, st.sub_theme_code
        """
        results = await Database.fetch(conn, query, academic_year, academic_term)
        results_list = []
        for result in results:
            result_dict = dict(result)
            result_dict['enabled'] = result_dict['enabled'] == 'Y'
            results_list.append(result_dict)
        return results_list

    @staticmethod
    async def update_school_year_sub_theme_setting(conn, setting_id: str, enabled: bool,
                                                 updated_by: Optional[str] = None,
                                                 academic_year: Optional[int] = None,
                                                 academic_term: Optional[int] = None):
        """更新學年期細項主題設定（通過 ID）
        
        如果 setting_id 對應的記錄不存在，且提供了 academic_year 和 academic_term，
        則會嘗試將 setting_id 視為 sub_theme_id 並自動創建或更新記錄。
        """
        current_time = datetime.now()
        enabled_char = 'Y' if enabled else 'N'
        
        # 先檢查記錄是否存在（通過 setting_id）
        existing = await SchoolYearSubThemeSettingsDAO.get_school_year_sub_theme_setting_by_id(conn, setting_id)
        
        if existing:
            # 記錄存在，執行更新
            update_query = """
            UPDATE academic_year_coures_sub_theme_settings 
            SET enabled = $1, updated_by = $2, updated_at = $3
            WHERE id = $4
            """
            await Database.execute(conn, update_query, enabled_char, updated_by, current_time, setting_id)
            
            # 查詢並返回結果
            result = await SchoolYearSubThemeSettingsDAO.get_school_year_sub_theme_setting_by_id(conn, setting_id)
            return result
        else:
            # 記錄不存在，嘗試自動創建或更新
            if academic_year is None or academic_term is None:
                # 沒有提供學年期資訊，無法創建
                return None
            
            # 將 setting_id 視為 sub_theme_id，查詢對應的 sub_theme
            sub_theme_query = """
            SELECT st.id, st.sub_theme_code, t.theme_code
            FROM coures_sub_themes st
            JOIN coures_themes t ON st.coures_themes_id = t.id
            WHERE st.id = $1
            """
            sub_theme = await Database.fetchrow(conn, sub_theme_query, setting_id)
            
            if not sub_theme:
                # 找不到對應的 sub_theme，無法創建
                return None
            
            # 先檢查該學年期 + sub_theme 的組合是否已經存在
            existing_by_sub_theme_query = """
            SELECT id FROM academic_year_coures_sub_theme_settings
            WHERE academic_year = $1 AND academic_term = $2 AND coures_sub_themes_id = $3
            """
            existing_setting = await Database.fetchrow(conn, existing_by_sub_theme_query, 
                                                       academic_year, academic_term, setting_id)
            
            if existing_setting:
                # 該學年期的設定已存在，執行更新
                update_query = """
                UPDATE academic_year_coures_sub_theme_settings 
                SET enabled = $1, updated_by = $2, updated_at = $3
                WHERE id = $4
                """
                await Database.execute(conn, update_query, enabled_char, updated_by, 
                                       current_time, existing_setting['id'])
                
                # 查詢並返回結果
                result = await SchoolYearSubThemeSettingsDAO.get_school_year_sub_theme_setting_by_id(
                    conn, existing_setting['id'])
                return result
            else:
                # 創建新記錄
                new_setting_id = str(uuid.uuid4())
                insert_query = """
                INSERT INTO academic_year_coures_sub_theme_settings 
                (id, academic_year, academic_term, coures_sub_themes_id, enabled, 
                 created_by, updated_by, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """
                await Database.execute(conn, insert_query, new_setting_id, academic_year, academic_term,
                                     setting_id, enabled_char, updated_by, updated_by, current_time, current_time)
                
                # 查詢並返回結果
                result = await SchoolYearSubThemeSettingsDAO.get_school_year_sub_theme_setting_by_id(
                    conn, new_setting_id)
                return result

    @staticmethod
    async def update_school_year_sub_theme_setting_by_code(conn, academic_year: int, academic_term: int, theme_code: str,
                                                 sub_theme_code: str, enabled: bool,
                                                 updated_by: Optional[str] = None):
        """更新學年期細項主題設定（通過 CODE，用於向後兼容）
        
        如果記錄不存在，會自動創建
        """
        current_time = datetime.now()
        
        # Oracle 不支持 ON CONFLICT，需要先查詢是否存在
        existing = await SchoolYearSubThemeSettingsDAO.get_school_year_sub_theme_setting_by_code(
            conn, academic_year, academic_term, theme_code, sub_theme_code)
        
        if existing:
            return await SchoolYearSubThemeSettingsDAO.update_school_year_sub_theme_setting(
                conn, existing['id'], enabled, updated_by)
        else:
            # 驗證 sub_theme_code 是否屬於該 theme_code
            sub_theme = await SubThemeDAO.get_sub_theme_by_code(conn, theme_code, sub_theme_code)
            if not sub_theme:
                raise ValueError(f"sub_theme_code '{sub_theme_code}' 不屬於 theme_code '{theme_code}'")
            
            # 插入新記錄
            setting_id = str(uuid.uuid4())
            insert_query = """
            INSERT INTO academic_year_coures_sub_theme_settings 
            (id, academic_year, academic_term, coures_sub_themes_id, enabled, 
             created_by, updated_by, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """
            enabled_char = 'Y' if enabled else 'N'
            await Database.execute(conn, insert_query, setting_id, academic_year, academic_term,
                                 sub_theme['id'], enabled_char, updated_by, updated_by, current_time, current_time)
            
            # 查詢並返回結果
            result = await SchoolYearSubThemeSettingsDAO.get_school_year_sub_theme_setting_by_code(
                conn, academic_year, academic_term, theme_code, sub_theme_code)
            return result

    @staticmethod
    async def delete_school_year_sub_theme_setting(conn, setting_id: str):
        """刪除學年期細項主題設定（通過 ID）"""
        setting = await SchoolYearSubThemeSettingsDAO.get_school_year_sub_theme_setting_by_id(conn, setting_id)
        if setting:
            query = "DELETE FROM academic_year_coures_sub_theme_settings WHERE id = $1"
            await Database.execute(conn, query, setting_id)
        return setting

    @staticmethod
    async def delete_school_year_sub_theme_setting_by_code(conn, academic_year: int, academic_term: int, 
                                                   theme_code: str, sub_theme_code: str):
        """刪除學年期細項主題設定（通過 CODE，用於向後兼容）"""
        setting = await SchoolYearSubThemeSettingsDAO.get_school_year_sub_theme_setting_by_code(
            conn, academic_year, academic_term, theme_code, sub_theme_code)
        if setting:
            return await SchoolYearSubThemeSettingsDAO.delete_school_year_sub_theme_setting(conn, setting['id'])
        return None


class SchoolYearDAO:
    """學年期數據訪問對象"""

    @staticmethod
    async def get_school_year_complete_info(conn, academic_year: int, academic_term: int) -> List:
        """獲取學年期完整資訊 - 包含主題、細項、指標設定
        
        回傳該學年期啟用的主題，以及每個主題的所有細項（不論是否啟用）
        每個細項會標記 enabled 狀態
        """
        # 先取得該學年期啟用的主題
        themes_query = """
        SELECT 
            syts.id as setting_id,
            syts.academic_year,
            syts.academic_term,
            syts.coures_themes_id,
            t.id as theme_id,
            t.theme_code,
            t.theme_name,
            t.theme_short_name,
            t.theme_english_name,
            syts.fill_in_week_enabled,
            syts.scale_max,
            syts.select_most_relevant_sub_theme_enabled
        FROM academic_year_coures_themes_setting syts
        JOIN coures_themes t ON syts.coures_themes_id = t.id
        WHERE syts.academic_year = $1 AND syts.academic_term = $2
        ORDER BY t.theme_code
        """
        themes_results = await Database.fetch(conn, themes_query, academic_year, academic_term)
        
        if not themes_results:
            return []
        
        results_list = []
        for theme_row in themes_results:
            theme_dict = dict(theme_row)
            theme_dict['fill_in_week_enabled'] = theme_dict['fill_in_week_enabled'] == 'Y'
            theme_dict['select_most_relevant_sub_theme_enabled'] = theme_dict.get('select_most_relevant_sub_theme_enabled', 'N') == 'Y'
            coures_themes_id = theme_dict['coures_themes_id']
            
            # 取得該主題的所有細項，並標記啟用狀態
            sub_themes_query = """
            SELECT 
                st.id as sub_theme_id,
                st.sub_theme_code,
                st.sub_theme_name,
                st.sub_theme_english_name,
                st.sub_theme_content,
                st.sub_theme_english_content,
                COALESCE(systs.enabled, 'N') as enabled
            FROM coures_sub_themes st
            LEFT JOIN academic_year_coures_sub_theme_settings systs 
                ON st.id = systs.coures_sub_themes_id
                AND systs.academic_year = $1 
                AND systs.academic_term = $2
            WHERE st.coures_themes_id = $3
            ORDER BY st.sub_theme_code
            """
            sub_themes_results = await Database.fetch(conn, sub_themes_query, academic_year, academic_term, coures_themes_id)
            
            # 為每個細項建立一筆記錄
            for sub_theme_row in sub_themes_results:
                result_dict = theme_dict.copy()
                sub_theme_dict = dict(sub_theme_row)
                result_dict['sub_theme_id'] = sub_theme_dict['sub_theme_id']
                result_dict['sub_theme_code'] = sub_theme_dict['sub_theme_code']
                result_dict['sub_theme_name'] = sub_theme_dict['sub_theme_name']
                result_dict['sub_theme_english_name'] = sub_theme_dict['sub_theme_english_name']
                result_dict['sub_theme_content'] = sub_theme_dict.get('sub_theme_content')
                result_dict['sub_theme_english_content'] = sub_theme_dict.get('sub_theme_english_content')
                result_dict['enabled'] = sub_theme_dict.get('enabled') == 'Y'
                results_list.append(result_dict)
        
        return results_list


class CourseEntriesDAO:
    """課程填寫記錄數據訪問對象"""

    @staticmethod
    async def create_course_entry(conn, subj_no: str, ps_class_nbr: str, academic_year: int, academic_term: int,
                                sub_theme_code: str, indicator_value: str, 
                                week_numbers: Optional[List[int]] = None, is_most_relevant: bool = False,
                                created_by: Optional[str] = None):
        """創建課程填寫記錄（如果已存在則更新）
        
        注意：sub_theme_code 用於查找 sub_theme_id
        """
        # 先通過 sub_theme_code 獲取 sub_theme_id
        # 需要先找到對應的 sub_theme（可能有多個 theme 有相同的 sub_theme_code）
        # 這裡需要通過學年期設定來確定是哪個 sub_theme
        sub_theme_query = """
        SELECT st.id, st.sub_theme_code
        FROM coures_sub_themes st
        JOIN academic_year_coures_sub_theme_settings systs ON st.id = systs.coures_sub_themes_id
        WHERE systs.academic_year = $1 
          AND systs.academic_term = $2 
          AND st.sub_theme_code = $3
          AND systs.enabled = 'Y'
        """
        sub_theme_result = await Database.fetchrow(conn, sub_theme_query, academic_year, academic_term, sub_theme_code)
        if not sub_theme_result:
            raise ValueError(f"細項主題 '{sub_theme_code}' 在學年期 {academic_year}-{academic_term} 中沒有啟用設定，無法創建資料")
        
        sub_theme_id = sub_theme_result['id']
        
        # 將 week_numbers 轉換為 JSON 字串（Oracle 使用 CLOB）
        week_numbers_json = None
        if week_numbers:
            week_numbers_json = json.dumps(week_numbers)
        
        # 將 is_most_relevant 轉換為 'Y'/'N'
        is_most_relevant_char = 'Y' if is_most_relevant else 'N'
        
        current_time = datetime.now()
        
        # 先檢查記錄是否已存在
        existing_entry = await CourseEntriesDAO.get_course_entry_by_sub_theme_id(
            conn, subj_no, ps_class_nbr, academic_year, academic_term, sub_theme_id)
        
        if existing_entry:
            # 記錄已存在，執行更新
            return await CourseEntriesDAO.update_course_entry_by_id(
                conn, existing_entry['id'], indicator_value, week_numbers, is_most_relevant, updated_by=created_by)
        else:
            # 記錄不存在，執行創建
            entry_id = str(uuid.uuid4())
            
            query = """
            INSERT INTO course_entries 
            (id, SUBJ_NO, PS_CLASS_NBR, ACADEMIC_YEAR, ACADEMIC_TERM, coures_sub_themes_id, indicator_value, week_numbers, 
             is_most_relevant, created_by, updated_by, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """
            await Database.execute(conn, query, entry_id, subj_no, ps_class_nbr, academic_year, academic_term,
                                  sub_theme_id, indicator_value, week_numbers_json, is_most_relevant_char,
                                  created_by, created_by, current_time, current_time)
            
            # Oracle 不支持 RETURNING，需要再次查詢
            return await CourseEntriesDAO.get_course_entry_by_id(conn, entry_id)

    @staticmethod
    async def get_course_entry_by_sub_theme_id(conn, subj_no: str, ps_class_nbr: str, academic_year: int, academic_term: int, sub_theme_id: str):
        """獲取單筆課程填寫記錄（通過 sub_theme_id）"""
        query = """
        SELECT ce.id, ce.SUBJ_NO, ce.PS_CLASS_NBR, ce.ACADEMIC_YEAR, ce.ACADEMIC_TERM, 
               ce.coures_sub_themes_id, st.id as sub_theme_id, st.sub_theme_code, t.theme_code, 
               ce.indicator_value, ce.week_numbers, ce.is_most_relevant,
               ce.created_at, ce.updated_at, ce.created_by, ce.updated_by
        FROM course_entries ce
        JOIN coures_sub_themes st ON ce.coures_sub_themes_id = st.id
        JOIN coures_themes t ON st.coures_themes_id = t.id
        WHERE ce.SUBJ_NO = $1 AND ce.PS_CLASS_NBR = $2 AND ce.ACADEMIC_YEAR = $3 AND ce.ACADEMIC_TERM = $4 AND ce.coures_sub_themes_id = $5
        """
        result = await Database.fetchrow(conn, query, subj_no, ps_class_nbr, academic_year, academic_term, sub_theme_id)
        if result:
            result = dict(result)
            if result.get('week_numbers'):
                if isinstance(result['week_numbers'], str):
                    result['week_numbers'] = json.loads(result['week_numbers'])
            # 轉換 is_most_relevant 為 boolean
            if result.get('is_most_relevant'):
                result['is_most_relevant'] = result['is_most_relevant'] == 'Y'
        return result

    @staticmethod
    async def get_course_entry(conn, subj_no: str, ps_class_nbr: str, academic_year: int, academic_term: int, sub_theme_code: str):
        """獲取單筆課程填寫記錄（通過 sub_theme_code，用於向後兼容）"""
        # 先找到對應的 sub_theme_id（通過學年期設定）
        sub_theme_query = """
        SELECT st.id
        FROM coures_sub_themes st
        JOIN academic_year_coures_sub_theme_settings systs ON st.id = systs.coures_sub_themes_id
        WHERE systs.academic_year = $1 
          AND systs.academic_term = $2 
          AND st.sub_theme_code = $3
        """
        sub_theme_result = await Database.fetchrow(conn, sub_theme_query, academic_year, academic_term, sub_theme_code)
        if not sub_theme_result:
            return None
        
        return await CourseEntriesDAO.get_course_entry_by_sub_theme_id(
            conn, subj_no, ps_class_nbr, academic_year, academic_term, sub_theme_result['id'])

    @staticmethod
    async def get_course_entry_by_id(conn, entry_id: str):
        """根據 ID 獲取單筆課程填寫記錄"""
        query = """
        SELECT ce.id, ce.SUBJ_NO, ce.PS_CLASS_NBR, ce.ACADEMIC_YEAR, ce.ACADEMIC_TERM, 
               ce.coures_sub_themes_id, st.id as sub_theme_id, st.sub_theme_code, t.theme_code, 
               ce.indicator_value, ce.week_numbers, ce.is_most_relevant,
               ce.created_at, ce.updated_at, ce.created_by, ce.updated_by
        FROM course_entries ce
        JOIN coures_sub_themes st ON ce.coures_sub_themes_id = st.id
        JOIN coures_themes t ON st.coures_themes_id = t.id
        WHERE ce.id = $1
        """
        result = await Database.fetchrow(conn, query, entry_id)
        if result:
            result = dict(result)
            if result.get('week_numbers'):
                if isinstance(result['week_numbers'], str):
                    result['week_numbers'] = json.loads(result['week_numbers'])
            # 轉換 is_most_relevant 為 boolean
            if result.get('is_most_relevant'):
                result['is_most_relevant'] = result['is_most_relevant'] == 'Y'
        return result

    @staticmethod
    async def create_course_entries_batch(conn, entries_data: List[dict]) -> List:
        """批量創建課程填寫記錄"""
        results = []
        for entry_data in entries_data:
            try:
                result = await CourseEntriesDAO.create_course_entry(
                    conn,
                    entry_data['subj_no'],
                    entry_data['ps_class_nbr'],
                    entry_data['academic_year'],
                    entry_data['academic_term'],
                    entry_data['sub_theme_code'],
                    entry_data['indicator_value'],
                    entry_data.get('week_numbers'),
                    entry_data.get('is_most_relevant', False),
                    created_by=entry_data.get('created_by')
                )
                if result:
                    results.append(result)
            except Exception as e:
                print(f"Error creating entry: {e}")
                continue
        return results

    @staticmethod
    async def get_teacher_form_data(conn, subj_no: str, ps_class_nbr: str, academic_year: int, academic_term: int) -> List:
        """
        獲取教師填寫表單數據
        直接使用 SUBJ_NO JOIN COFSUBJ 取得課程名稱，使用表中的 ACADEMIC_YEAR 和 ACADEMIC_TERM
        """
        query = """
        SELECT 
            COALESCE(cb.subj_chn_name, '') as course_chinese_name,
            COALESCE(cb.subj_eng_name, '') as course_english_name,
            ce.ACADEMIC_YEAR as academic_year,
            ce.ACADEMIC_TERM as academic_term,
            t.id as theme_id,
            t.theme_code,
            t.theme_name,
            t.theme_short_name,
            t.theme_english_name,
            syts.fill_in_week_enabled,
            syts.scale_max,
            syts.select_most_relevant_sub_theme_enabled,
            st.id as sub_theme_id,
            st.sub_theme_code,
            st.sub_theme_name,
            st.sub_theme_english_name,
            st.sub_theme_content,
            st.sub_theme_english_content,
            ce.indicator_value,
            ce.week_numbers,
            ce.is_most_relevant,
            ce.id as entry_id
        FROM academic_year_coures_themes_setting syts
        JOIN coures_themes t ON syts.coures_themes_id = t.id
        JOIN coures_sub_themes st ON st.coures_themes_id = syts.coures_themes_id
        JOIN academic_year_coures_sub_theme_settings systs 
            ON systs.academic_year = syts.academic_year 
            AND systs.academic_term = syts.academic_term
            AND systs.coures_sub_themes_id = st.id
        LEFT JOIN SCHOOL.COFSUBJ cb ON cb.subj_no = $1
        LEFT JOIN course_entries ce 
            ON ce.SUBJ_NO = $2
            AND ce.PS_CLASS_NBR = $3
            AND ce.ACADEMIC_YEAR = $4
            AND ce.ACADEMIC_TERM = $5
            AND systs.coures_sub_themes_id = ce.coures_sub_themes_id
        WHERE syts.academic_year = $6 
          AND syts.academic_term = $7
          AND systs.enabled = 'Y'
        ORDER BY t.theme_code, st.sub_theme_code
        """
        # 參數順序：$1=subj_no (COFSUBJ), $2=subj_no (course_entries), $3=ps_class_nbr (course_entries),
        # $4=academic_year (course_entries), $5=academic_term (course_entries), $6=academic_year (WHERE), $7=academic_term (WHERE)
        results = await Database.fetch(conn, query, subj_no, subj_no, ps_class_nbr, academic_year, academic_term, academic_year, academic_term)
        results_list = []
        for result in results:
            result_dict = dict(result)
            result_dict['fill_in_week_enabled'] = result_dict.get('fill_in_week_enabled') == 'Y'
            result_dict['select_most_relevant_sub_theme_enabled'] = result_dict.get('select_most_relevant_sub_theme_enabled') == 'Y'
            if result_dict.get('week_numbers') and isinstance(result_dict['week_numbers'], str):
                result_dict['week_numbers'] = json.loads(result_dict['week_numbers'])
            # 轉換 is_most_relevant 為 boolean
            if result_dict.get('is_most_relevant'):
                result_dict['is_most_relevant'] = result_dict['is_most_relevant'] == 'Y'
            results_list.append(result_dict)
        return results_list

    @staticmethod
    async def update_course_entry(conn, subj_no: str, ps_class_nbr: str, academic_year: int, academic_term: int, sub_theme_code: str,
                                indicator_value: str, week_numbers: Optional[List[int]] = None,
                                is_most_relevant: Optional[bool] = None, updated_by: Optional[str] = None):
        """更新課程填寫記錄（通過 sub_theme_code，用於向後兼容）"""
        # 先找到對應的 entry
        entry = await CourseEntriesDAO.get_course_entry(conn, subj_no, ps_class_nbr, academic_year, academic_term, sub_theme_code)
        if not entry:
            raise ValueError(f"找不到對應的課程填寫記錄")
        return await CourseEntriesDAO.update_course_entry_by_id(
            conn, entry['id'], indicator_value, week_numbers, is_most_relevant, updated_by)

    @staticmethod
    async def update_course_entry_by_id(conn, entry_id: str,
                                       indicator_value: str, week_numbers: Optional[List[int]] = None,
                                       is_most_relevant: Optional[bool] = None, updated_by: Optional[str] = None):
        """根據 ID 更新課程填寫記錄"""
        week_numbers_json = None
        if week_numbers:
            week_numbers_json = json.dumps(week_numbers)
        
        # 構建動態 SQL，確保參數正確綁定
        # 使用 CURRENT_TIMESTAMP 直接設置 updated_at，避免日期類型轉換問題
        update_fields = []
        values = []
        param_idx = 1
        
        update_fields.append(f"indicator_value = ${param_idx}")
        values.append(indicator_value)
        param_idx += 1
        
        update_fields.append(f"week_numbers = ${param_idx}")
        values.append(week_numbers_json)
        param_idx += 1
        
        if is_most_relevant is not None:
            is_most_relevant_char = 'Y' if is_most_relevant else 'N'
            update_fields.append(f"is_most_relevant = ${param_idx}")
            values.append(is_most_relevant_char)
            param_idx += 1
        
        if updated_by is not None:
            update_fields.append(f"updated_by = ${param_idx}")
            values.append(updated_by)
            param_idx += 1
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        # WHERE 條件的參數放在最後
        values.append(entry_id)
        
        query = f"""
        UPDATE course_entries 
        SET {', '.join(update_fields)}
        WHERE id = ${param_idx}
        """
        await Database.execute(conn, query, *values)
        return await CourseEntriesDAO.get_course_entry_by_id(conn, entry_id)

    @staticmethod
    async def get_courses_by_sub_theme(conn, academic_year: int, academic_term: int, 
                                      theme_code: str, sub_theme_code: str) -> List:
        """根據學年期和細項主題查詢已填寫的課程列表"""
        query = """
        SELECT DISTINCT ce.SUBJ_NO as course_id
        FROM course_entries ce
        JOIN coures_sub_themes st ON ce.coures_sub_themes_id = st.id
        JOIN coures_themes t ON st.coures_themes_id = t.id
        WHERE ce.ACADEMIC_YEAR = $1 
          AND ce.ACADEMIC_TERM = $2
          AND t.theme_code = $3 
          AND st.sub_theme_code = $4
        ORDER BY course_id
        """
        return await Database.fetch(conn, query, academic_year, academic_term, theme_code, sub_theme_code)

    @staticmethod
    async def check_course_entries_exist(conn, subj_no: str, ps_class_nbr: str, academic_year: int, academic_term: int) -> bool:
        """檢查指定課程是否有填寫記錄"""
        query = """
        SELECT COUNT(*) FROM course_entries 
        WHERE SUBJ_NO = $1 AND PS_CLASS_NBR = $2 AND ACADEMIC_YEAR = $3 AND ACADEMIC_TERM = $4
        """
        count = await Database.fetchval(conn, query, subj_no, ps_class_nbr, academic_year, academic_term)
        return count > 0 if count else False

    @staticmethod
    async def get_enabled_theme_sub_themes(conn, academic_year: int, academic_term: int) -> List:
        """取得某學年期所有啟用的主題和細項設定"""
        query = """
        SELECT DISTINCT t.theme_code, st.sub_theme_code 
        FROM academic_year_coures_sub_theme_settings systs
        JOIN coures_sub_themes st ON systs.coures_sub_themes_id = st.id
        JOIN coures_themes t ON st.coures_themes_id = t.id
        WHERE systs.academic_year = $1 AND systs.academic_term = $2 AND systs.enabled = 'Y'
        ORDER BY t.theme_code, st.sub_theme_code
        """
        return await Database.fetch(conn, query, academic_year, academic_term)

    @staticmethod
    async def get_course_entries_by_subj_no(conn, subj_no: str, ps_class_nbr: str, academic_year: int, academic_term: int) -> List:
        """取得指定課程的所有記錄"""
        query = """
        SELECT ce.id, ce.SUBJ_NO, ce.PS_CLASS_NBR, ce.ACADEMIC_YEAR, ce.ACADEMIC_TERM, 
               ce.coures_sub_themes_id, st.id as sub_theme_id, st.sub_theme_code, t.theme_code,
               ce.indicator_value, ce.week_numbers, ce.is_most_relevant, 
               ce.created_at, ce.updated_at, ce.created_by, ce.updated_by
        FROM course_entries ce
        JOIN coures_sub_themes st ON ce.coures_sub_themes_id = st.id
        JOIN coures_themes t ON st.coures_themes_id = t.id
        WHERE ce.SUBJ_NO = $1 AND ce.PS_CLASS_NBR = $2 AND ce.ACADEMIC_YEAR = $3 AND ce.ACADEMIC_TERM = $4
        ORDER BY t.theme_code, st.sub_theme_code
        """
        results = await Database.fetch(conn, query, subj_no, ps_class_nbr, academic_year, academic_term)
        results_list = []
        for result in results:
            result_dict = dict(result)
            if result_dict.get('week_numbers') and isinstance(result_dict['week_numbers'], str):
                result_dict['week_numbers'] = json.loads(result_dict['week_numbers'])
            # 轉換 is_most_relevant 為 boolean
            if result_dict.get('is_most_relevant'):
                result_dict['is_most_relevant'] = result_dict['is_most_relevant'] == 'Y'
            results_list.append(result_dict)
        return results_list

    @staticmethod
    async def delete_course_entries_by_subj_no(conn, subj_no: str, ps_class_nbr: str, academic_year: int, academic_term: int) -> int:
        """刪除指定課程的所有記錄，返回刪除的記錄數"""
        # 先查詢有多少筆
        count_query = "SELECT COUNT(*) FROM course_entries WHERE SUBJ_NO = $1 AND PS_CLASS_NBR = $2 AND ACADEMIC_YEAR = $3 AND ACADEMIC_TERM = $4"
        count = await Database.fetchval(conn, count_query, subj_no, ps_class_nbr, academic_year, academic_term)
        
        if count and count > 0:
            delete_query = "DELETE FROM course_entries WHERE SUBJ_NO = $1 AND PS_CLASS_NBR = $2 AND ACADEMIC_YEAR = $3 AND ACADEMIC_TERM = $4"
            await Database.execute(conn, delete_query, subj_no, ps_class_nbr, academic_year, academic_term)
        
        return count if count else 0

    @staticmethod
    async def delete_course_entry(conn, subj_no: str, ps_class_nbr: str, academic_year: int, academic_term: int, sub_theme_code: str):
        """刪除指定的課程填寫記錄（通過 sub_theme_code，用於向後兼容）"""
        entry = await CourseEntriesDAO.get_course_entry(conn, subj_no, ps_class_nbr, academic_year, academic_term, sub_theme_code)
        if entry:
            return await CourseEntriesDAO.delete_course_entry_by_id(conn, entry['id'])
        return None

    @staticmethod
    async def delete_course_entry_by_id(conn, entry_id: str):
        """根據 ID 刪除指定的課程填寫記錄"""
        entry = await CourseEntriesDAO.get_course_entry_by_id(conn, entry_id)
        if entry:
            query = "DELETE FROM course_entries WHERE id = $1"
            await Database.execute(conn, query, entry_id)
        return entry

    @staticmethod
    async def copy_course_entry_with_new_user(
        conn,
        subj_no: str,
        ps_class_nbr: str,
        academic_year: int,
        academic_term: int,
        sub_theme_code: str,
        indicator_value: str,
        week_numbers_json: Optional[str],
        is_most_relevant: bool,
        user_id: str
    ):
        """複製單筆課程記錄（用於跨學年期複製）"""
        # 先通過 sub_theme_code 獲取 sub_theme_id
        sub_theme_query = """
        SELECT st.id
        FROM coures_sub_themes st
        JOIN academic_year_coures_sub_theme_settings systs ON st.id = systs.coures_sub_themes_id
        WHERE systs.academic_year = $1 
          AND systs.academic_term = $2 
          AND st.sub_theme_code = $3
        """
        sub_theme_result = await Database.fetchrow(conn, sub_theme_query, academic_year, academic_term, sub_theme_code)
        if not sub_theme_result:
            raise ValueError(f"細項主題 '{sub_theme_code}' 在學年期 {academic_year}-{academic_term} 中沒有設定")
        
        sub_theme_id = sub_theme_result['id']
        current_time = datetime.now()
        entry_id = str(uuid.uuid4())
        is_most_relevant_char = 'Y' if is_most_relevant else 'N'
        query = """
        INSERT INTO course_entries (
            id, SUBJ_NO, PS_CLASS_NBR, ACADEMIC_YEAR, ACADEMIC_TERM, coures_sub_themes_id,
            indicator_value, week_numbers, is_most_relevant, created_by, updated_by, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """
        await Database.execute(conn, query, entry_id, subj_no, ps_class_nbr, academic_year, academic_term, sub_theme_id,
                              indicator_value, week_numbers_json, is_most_relevant_char, user_id, user_id, current_time, current_time)
        # Oracle 不支持 RETURNING，需要再次查詢
        result = await CourseEntriesDAO.get_course_entry_by_id(conn, entry_id)
        if result:
            result = dict(result)
            if result.get('week_numbers') and isinstance(result['week_numbers'], str):
                result['week_numbers'] = json.loads(result['week_numbers'])
        return result

    @staticmethod
    async def get_theme_most_relevant_requirement(conn, academic_year: int, academic_term: int, theme_code: str) -> bool:
        """查詢該主題是否需要勾選最相關科目"""
        query = """
        SELECT syts.select_most_relevant_sub_theme_enabled
        FROM academic_year_coures_themes_setting syts
        JOIN coures_themes t ON syts.coures_themes_id = t.id
        WHERE syts.academic_year = $1 AND syts.academic_term = $2 AND t.theme_code = $3
        """
        result = await Database.fetchrow(conn, query, academic_year, academic_term, theme_code)
        if result:
            return result['select_most_relevant_sub_theme_enabled'] == 'Y'
        return False

    @staticmethod
    async def check_most_relevant_validation(conn, subj_no: str, ps_class_nbr: str, academic_year: int, 
                                           academic_term: int, theme_code: str, exclude_sub_theme_code: Optional[str] = None) -> bool:
        """檢查該課程在該主題下是否已有 is_most_relevant='Y' 的記錄"""
        if exclude_sub_theme_code:
            query = """
            SELECT COUNT(*) as count
            FROM course_entries ce
            JOIN coures_sub_themes st ON ce.coures_sub_themes_id = st.id
            JOIN coures_themes t ON st.coures_themes_id = t.id
            WHERE ce.SUBJ_NO = $1 AND ce.PS_CLASS_NBR = $2 
              AND ce.ACADEMIC_YEAR = $3 AND ce.ACADEMIC_TERM = $4
              AND t.theme_code = $5 AND ce.is_most_relevant = 'Y'
              AND st.sub_theme_code != $6
            """
            result = await Database.fetchrow(conn, query, subj_no, ps_class_nbr, academic_year, academic_term, theme_code, exclude_sub_theme_code)
        else:
            query = """
            SELECT COUNT(*) as count
            FROM course_entries ce
            JOIN coures_sub_themes st ON ce.coures_sub_themes_id = st.id
            JOIN coures_themes t ON st.coures_themes_id = t.id
            WHERE ce.SUBJ_NO = $1 AND ce.PS_CLASS_NBR = $2 
              AND ce.ACADEMIC_YEAR = $3 AND ce.ACADEMIC_TERM = $4
              AND t.theme_code = $5 AND ce.is_most_relevant = 'Y'
            """
            result = await Database.fetchrow(conn, query, subj_no, ps_class_nbr, academic_year, academic_term, theme_code)
        
        if result:
            return result['count'] > 0
        return False

    @staticmethod
    async def get_all_courses_by_academic_year_term(conn, academic_year: int, academic_term: int) -> List:
        """查詢指定學年期的所有課程（DISTINCT SUBJ_NO, PS_CLASS_NBR）"""
        query = """
        SELECT DISTINCT SUBJ_NO, PS_CLASS_NBR
        FROM course_entries
        WHERE ACADEMIC_YEAR = $1 AND ACADEMIC_TERM = $2
        ORDER BY SUBJ_NO, PS_CLASS_NBR
        """
        results = await Database.fetch(conn, query, academic_year, academic_term)
        return [dict(row) for row in results]

    @staticmethod
    async def get_all_course_entries_by_academic_year_term(conn, academic_year: int, academic_term: int) -> List:
        """查詢指定學年期的所有課程填寫記錄（包含課程基本資訊和所有 course_entries 資料）"""
        query = """
        SELECT 
            ce.id,
            ce.SUBJ_NO,
            ce.PS_CLASS_NBR,
            ce.ACADEMIC_YEAR,
            ce.ACADEMIC_TERM,
            ce.coures_sub_themes_id,
            st.id as sub_theme_id,
            st.sub_theme_code,
            t.theme_code,
            st.sub_theme_name,
            ce.indicator_value,
            ce.week_numbers,
            ce.is_most_relevant,
            COALESCE(cb.subj_chn_name, '') as course_chinese_name
        FROM course_entries ce
        JOIN coures_sub_themes st ON ce.coures_sub_themes_id = st.id
        JOIN coures_themes t ON st.coures_themes_id = t.id
        LEFT JOIN SCHOOL.COFSUBJ cb ON cb.subj_no = ce.SUBJ_NO
        WHERE ce.ACADEMIC_YEAR = $1 AND ce.ACADEMIC_TERM = $2
        ORDER BY t.theme_code, st.sub_theme_code
        """
        results = await Database.fetch(conn, query, academic_year, academic_term)
        results_list = []
        for result in results:
            result_dict = dict(result)
            # 解析 week_numbers JSON 字串為列表
            if result_dict.get('week_numbers') and isinstance(result_dict['week_numbers'], str):
                result_dict['week_numbers'] = json.loads(result_dict['week_numbers'])
            # 轉換 is_most_relevant 為 boolean
            if result_dict.get('is_most_relevant'):
                result_dict['is_most_relevant'] = result_dict['is_most_relevant'] == 'Y'
            results_list.append(result_dict)
        return results_list

    @staticmethod
    async def get_courses_from_cofopms_with_filters(
        conn,
        academic_year_start: int,
        academic_term_start: int,
        academic_year_end: int,
        academic_term_end: int,
        department: Optional[str] = None,
        has_class: Optional[str] = None,
        theme_code: Optional[str] = None,
        sub_theme_code: Optional[str] = None
    ) -> List:
        """
        從 COFOPMS 查詢課程資料，支援篩選條件
        
        Args:
            academic_year_start: 學年期起（學年）
            academic_term_start: 學年期起（學期）
            academic_year_end: 學年期訖（學年）
            academic_term_end: 學年期訖（學期）
            department: 開課單位代碼（可選）
            has_class: 成班與否 Y/N（可選）
            theme_code: 主題代碼（可選，過濾有填寫該主題的課程）
            sub_theme_code: 細項主題代碼（可選，過濾有填寫該細項的課程）
        
        Returns:
            課程列表，包含 COFOPMS 欄位和 JOIN 的名稱欄位
        """
        # 組合學年期字串用於範圍比較
        start_year_term = f"{academic_year_start}{academic_term_start}"
        end_year_term = f"{academic_year_end}{academic_term_end}"
        
        # 基本查詢
        query = """
        SELECT 
            o.OPMS_ACADM_YEAR,
            o.OPMS_ACADM_TERM,
            o.OPMS_SERIAL_NO,
            o.PS_CLASS_NBR,
            o.OPMS_COURSE_NO,
            COALESCE(cs.SUBJ_CHN_NAME, '') as COURSE_NAME,
            o.OPMS_SET_DEPT,
            COALESCE(d1.DEPT_FULL_NAME, '') as DEPT_NAME,
            o.OPMS_DEPT,
            COALESCE(d2.DEPT_FULL_NAME, '') as DEPT_NAME_SEL,
            o.OPMS_TEACHER,
            COALESCE(p.EMPL_CHN_NAME, '') as TEACHER_NAME,
            o.OPMS_EXPR,
            COALESCE(e.EMPL_CHN_NAME, '') as EXPR_NAME,
            o.OPMS_CODE,
            o.OPMS_COURSE_KIND,
            o.OPMS_CREDIT,
            o.OPMS_SEL_STUDENTS,
            o.OPMS_STUDENTS,
            o.OPMS_AGREE,
            o.OPMS_CLASS_GROUP,
            o.OPMS_KIND_CODE,
            o.OPMS_TEACHER_GROUP,
            o.OPMS_ENGLISH_GROUP
        FROM SCHOOL.COFOPMS o
        LEFT JOIN SCHOOL.COFSUBJ cs ON o.OPMS_COURSE_NO = cs.SUBJ_NO
        LEFT JOIN (
            SELECT DEPT_NO, DEPT_FULL_NAME,
                   ROW_NUMBER() OVER (PARTITION BY DEPT_NO ORDER BY DEPT_D_FROM DESC NULLS LAST) as rn
            FROM PERSON.NCHUDEPT
        ) d1 ON o.OPMS_SET_DEPT = d1.DEPT_NO AND d1.rn = 1
        LEFT JOIN (
            SELECT DEPT_NO, DEPT_FULL_NAME,
                   ROW_NUMBER() OVER (PARTITION BY DEPT_NO ORDER BY DEPT_D_FROM DESC NULLS LAST) as rn
            FROM PERSON.NCHUDEPT
        ) d2 ON o.OPMS_DEPT = d2.DEPT_NO AND d2.rn = 1
        LEFT JOIN PERSON.PSFEMPL p ON o.OPMS_TEACHER = p.EMPL_NO
        LEFT JOIN PERSON.PSFEMPL e ON o.OPMS_EXPR = e.EMPL_NO
        WHERE (o.OPMS_ACADM_YEAR || o.OPMS_ACADM_TERM) >= $1
          AND (o.OPMS_ACADM_YEAR || o.OPMS_ACADM_TERM) <= $2
        """
        
        params = [start_year_term, end_year_term]
        param_idx = 3
        
        # 開課單位篩選
        if department:
            query += f" AND o.OPMS_SET_DEPT = ${param_idx}"
            params.append(department)
            param_idx += 1
        
        # 成班與否篩選
        if has_class:
            query += f" AND o.OPMS_CODE = ${param_idx}"
            params.append(has_class)
            param_idx += 1
        
        # 主題篩選（過濾有填寫該主題的課程）
        if theme_code:
            query += f"""
            AND EXISTS (
                SELECT 1 FROM course_entries ce
                JOIN coures_sub_themes st ON ce.coures_sub_themes_id = st.id
                JOIN coures_themes t ON st.coures_themes_id = t.id
                WHERE ce.PS_CLASS_NBR = o.PS_CLASS_NBR
                  AND ce.ACADEMIC_YEAR = TO_NUMBER(o.OPMS_ACADM_YEAR)
                  AND ce.ACADEMIC_TERM = TO_NUMBER(o.OPMS_ACADM_TERM)
                  AND t.theme_code = ${param_idx}
            )
            """
            params.append(theme_code)
            param_idx += 1
        
        # 細項主題篩選（過濾有填寫該細項的課程）
        if sub_theme_code:
            query += f"""
            AND EXISTS (
                SELECT 1 FROM course_entries ce
                JOIN coures_sub_themes st ON ce.coures_sub_themes_id = st.id
                WHERE ce.PS_CLASS_NBR = o.PS_CLASS_NBR
                  AND ce.ACADEMIC_YEAR = TO_NUMBER(o.OPMS_ACADM_YEAR)
                  AND ce.ACADEMIC_TERM = TO_NUMBER(o.OPMS_ACADM_TERM)
                  AND st.sub_theme_code = ${param_idx}
            )
            """
            params.append(sub_theme_code)
            param_idx += 1
        
        query += " ORDER BY o.OPMS_ACADM_YEAR, o.OPMS_ACADM_TERM, o.OPMS_SET_DEPT, o.OPMS_SERIAL_NO"
        
        results = await Database.fetch(conn, query, *params)
        return [dict(row) for row in results]

    @staticmethod
    async def get_course_entries_with_filters(
        conn,
        academic_year_start: int,
        academic_term_start: int,
        academic_year_end: int,
        academic_term_end: int,
        theme_code: Optional[str] = None,
        sub_theme_code: Optional[str] = None
    ) -> List:
        """
        查詢課程填寫記錄，支援學年期範圍和主題/細項篩選
        
        Args:
            academic_year_start: 學年期起（學年）
            academic_term_start: 學年期起（學期）
            academic_year_end: 學年期訖（學年）
            academic_term_end: 學年期訖（學期）
            theme_code: 主題代碼（可選）
            sub_theme_code: 細項主題代碼（可選）
        
        Returns:
            課程填寫記錄列表
        """
        # 組合學年期字串用於範圍比較
        start_year_term = f"{academic_year_start}{academic_term_start}"
        end_year_term = f"{academic_year_end}{academic_term_end}"
        
        query = """
        SELECT 
            ce.id,
            ce.SUBJ_NO,
            ce.PS_CLASS_NBR,
            ce.ACADEMIC_YEAR,
            ce.ACADEMIC_TERM,
            ce.coures_sub_themes_id,
            st.id as sub_theme_id,
            st.sub_theme_code,
            t.theme_code,
            t.theme_short_name,
            st.sub_theme_name,
            ce.indicator_value,
            ce.week_numbers,
            ce.is_most_relevant
        FROM course_entries ce
        JOIN coures_sub_themes st ON ce.coures_sub_themes_id = st.id
        JOIN coures_themes t ON st.coures_themes_id = t.id
        WHERE (ce.ACADEMIC_YEAR || ce.ACADEMIC_TERM) >= $1
          AND (ce.ACADEMIC_YEAR || ce.ACADEMIC_TERM) <= $2
        """
        
        params = [start_year_term, end_year_term]
        param_idx = 3
        
        # 主題篩選
        if theme_code:
            query += f" AND t.theme_code = ${param_idx}"
            params.append(theme_code)
            param_idx += 1
        
        # 細項主題篩選
        if sub_theme_code:
            query += f" AND st.sub_theme_code = ${param_idx}"
            params.append(sub_theme_code)
            param_idx += 1
        
        query += " ORDER BY ce.ACADEMIC_YEAR, ce.ACADEMIC_TERM, t.theme_code, st.sub_theme_code"
        
        results = await Database.fetch(conn, query, *params)
        results_list = []
        for result in results:
            result_dict = dict(result)
            # 解析 week_numbers JSON 字串為列表
            if result_dict.get('week_numbers') and isinstance(result_dict['week_numbers'], str):
                result_dict['week_numbers'] = json.loads(result_dict['week_numbers'])
            # 轉換 is_most_relevant 為 boolean
            if result_dict.get('is_most_relevant'):
                result_dict['is_most_relevant'] = result_dict['is_most_relevant'] == 'Y'
            results_list.append(result_dict)
        return results_list
