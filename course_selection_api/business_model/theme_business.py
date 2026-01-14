from fastapi import HTTPException, status
from typing import Dict, Any, List
import oracledb

from course_selection_api.data_access_object.theme_dao import ThemeDAO, SubThemeDAO
from course_selection_api.schema.theme import (
    ThemeCreateRequest, ThemeUpdateRequest,
    SubThemeCreateRequest, SubThemeUpdateRequest
)
from course_selection_api.lib.auth_library.simple_token import SimpleTokenAuth


class ThemeBusiness:
    """主題業務邏輯類"""

    @staticmethod
    async def create_theme(conn, request: ThemeCreateRequest) -> Dict[str, Any]:
        """創建新主題"""
        try:
            # 驗證 token
            SimpleTokenAuth.verify_token(request.token, request.user_id)
            
            # 檢查主題代碼是否已存在
            existing_theme = await ThemeDAO.get_theme_by_code(conn, request.theme_code)
            if existing_theme:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"主題代碼 '{request.theme_code}' 已存在"
                )

            # 創建主題
            theme = await ThemeDAO.create_theme(
                conn,
                theme_code=request.theme_code,
                theme_name=request.theme_name,
                theme_short_name=request.theme_short_name,
                theme_english_name=request.theme_english_name,
                chinese_link=request.chinese_link,
                english_link=request.english_link,
                created_by=request.user_id
            )

            return {
                "id": theme["id"],
                "theme_code": theme["theme_code"],
                "theme_name": theme["theme_name"],
                "message": "主題創建成功"
            }

        except oracledb.IntegrityError as e:
            error_str = str(e)
            if 'ORA-00001' in error_str or 'unique constraint' in error_str.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"主題代碼 '{request.theme_code}' 已存在"
                )
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"創建主題失敗: {str(e)}"
            )

    @staticmethod
    async def get_all_themes(conn) -> Dict[str, Any]:
        """獲取所有主題"""
        try:
            themes = await ThemeDAO.get_all_themes(conn)
            
            theme_list = []
            for theme in themes:
                if not theme:
                    continue
                theme_list.append({
                    "id": theme.get("id"),
                    "theme_code": theme.get("theme_code"),
                    "theme_name": theme.get("theme_name"),
                    "theme_short_name": theme.get("theme_short_name"),
                    "theme_english_name": theme.get("theme_english_name"),
                    "chinese_link": theme.get("chinese_link"),
                    "english_link": theme.get("english_link"),
                    "created_at": str(theme["created_at"]) if theme.get("created_at") else None,
                    "updated_at": str(theme["updated_at"]) if theme.get("updated_at") else None,
                    "created_by": theme.get("created_by"),
                    "updated_by": theme.get("updated_by")
                })

            return {"themes": theme_list}

        except KeyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"獲取主題列表失敗: 缺少必要的欄位 {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"獲取主題列表失敗: {str(e)}"
            )

    @staticmethod
    async def update_theme(conn, theme_id: str, request: ThemeUpdateRequest) -> Dict[str, Any]:
        """更新主題（通過 ID）"""
        try:
            # 驗證 token
            SimpleTokenAuth.verify_token(request.token, request.user_id)
            
            # 檢查主題是否存在
            existing_theme = await ThemeDAO.get_theme_by_id(conn, theme_id)
            if not existing_theme:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"主題ID '{theme_id}' 不存在"
                )

            # 更新主題（允許更新 theme_code）
            updated_theme = await ThemeDAO.update_theme(
                conn,
                theme_id=theme_id,
                theme_code=request.theme_code if hasattr(request, 'theme_code') and request.theme_code else None,
                theme_name=request.theme_name,
                theme_short_name=request.theme_short_name,
                theme_english_name=request.theme_english_name,
                chinese_link=request.chinese_link,
                english_link=request.english_link,
                updated_by=request.user_id
            )

            return {
                "id": updated_theme["id"],
                "theme_code": updated_theme["theme_code"],
                "theme_name": updated_theme["theme_name"],
                "message": "主題更新成功"
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新主題失敗: {str(e)}"
            )

    @staticmethod
    async def delete_theme(conn, theme_id: str, request) -> Dict[str, Any]:
        """刪除主題（通過 ID）"""
        try:
            # 驗證 token
            SimpleTokenAuth.verify_token(request.token, request.user_id)
            
            # 檢查主題是否存在
            existing_theme = await ThemeDAO.get_theme_by_id(conn, theme_id)
            if not existing_theme:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"主題ID '{theme_id}' 不存在"
                )

            # 檢查是否有相關的細項主題
            has_sub_themes = await ThemeDAO.check_theme_has_sub_themes(conn, theme_id)
            if has_sub_themes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"主題 '{existing_theme.get('theme_code', theme_id)}' 已有相關細項主題，無法刪除"
                )

            # 刪除主題
            deleted_theme = await ThemeDAO.delete_theme(conn, theme_id)
            if not deleted_theme:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"主題ID '{theme_id}' 不存在"
                )

            return {
                "id": deleted_theme["id"],
                "theme_code": deleted_theme["theme_code"],
                "message": "主題刪除成功"
            }

        except HTTPException:
            raise
        except oracledb.IntegrityError as e:
            error_str = str(e)
            if 'ORA-02291' in error_str or 'ORA-02292' in error_str or 'foreign key constraint' in error_str.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"主題已有相關細項主題，無法刪除"
                )
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"刪除主題失敗: {str(e)}"
            )


