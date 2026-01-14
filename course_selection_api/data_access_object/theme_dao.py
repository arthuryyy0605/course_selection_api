from typing import List, Optional
from datetime import datetime
import uuid
from .db import Database


class ThemeDAO:
    """主題數據訪問對象"""

    @staticmethod
    async def create_theme(conn, theme_code: str, theme_name: str, theme_short_name: str, 
                          theme_english_name: str, chinese_link: Optional[str] = None, 
                          english_link: Optional[str] = None, created_by: Optional[str] = None):
        """創建新主題"""
        theme_id = str(uuid.uuid4())
        current_time = datetime.now()
        query = """
        INSERT INTO coures_themes 
        (id, theme_code, theme_name, theme_short_name, theme_english_name, chinese_link, english_link, 
         created_by, updated_by, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """
        await Database.execute(conn, query, theme_id, theme_code, theme_name, theme_short_name, 
                              theme_english_name, chinese_link, english_link, created_by, created_by, current_time, current_time)
        # Oracle 不支持 RETURNING，需要再次查詢
        return await ThemeDAO.get_theme_by_id(conn, theme_id)

    @staticmethod
    async def get_theme_by_id(conn, theme_id: str):
        """根據主題ID獲取主題"""
        query = """
        SELECT id, theme_code, theme_name, theme_short_name, theme_english_name, 
               chinese_link, english_link, created_at, updated_at, created_by, updated_by
        FROM coures_themes
        WHERE id = $1
        """
        result = await Database.fetchrow(conn, query, theme_id)
        return dict(result) if result else None

    @staticmethod
    async def get_theme_by_code(conn, theme_code: str):
        """根據主題代碼獲取主題"""
        query = """
        SELECT id, theme_code, theme_name, theme_short_name, theme_english_name, 
               chinese_link, english_link, created_at, updated_at, created_by, updated_by
        FROM coures_themes
        WHERE theme_code = $1
        """
        result = await Database.fetchrow(conn, query, theme_code)
        return dict(result) if result else None

    @staticmethod
    async def get_all_themes(conn) -> List:
        """獲取所有主題"""
        query = """
        SELECT id, theme_code, theme_name, theme_short_name, theme_english_name, 
               chinese_link, english_link, created_at, updated_at, created_by, updated_by
        FROM coures_themes
        ORDER BY theme_code
        """
        results = await Database.fetch(conn, query)
        return [dict(r) for r in results]

    @staticmethod
    async def update_theme(conn, theme_id: str, theme_code: Optional[str] = None,
                          theme_name: Optional[str] = None, 
                          theme_short_name: Optional[str] = None, theme_english_name: Optional[str] = None,
                          chinese_link: Optional[str] = None, english_link: Optional[str] = None,
                          updated_by: Optional[str] = None):
        """更新主題（通過 ID）"""
        # 動態構建更新查詢
        update_fields = []
        values = []
        param_idx = 1

        if theme_code is not None:
            update_fields.append(f"theme_code = ${param_idx}")
            values.append(theme_code)
            param_idx += 1

        if theme_name is not None:
            update_fields.append(f"theme_name = ${param_idx}")
            values.append(theme_name)
            param_idx += 1

        if theme_short_name is not None:
            update_fields.append(f"theme_short_name = ${param_idx}")
            values.append(theme_short_name)
            param_idx += 1

        if theme_english_name is not None:
            update_fields.append(f"theme_english_name = ${param_idx}")
            values.append(theme_english_name)
            param_idx += 1

        if chinese_link is not None:
            update_fields.append(f"chinese_link = ${param_idx}")
            values.append(chinese_link)
            param_idx += 1

        if english_link is not None:
            update_fields.append(f"english_link = ${param_idx}")
            values.append(english_link)
            param_idx += 1

        if not update_fields:
            # 如果沒有字段需要更新，直接返回原數據
            return await ThemeDAO.get_theme_by_id(conn, theme_id)

        # 添加 updated_by 和 updated_at（手動更新時間）
        if updated_by is not None:
            update_fields.append(f"updated_by = ${param_idx}")
            values.append(updated_by)
            param_idx += 1
        
        # Oracle 需要手動更新 updated_at
        from datetime import datetime
        update_fields.append(f"updated_at = ${param_idx}")
        values.append(datetime.now())
        param_idx += 1
        
        values.append(theme_id)
        
        query = f"""
        UPDATE coures_themes 
        SET {', '.join(update_fields)}
        WHERE id = ${param_idx}
        """
        
        await Database.execute(conn, query, *values)
        return await ThemeDAO.get_theme_by_id(conn, theme_id)

    @staticmethod
    async def update_theme_by_code(conn, theme_code: str, theme_name: Optional[str] = None, 
                          theme_short_name: Optional[str] = None, theme_english_name: Optional[str] = None,
                          chinese_link: Optional[str] = None, english_link: Optional[str] = None,
                          updated_by: Optional[str] = None):
        """更新主題（通過 CODE，用於向後兼容）"""
        # 先獲取 ID
        theme = await ThemeDAO.get_theme_by_code(conn, theme_code)
        if not theme:
            return None
        return await ThemeDAO.update_theme(conn, theme['id'], theme_code, theme_name, 
                                          theme_short_name, theme_english_name, 
                                          chinese_link, english_link, updated_by)

    @staticmethod
    async def delete_theme(conn, theme_id: str):
        """刪除主題（通過 ID）"""
        # 先獲取主題資訊
        theme = await ThemeDAO.get_theme_by_id(conn, theme_id)
        if theme:
            query = "DELETE FROM coures_themes WHERE id = $1"
            await Database.execute(conn, query, theme_id)
        return theme

    @staticmethod
    async def delete_theme_by_code(conn, theme_code: str):
        """刪除主題（通過 CODE，用於向後兼容）"""
        theme = await ThemeDAO.get_theme_by_code(conn, theme_code)
        if theme:
            return await ThemeDAO.delete_theme(conn, theme['id'])
        return None

    @staticmethod
    async def check_theme_has_sub_themes(conn, theme_id: str) -> bool:
        """檢查主題是否有相關的細項主題"""
        query = "SELECT COUNT(*) FROM coures_sub_themes WHERE coures_themes_id = $1"
        count = await Database.fetchval(conn, query, theme_id)
        return count > 0 if count else False