class SubThemeBusiness:
    """細項主題業務邏輯類"""

    @staticmethod
    async def create_sub_theme(conn, request: SubThemeCreateRequest) -> Dict[str, Any]:
        """創建新細項主題"""
        try:
            # 驗證 token
            SimpleTokenAuth.verify_token(request.token, request.user_id)
            
            # 檢查主題ID是否存在
            theme_exists = await ThemeDAO.get_theme_by_id(conn, request.coures_themes_id)
            if not theme_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"主題ID '{request.coures_themes_id}' 不存在"
                )

            # 檢查細項主題代碼是否已存在（在同一主題下）
            existing_sub_themes = await SubThemeDAO.get_sub_themes_by_theme_id(conn, request.coures_themes_id)
            for existing_sub_theme in existing_sub_themes:
                if existing_sub_theme['sub_theme_code'] == request.sub_theme_code:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"細項主題代碼 '{request.sub_theme_code}' 在該主題下已存在"
                    )

            # 創建細項主題
            sub_theme = await SubThemeDAO.create_sub_theme(
                conn,
                coures_themes_id=request.coures_themes_id,
                sub_theme_code=request.sub_theme_code,
                sub_theme_name=request.sub_theme_name,
                sub_theme_english_name=request.sub_theme_english_name,
                sub_theme_content=request.sub_theme_content,
                sub_theme_english_content=request.sub_theme_english_content,
                created_by=request.user_id
            )

            return {
                "id": sub_theme["id"],
                "theme_code": sub_theme["theme_code"],
                "sub_theme_code": sub_theme["sub_theme_code"],
                "sub_theme_name": sub_theme["sub_theme_name"],
                "message": "細項主題創建成功"
            }

        except HTTPException:
            raise
        except oracledb.IntegrityError as e:
            error_str = str(e)
            if 'ORA-00001' in error_str or 'unique constraint' in error_str.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"細項主題代碼 '{request.sub_theme_code}' 已存在"
                )
            elif 'ORA-02291' in error_str or 'ORA-02292' in error_str or 'foreign key constraint' in error_str.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"主題ID '{request.coures_themes_id}' 不存在"
                )
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"創建細項主題失敗: {str(e)}"
            )

    @staticmethod
    async def get_all_sub_themes(conn) -> Dict[str, Any]:
        """獲取所有細項主題列表"""
        try:
            sub_themes = await SubThemeDAO.get_all_sub_themes(conn)
            
            sub_theme_list = []
            for sub_theme in sub_themes:
                sub_theme_list.append({
                    "id": sub_theme["id"],
                    "coures_themes_id": sub_theme["coures_themes_id"],
                    "theme_code": sub_theme["theme_code"],
                    "sub_theme_code": sub_theme["sub_theme_code"],
                    "sub_theme_name": sub_theme["sub_theme_name"],
                    "sub_theme_english_name": sub_theme["sub_theme_english_name"],
                    "sub_theme_content": sub_theme["sub_theme_content"],
                    "sub_theme_english_content": sub_theme["sub_theme_english_content"],
                    "created_at": str(sub_theme["created_at"]) if sub_theme["created_at"] else None,
                    "updated_at": str(sub_theme["updated_at"]) if sub_theme["updated_at"] else None,
                    "created_by": sub_theme["created_by"],
                    "updated_by": sub_theme["updated_by"]
                })

            return {"sub_themes": sub_theme_list}

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"獲取細項主題列表失敗: {str(e)}"
            )

    @staticmethod
    async def get_sub_themes_by_theme_code(conn, theme_code: str) -> Dict[str, Any]:
        """根據主題代碼獲取細項主題列表"""
        try:
            sub_themes = await SubThemeDAO.get_sub_themes_by_theme_code(conn, theme_code)
            
            sub_theme_list = []
            for sub_theme in sub_themes:
                sub_theme_list.append({
                    "id": sub_theme["id"],
                    "coures_themes_id": sub_theme["coures_themes_id"],
                    "theme_code": sub_theme["theme_code"],
                    "sub_theme_code": sub_theme["sub_theme_code"],
                    "sub_theme_name": sub_theme["sub_theme_name"],
                    "sub_theme_english_name": sub_theme["sub_theme_english_name"],
                    "sub_theme_content": sub_theme["sub_theme_content"],
                    "sub_theme_english_content": sub_theme["sub_theme_english_content"],
                    "created_at": str(sub_theme["created_at"]) if sub_theme["created_at"] else None,
                    "updated_at": str(sub_theme["updated_at"]) if sub_theme["updated_at"] else None,
                    "created_by": sub_theme["created_by"],
                    "updated_by": sub_theme["updated_by"]
                })

            return {"sub_themes": sub_theme_list}

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"獲取細項主題列表失敗: {str(e)}"
            )

    @staticmethod
    async def update_sub_theme(conn, sub_theme_id: str, request: SubThemeUpdateRequest) -> Dict[str, Any]:
        """更新細項主題（通過 ID）"""
        try:
            # 驗證 token
            SimpleTokenAuth.verify_token(request.token, request.user_id)
            
            # 檢查細項主題是否存在
            existing_sub_theme = await SubThemeDAO.get_sub_theme_by_id(conn, sub_theme_id)
            if not existing_sub_theme:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"細項主題ID '{sub_theme_id}' 不存在"
                )

            # 如果要更新主題ID，檢查新的主題ID是否存在
            coures_themes_id = existing_sub_theme['coures_themes_id']
            if request.coures_themes_id and request.coures_themes_id != existing_sub_theme['coures_themes_id']:
                new_theme = await ThemeDAO.get_theme_by_id(conn, request.coures_themes_id)
                if not new_theme:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"主題ID '{request.coures_themes_id}' 不存在"
                    )
                coures_themes_id = request.coures_themes_id

            # 更新細項主題
            updated_sub_theme = await SubThemeDAO.update_sub_theme(
                conn,
                sub_theme_id=sub_theme_id,
                coures_themes_id=coures_themes_id,
                sub_theme_code=request.sub_theme_code if hasattr(request, 'sub_theme_code') and request.sub_theme_code else None,
                sub_theme_name=request.sub_theme_name,
                sub_theme_english_name=request.sub_theme_english_name,
                sub_theme_content=request.sub_theme_content,
                sub_theme_english_content=request.sub_theme_english_content,
                updated_by=request.user_id
            )

            return {
                "id": updated_sub_theme["id"],
                "theme_code": updated_sub_theme["theme_code"],
                "sub_theme_code": updated_sub_theme["sub_theme_code"],
                "sub_theme_name": updated_sub_theme["sub_theme_name"],
                "message": "細項主題更新成功"
            }

        except HTTPException:
            raise
        except oracledb.IntegrityError as e:
            error_str = str(e)
            if 'ORA-02291' in error_str or 'ORA-02292' in error_str or 'foreign key constraint' in error_str.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"主題代碼不存在"
                )
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新細項主題失敗: {str(e)}"
            )

    @staticmethod
    async def delete_sub_theme(conn, sub_theme_id: str, request) -> Dict[str, Any]:
        """刪除細項主題（通過 ID）"""
        try:
            # 驗證 token
            SimpleTokenAuth.verify_token(request.token, request.user_id)
            
            # 檢查細項主題是否存在
            existing_sub_theme = await SubThemeDAO.get_sub_theme_by_id(conn, sub_theme_id)
            if not existing_sub_theme:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"細項主題ID '{sub_theme_id}' 不存在"
                )

            # 檢查是否已有填寫相關資料
            has_data = await SubThemeDAO.check_sub_theme_has_data(conn, sub_theme_id)
            if has_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"細項主題 '{existing_sub_theme.get('sub_theme_code', sub_theme_id)}' 已有課程使用，無法刪除"
                )

            # 刪除細項主題
            deleted_sub_theme = await SubThemeDAO.delete_sub_theme(conn, sub_theme_id)
            if not deleted_sub_theme:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"細項主題ID '{sub_theme_id}' 不存在"
                )

            return {
                "id": deleted_sub_theme["id"],
                "sub_theme_code": deleted_sub_theme["sub_theme_code"],
                "message": "細項主題刪除成功"
            }

        except HTTPException:
            raise
        except oracledb.IntegrityError as e:
            error_str = str(e)
            if 'ORA-02291' in error_str or 'ORA-02292' in error_str or 'foreign key constraint' in error_str.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"細項主題已有課程使用，無法刪除"
                )
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"刪除細項主題失敗: {str(e)}"
            )