class SubThemeDAO:
    """細項主題數據訪問對象"""

    @staticmethod
    async def create_sub_theme(conn, coures_themes_id: str, sub_theme_code: str,
                              sub_theme_name: str, sub_theme_english_name: str,
                              sub_theme_content: Optional[str] = None,
                              sub_theme_english_content: Optional[str] = None,
                              created_by: Optional[str] = None):
        """創建新細項主題"""
        # 驗證主題ID是否存在
        theme = await ThemeDAO.get_theme_by_id(conn, coures_themes_id)
        if not theme:
            raise ValueError(f"主題ID '{coures_themes_id}' 不存在")
        
        sub_theme_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        query = """
        INSERT INTO coures_sub_themes 
        (id, coures_themes_id, sub_theme_code, sub_theme_name, sub_theme_english_name, 
         sub_theme_content, sub_theme_english_content, created_by, updated_by, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """
        await Database.execute(conn, query, sub_theme_id, coures_themes_id, sub_theme_code, sub_theme_name, 
                              sub_theme_english_name, sub_theme_content, sub_theme_english_content, created_by, created_by, current_time, current_time)
        # Oracle 不支持 RETURNING，需要再次查詢
        return await SubThemeDAO.get_sub_theme_by_id(conn, sub_theme_id)

    @staticmethod
    async def get_sub_theme_by_id(conn, sub_theme_id: str):
        """根據細項主題ID獲取細項主題"""
        query = """
        SELECT st.id, st.coures_themes_id, t.theme_code, st.sub_theme_code, st.sub_theme_name, st.sub_theme_english_name, 
               st.sub_theme_content, st.sub_theme_english_content, st.created_at, st.updated_at, st.created_by, st.updated_by
        FROM coures_sub_themes st
        JOIN coures_themes t ON st.coures_themes_id = t.id
        WHERE st.id = $1
        """
        result = await Database.fetchrow(conn, query, sub_theme_id)
        return dict(result) if result else None

    @staticmethod
    async def get_sub_theme(conn, sub_theme_code: str):
        """根據細項主題代碼獲取細項主題（不需要 theme_code）"""
        query = """
        SELECT st.id, st.coures_themes_id, t.theme_code, st.sub_theme_code, st.sub_theme_name, st.sub_theme_english_name, 
               st.sub_theme_content, st.sub_theme_english_content, st.created_at, st.updated_at, st.created_by, st.updated_by
        FROM coures_sub_themes st
        JOIN coures_themes t ON st.coures_themes_id = t.id
        WHERE st.sub_theme_code = $1
        """
        result = await Database.fetchrow(conn, query, sub_theme_code)
        return dict(result) if result else None

    @staticmethod
    async def get_sub_theme_by_code(conn, theme_code: str, sub_theme_code: str):
        """根據主題代碼和細項主題代碼獲取細項主題"""
        query = """
        SELECT st.id, st.coures_themes_id, t.theme_code, st.sub_theme_code, st.sub_theme_name, st.sub_theme_english_name, 
               st.sub_theme_content, st.sub_theme_english_content, st.created_at, st.updated_at, st.created_by, st.updated_by
        FROM coures_sub_themes st
        JOIN coures_themes t ON st.coures_themes_id = t.id
        WHERE t.theme_code = $1 AND st.sub_theme_code = $2
        """
        result = await Database.fetchrow(conn, query, theme_code, sub_theme_code)
        return dict(result) if result else None

    @staticmethod
    async def get_all_sub_themes(conn) -> List:
        """獲取所有細項主題列表"""
        query = """
        SELECT st.id, st.coures_themes_id, t.theme_code, st.sub_theme_code, st.sub_theme_name, st.sub_theme_english_name, 
               st.sub_theme_content, st.sub_theme_english_content, st.created_at, st.updated_at, st.created_by, st.updated_by
        FROM coures_sub_themes st
        JOIN coures_themes t ON st.coures_themes_id = t.id
        ORDER BY t.theme_code, st.sub_theme_code
        """
        results = await Database.fetch(conn, query)
        return [dict(r) for r in results]

    @staticmethod
    async def get_sub_themes_by_theme_code(conn, theme_code: str) -> List:
        """根據主題代碼獲取細項主題列表"""
        query = """
        SELECT st.id, st.coures_themes_id, t.theme_code, st.sub_theme_code, st.sub_theme_name, st.sub_theme_english_name, 
               st.sub_theme_content, st.sub_theme_english_content, st.created_at, st.updated_at, st.created_by, st.updated_by
        FROM coures_sub_themes st
        JOIN coures_themes t ON st.coures_themes_id = t.id
        WHERE t.theme_code = $1
        ORDER BY st.sub_theme_code
        """
        results = await Database.fetch(conn, query, theme_code)
        return [dict(r) for r in results]

    @staticmethod
    async def get_sub_themes_by_theme_id(conn, theme_id: str) -> List:
        """根據主題ID獲取細項主題列表"""
        query = """
        SELECT st.id, st.coures_themes_id, t.theme_code, st.sub_theme_code, st.sub_theme_name, st.sub_theme_english_name, 
               st.sub_theme_content, st.sub_theme_english_content, st.created_at, st.updated_at, st.created_by, st.updated_by
        FROM coures_sub_themes st
        JOIN coures_themes t ON st.coures_themes_id = t.id
        WHERE st.coures_themes_id = $1
        ORDER BY st.sub_theme_code
        """
        results = await Database.fetch(conn, query, theme_id)
        return [dict(r) for r in results]

    @staticmethod
    async def update_sub_theme(conn, sub_theme_id: str,
                              coures_themes_id: Optional[str] = None,
                              sub_theme_code: Optional[str] = None,
                              sub_theme_name: Optional[str] = None,
                              sub_theme_english_name: Optional[str] = None,
                              sub_theme_content: Optional[str] = None,
                              sub_theme_english_content: Optional[str] = None,
                              updated_by: Optional[str] = None):
        """更新細項主題（通過 ID）"""
        # 動態構建更新查詢
        update_fields = []
        values = []
        param_idx = 1

        if coures_themes_id is not None:
            update_fields.append(f"coures_themes_id = ${param_idx}")
            values.append(coures_themes_id)
            param_idx += 1

        if sub_theme_code is not None:
            update_fields.append(f"sub_theme_code = ${param_idx}")
            values.append(sub_theme_code)
            param_idx += 1

        if sub_theme_name is not None:
            update_fields.append(f"sub_theme_name = ${param_idx}")
            values.append(sub_theme_name)
            param_idx += 1

        if sub_theme_english_name is not None:
            update_fields.append(f"sub_theme_english_name = ${param_idx}")
            values.append(sub_theme_english_name)
            param_idx += 1

        if sub_theme_content is not None:
            update_fields.append(f"sub_theme_content = ${param_idx}")
            values.append(sub_theme_content)
            param_idx += 1

        if sub_theme_english_content is not None:
            update_fields.append(f"sub_theme_english_content = ${param_idx}")
            values.append(sub_theme_english_content)
            param_idx += 1

        if not update_fields:
            # 如果沒有字段需要更新，直接返回原數據
            return await SubThemeDAO.get_sub_theme_by_id(conn, sub_theme_id)

        # 添加 updated_by 和 updated_at（手動更新時間）
        if updated_by is not None:
            update_fields.append(f"updated_by = ${param_idx}")
            values.append(updated_by)
            param_idx += 1
        
        # Oracle 需要手動更新 updated_at
        update_fields.append(f"updated_at = ${param_idx}")
        values.append(datetime.now())
        param_idx += 1
        
        values.append(sub_theme_id)
        
        query = f"""
        UPDATE coures_sub_themes 
        SET {', '.join(update_fields)}
        WHERE id = ${param_idx}
        """
        
        await Database.execute(conn, query, *values)
        return await SubThemeDAO.get_sub_theme_by_id(conn, sub_theme_id)

    @staticmethod
    async def update_sub_theme_by_code(conn, theme_code: str, sub_theme_code: str,
                              new_theme_code: Optional[str] = None, sub_theme_name: Optional[str] = None,
                              sub_theme_english_name: Optional[str] = None,
                              sub_theme_content: Optional[str] = None,
                              sub_theme_english_content: Optional[str] = None,
                              updated_by: Optional[str] = None):
        """更新細項主題（通過 CODE，用於向後兼容）"""
        # 先獲取 ID
        sub_theme = await SubThemeDAO.get_sub_theme_by_code(conn, theme_code, sub_theme_code)
        if not sub_theme:
            return None
        
        # 如果需要更新 theme_code，需要獲取新的 theme_id
        coures_themes_id = sub_theme['coures_themes_id']
        if new_theme_code is not None:
            new_theme = await ThemeDAO.get_theme_by_code(conn, new_theme_code)
            if not new_theme:
                raise ValueError(f"主題代碼 '{new_theme_code}' 不存在")
            coures_themes_id = new_theme['id']
        
        return await SubThemeDAO.update_sub_theme(conn, sub_theme['id'], coures_themes_id, 
                                                  None, sub_theme_code, sub_theme_name, 
                                                  sub_theme_english_name, sub_theme_content, 
                                                  sub_theme_english_content, updated_by)

    @staticmethod
    async def delete_sub_theme(conn, sub_theme_id: str):
        """刪除細項主題（通過 ID）"""
        # 先獲取細項主題資訊
        sub_theme = await SubThemeDAO.get_sub_theme_by_id(conn, sub_theme_id)
        if sub_theme:
            query = "DELETE FROM coures_sub_themes WHERE id = $1"
            await Database.execute(conn, query, sub_theme_id)
        return sub_theme

    @staticmethod
    async def delete_sub_theme_by_code(conn, theme_code: str, sub_theme_code: str):
        """刪除細項主題（通過 CODE，用於向後兼容）"""
        sub_theme = await SubThemeDAO.get_sub_theme_by_code(conn, theme_code, sub_theme_code)
        if sub_theme:
            return await SubThemeDAO.delete_sub_theme(conn, sub_theme['id'])
        return None

    @staticmethod
    async def check_sub_theme_has_data(conn, sub_theme_id: str) -> bool:
        """檢查細項主題是否已有填寫相關資料"""
        query = """
        SELECT COUNT(*) 
        FROM course_entries
        WHERE coures_sub_themes_id = $1
        """
        try:
            count = await Database.fetchval(conn, query, sub_theme_id)
            return count > 0 if count else False
        except Exception:
            # 如果查詢失敗，假設沒有相關數據
            return False
