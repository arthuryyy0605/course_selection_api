from typing import Dict, Any, List
import json
import csv
import io
from fastapi import HTTPException, status
from course_selection_api.data_access_object.school_year_settings_dao import (
    SchoolYearDAO, 
    CourseEntriesDAO,
    SchoolYearThemeSettingsDAO
)
from course_selection_api.lib.auth_library.simple_token import SimpleTokenAuth
from collections import defaultdict


class SchoolYearBusiness:
    """學年期業務邏輯"""

    @staticmethod
    def _format_course_entry_result(result: Dict) -> Dict:
        """格式化課程填寫記錄結果"""
        result_dict = dict(result)
        # 格式化時間欄位
        if 'created_at' in result_dict and result_dict['created_at']:
            result_dict['created_at'] = result_dict['created_at'].isoformat()
        if 'updated_at' in result_dict and result_dict['updated_at']:
            result_dict['updated_at'] = result_dict['updated_at'].isoformat()
        # 格式化 week_numbers JSON
        if 'week_numbers' in result_dict and result_dict['week_numbers']:
            if isinstance(result_dict['week_numbers'], str):
                result_dict['week_numbers'] = json.loads(result_dict['week_numbers'])
        # 轉換 is_most_relevant 為 boolean（如果尚未轉換）
        if 'is_most_relevant' in result_dict:
            if isinstance(result_dict['is_most_relevant'], str):
                result_dict['is_most_relevant'] = result_dict['is_most_relevant'] == 'Y'
        return result_dict

    @staticmethod
    async def get_school_year_complete_info(conn, academic_year: int, academic_term: int) -> Dict[str, Any]:
        """獲取學年期完整資訊"""
        # 獲取原始資料
        raw_data = await SchoolYearDAO.get_school_year_complete_info(conn, academic_year, academic_term)
        
        if not raw_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"學年 {academic_year} 學期 {academic_term} 沒有找到相關設定"
            )
        
        # 整理數據結構
        themes_dict = defaultdict(lambda: {
            'theme_id': '',
            'theme_code': '',
            'theme_name': '',
            'theme_short_name': '',
            'theme_english_name': '',
            'fill_in_week_enabled': False,
            'scale_max': 0,
            'select_most_relevant_sub_theme_enabled': False,
            'sub_themes': []
        })
        
        for row in raw_data:
            theme_code = row['theme_code']
            
            # 設定主題基本資訊
            if not themes_dict[theme_code]['theme_code']:
                themes_dict[theme_code].update({
                    'theme_id': row.get('theme_id', ''),
                    'theme_code': row['theme_code'],
                    'theme_name': row['theme_name'],
                    'theme_short_name': row['theme_short_name'],
                    'theme_english_name': row['theme_english_name'],
                    'fill_in_week_enabled': row['fill_in_week_enabled'],
                    'scale_max': row['scale_max'],
                    'select_most_relevant_sub_theme_enabled': row.get('select_most_relevant_sub_theme_enabled', False)
                })
            
            # 添加細項主題資訊（包含 enabled 狀態）
            if row.get('sub_theme_code'):
                sub_theme_info = {
                    'sub_theme_id': row.get('sub_theme_id', ''),
                    'sub_theme_code': row['sub_theme_code'],
                    'sub_theme_name': row['sub_theme_name'],
                    'sub_theme_english_name': row['sub_theme_english_name'],
                    'sub_theme_content': row.get('sub_theme_content'),
                    'sub_theme_english_content': row.get('sub_theme_english_content'),
                    'enabled': row.get('enabled', False)  # 添加啟用狀態
                }
                
                # 避免重複添加
                existing_codes = [st['sub_theme_code'] for st in themes_dict[theme_code]['sub_themes']]
                if row['sub_theme_code'] not in existing_codes:
                    themes_dict[theme_code]['sub_themes'].append(sub_theme_info)
        
        # 轉換為列表格式
        themes_list = []
        for theme_code in sorted(themes_dict.keys()):
            theme_data = themes_dict[theme_code]
            # 排序細項主題
            theme_data['sub_themes'].sort(key=lambda x: x['sub_theme_code'])
            themes_list.append(theme_data)
        
        # 計算摘要統計
        total_themes = len(themes_list)
        total_sub_themes = sum(len(theme['sub_themes']) for theme in themes_list)
        enabled_sub_themes = sum(
            sum(1 for st in theme['sub_themes'] if st.get('enabled', False))
            for theme in themes_list
        )
        
        # 生成主題摘要
        themes_summary = [
            {
                'theme_code': theme['theme_code'],
                'theme_name': theme['theme_name'],
                'scale_max': theme['scale_max'],
                'sub_themes_count': len(theme['sub_themes']),
                'enabled_sub_themes_count': sum(1 for st in theme['sub_themes'] if st.get('enabled', False))
            }
            for theme in themes_list
        ]
        
        return {
            'academic_year': academic_year,
            'academic_term': academic_term,
            'summary': {
                'total_themes': total_themes,
                'total_sub_themes': total_sub_themes,
                'enabled_sub_themes': enabled_sub_themes
            },
            'themes_summary': themes_summary,
            'themes': themes_list
        }

    @staticmethod
    async def create_course_entry(conn, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """創建課程填寫記錄"""
        # 驗證 token
        SimpleTokenAuth.verify_token(entry_data['token'], entry_data['user_id'])
        
        subj_no = entry_data['subj_no']
        ps_class_nbr = entry_data['ps_class_nbr']
        academic_year = entry_data['academic_year']
        academic_term = entry_data['academic_term']
        sub_theme_code = entry_data['sub_theme_code']
        is_most_relevant = entry_data.get('is_most_relevant', False)
        
        # 移除 is_most_relevant 驗證邏輯，改由前端判斷
        
        try:
            result = await CourseEntriesDAO.create_course_entry(
                conn,
                subj_no,
                ps_class_nbr,
                academic_year,
                academic_term,
                sub_theme_code,
                entry_data['indicator_value'],
                entry_data.get('week_numbers'),
                is_most_relevant,
                created_by=entry_data['user_id']
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="課程填寫記錄創建失敗"
            )
        
        return SchoolYearBusiness._format_course_entry_result(result)

    @staticmethod
    async def create_course_entries_batch(conn, entries_data: list[dict[str, Any]], user_id: str, token: str) -> List[Dict[str, Any]]:
        """批量創建課程填寫記錄"""
        # 驗證 token
        SimpleTokenAuth.verify_token(token, user_id)
        
        # 移除批量驗證最相關科目邏輯，改由前端判斷
        
        # 為每個 entry 加入 created_by
        entries_with_user = []
        for entry in entries_data:
            entry_copy = entry.copy()
            entry_copy['created_by'] = user_id
            entries_with_user.append(entry_copy)
        
        results = await CourseEntriesDAO.create_course_entries_batch(conn, entries_with_user)
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="批量創建課程填寫記錄失敗"
            )
        
        # 格式化所有結果
        formatted_results = [SchoolYearBusiness._format_course_entry_result(result) for result in results]
        return formatted_results

    @staticmethod
    async def update_course_entry(conn, subj_no: str, ps_class_nbr: str, academic_year: int, academic_term: int, sub_theme_code: str, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新課程填寫記錄"""
        # 驗證 token
        SimpleTokenAuth.verify_token(entry_data['token'], entry_data['user_id'])
        
        is_most_relevant = entry_data.get('is_most_relevant')
        
        # 移除 is_most_relevant 驗證邏輯，改由前端判斷
        
        result = await CourseEntriesDAO.update_course_entry(
            conn,
            subj_no,
            ps_class_nbr,
            academic_year,
            academic_term,
            sub_theme_code,
            entry_data['indicator_value'],
            entry_data.get('week_numbers'),
            is_most_relevant,
            updated_by=entry_data['user_id']
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="課程填寫記錄不存在或更新失敗"
            )
        
        return SchoolYearBusiness._format_course_entry_result(result)

    @staticmethod
    async def update_course_entry_by_id(conn, entry_id: int, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """根據 ID 更新課程填寫記錄"""
        # 驗證 token
        SimpleTokenAuth.verify_token(entry_data['token'], entry_data['user_id'])
        
        is_most_relevant = entry_data.get('is_most_relevant')
        
        # 如果更新 is_most_relevant，需要驗證
        if is_most_relevant is not None:
            # 先取得現有記錄
            existing_entry = await CourseEntriesDAO.get_course_entry_by_id(conn, entry_id)
            if existing_entry:
                subj_no = existing_entry['subj_no']
                ps_class_nbr = existing_entry['ps_class_nbr']
                academic_year = existing_entry['academic_year']
                academic_term = existing_entry['academic_term']
                sub_theme_code = existing_entry['sub_theme_code']
                theme_code = existing_entry['theme_code']
                
                if is_most_relevant:
                    # 如果設定為最相關，驗證該課程在該主題下沒有其他 is_most_relevant='Y' 的記錄
                    has_existing = await CourseEntriesDAO.check_most_relevant_validation(
                        conn, subj_no, ps_class_nbr, academic_year, academic_term, theme_code, exclude_sub_theme_code=sub_theme_code
                    )
                    if has_existing:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"該課程在主題 '{theme_code}' 下已有其他最相關的 sub_theme，每個主題只能有一個最相關的 sub_theme"
                        )
        
        result = await CourseEntriesDAO.update_course_entry_by_id(
            conn,
            entry_id,
            entry_data['indicator_value'],
            entry_data.get('week_numbers'),
            is_most_relevant,
            updated_by=entry_data['user_id']
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="課程填寫記錄不存在或更新失敗"
            )
        
        return SchoolYearBusiness._format_course_entry_result(result)

    @staticmethod
    async def delete_course_entry(conn, subj_no: str, ps_class_nbr: str, academic_year: int, academic_term: int, sub_theme_code: str, delete_data: Dict[str, Any]) -> Dict[str, Any]:
        """刪除課程填寫記錄"""
        # 驗證 token
        SimpleTokenAuth.verify_token(delete_data['token'], delete_data['user_id'])
        
        result = await CourseEntriesDAO.delete_course_entry(conn, subj_no, ps_class_nbr, academic_year, academic_term, sub_theme_code)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="課程填寫記錄不存在或刪除失敗"
            )
        
        return SchoolYearBusiness._format_course_entry_result(result)

    @staticmethod
    async def delete_course_entry_by_id(conn, entry_id: int, delete_data: Dict[str, Any]) -> Dict[str, Any]:
        """根據 ID 刪除課程填寫記錄"""
        # 驗證 token
        SimpleTokenAuth.verify_token(delete_data['token'], delete_data['user_id'])
        
        result = await CourseEntriesDAO.delete_course_entry_by_id(conn, entry_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="課程填寫記錄不存在或刪除失敗"
            )
        
        return SchoolYearBusiness._format_course_entry_result(result)

    @staticmethod
    async def get_teacher_form_data(conn, subj_no: str, ps_class_nbr: str, academic_year: int, academic_term: int) -> Dict[str, Any]:
        """
        獲取教師表單數據
        使用 subj_no, ps_class_nbr, academic_year, academic_term 參數，直接從 course_entries 表和 COFSUBJ 取得資料
        """
        result = await CourseEntriesDAO.get_teacher_form_data(conn, subj_no, ps_class_nbr, academic_year, academic_term)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"課程 '{subj_no}' 在學年期 {academic_year}-{academic_term} 沒有找到相關設定或課程不存在"
            )
        
        # 從第一筆資料取得課程基本資訊和學年期
        # 如果查詢結果中沒有這些值（因為沒有 course_entries 記錄），使用參數值或預設值
        first_row = result[0]
        course_chinese_name = first_row.get('course_chinese_name') if first_row.get('course_chinese_name') is not None else ''
        course_english_name = first_row.get('course_english_name') if first_row.get('course_english_name') is not None else ''
        # 如果查詢結果中沒有 academic_year 或 academic_term，使用傳入的參數值
        academic_year = first_row.get('academic_year') if first_row.get('academic_year') is not None else academic_year
        academic_term = first_row.get('academic_term') if first_row.get('academic_term') is not None else academic_term
        
        # 整理數據結構，按主題分組
        themes_dict = defaultdict(lambda: {
            'theme_id': '',
            'theme_code': '',
            'theme_name': '',
            'theme_short_name': '',
            'theme_english_name': '',
            'fill_in_week_enabled': False,
            'scale_max': 0,
            'select_most_relevant_sub_theme_enabled': False,
            'sub_themes': []
        })
        
        for row in result:
            theme_code = row['theme_code']
            
            # 設定主題基本資訊
            if not themes_dict[theme_code]['theme_code']:
                themes_dict[theme_code].update({
                    'theme_id': row.get('theme_id', ''),
                    'theme_code': row['theme_code'],
                    'theme_name': row['theme_name'],
                    'theme_short_name': row['theme_short_name'],
                    'theme_english_name': row['theme_english_name'],
                    'fill_in_week_enabled': row['fill_in_week_enabled'],
                    'scale_max': row['scale_max'],
                    'select_most_relevant_sub_theme_enabled': row.get('select_most_relevant_sub_theme_enabled', False)
                })
            
            # 添加細項主題資訊
            if row.get('sub_theme_code'):
                # 處理 week_numbers JSON 數據
                week_numbers = row.get('week_numbers')
                if week_numbers and isinstance(week_numbers, str):
                    week_numbers = json.loads(week_numbers)
                
                # 處理 is_most_relevant
                is_most_relevant = row.get('is_most_relevant', False)
                if isinstance(is_most_relevant, str):
                    is_most_relevant = is_most_relevant == 'Y'
                
                sub_theme_info = {
                    'sub_theme_id': row.get('sub_theme_id', ''),
                    'sub_theme_code': row['sub_theme_code'],
                    'sub_theme_name': row['sub_theme_name'],
                    'sub_theme_english_name': row['sub_theme_english_name'],
                    'sub_theme_content': row.get('sub_theme_content'),
                    'sub_theme_english_content': row.get('sub_theme_english_content'),
                    'current_value': row.get('indicator_value'),
                    'week_numbers': week_numbers,
                    'is_most_relevant': is_most_relevant,
                    'entry_id': row.get('entry_id')
                }
                
                # 避免重複添加
                existing_codes = [st['sub_theme_code'] for st in themes_dict[theme_code]['sub_themes']]
                if row['sub_theme_code'] not in existing_codes:
                    themes_dict[theme_code]['sub_themes'].append(sub_theme_info)
        
        # 轉換為列表格式
        themes_list = []
        for theme_code in sorted(themes_dict.keys()):
            theme_data = themes_dict[theme_code]
            # 排序細項主題
            theme_data['sub_themes'].sort(key=lambda x: x['sub_theme_code'])
            themes_list.append(theme_data)
        
        return {
            'course_id': subj_no,  # API 回傳為 course_id
            'ps_class_nbr': ps_class_nbr,
            'course_chinese_name': course_chinese_name,
            'course_english_name': course_english_name,
            'academic_year': academic_year,
            'academic_term': academic_term,
            'themes': themes_list
        }

    @staticmethod
    async def get_courses_by_sub_theme(conn, academic_year: int, academic_term: int, theme_code: str, 
                                      sub_theme_code: str) -> List[str]:
        """獲取已填寫指定細項的課程列表"""
        results = await CourseEntriesDAO.get_courses_by_sub_theme(
            conn, academic_year, academic_term, theme_code, sub_theme_code
        )
        course_ids = [row['course_id'] for row in results]
        return course_ids

    @staticmethod
    async def check_course_entries_exist(conn, subj_no: str, ps_class_nbr: str, academic_year: int, academic_term: int) -> bool:
        """檢查指定課程是否有填寫記錄"""
        exists = await CourseEntriesDAO.check_course_entries_exist(conn, subj_no, ps_class_nbr, academic_year, academic_term)
        return exists

    @staticmethod
    async def copy_course_entries(conn, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        複製課程記錄到新學年期
        注意：由於 course_entries 不再存儲學年期，此功能需要重新設計
        這裡提供簡化版本
        """
        # 驗證 token
        SimpleTokenAuth.verify_token(data['token'], data['user_id'])
        
        subj_no = data['subj_no']
        source_academic_year = data['source_academic_year']
        source_academic_term = data['source_academic_term']
        target_academic_year = data['target_academic_year']
        target_academic_term = data['target_academic_term']
        user_id = data['user_id']
        
        try:
            # 1. 檢查來源課程是否有資料
            ps_class_nbr = data.get('ps_class_nbr', '')
            source_entries = await CourseEntriesDAO.get_course_entries_by_subj_no(conn, subj_no, ps_class_nbr, source_academic_year, source_academic_term)
            
            if not source_entries:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"課程 {subj_no} 在學年期 {source_academic_year}-{source_academic_term} 沒有填寫記錄"
                )
            
            # 2. 取得目標學年期啟用的 theme/sub_theme 設定
            target_enabled_settings = await CourseEntriesDAO.get_enabled_theme_sub_themes(
                conn, target_academic_year, target_academic_term
            )
            
            if not target_enabled_settings:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"目標學年 {target_academic_year} 學期 {target_academic_term} 沒有啟用的主題設定"
                )
            
            # 建立啟用設定的集合
            enabled_set = {
                (row['theme_code'], row['sub_theme_code']) 
                for row in target_enabled_settings
            }
            
            # 3. 過濾來源資料並複製
            skipped_count = 0
            copied_count = 0
            deleted_count = 0
            
            # 先刪除目標學年期的現有記錄（如果存在）
            existing_target_entries = await CourseEntriesDAO.get_course_entries_by_subj_no(
                conn, subj_no, ps_class_nbr, target_academic_year, target_academic_term
            )
            if existing_target_entries:
                deleted_count = len(existing_target_entries)
                for entry in existing_target_entries:
                    await CourseEntriesDAO.delete_course_entry(
                        conn, subj_no, ps_class_nbr, target_academic_year, target_academic_term, entry['sub_theme_code']
                    )
            
            # 複製記錄
            for entry in source_entries:
                theme_sub_key = (entry['theme_code'], entry['sub_theme_code'])
                if theme_sub_key in enabled_set:
                    # 可以複製（目標學年期也有此設定）
                    week_numbers_json = None
                    if entry.get('week_numbers'):
                        if isinstance(entry['week_numbers'], list):
                            week_numbers_json = json.dumps(entry['week_numbers'])
                        else:
                            week_numbers_json = entry['week_numbers']
                    
                    is_most_relevant = entry.get('is_most_relevant', False)
                    if isinstance(is_most_relevant, str):
                        is_most_relevant = bool(is_most_relevant)
                    
                    await CourseEntriesDAO.copy_course_entry_with_new_user(
                        conn,
                        subj_no,
                        ps_class_nbr,
                        target_academic_year,
                        target_academic_term,
                        entry['sub_theme_code'],
                        entry['indicator_value'],
                        week_numbers_json,
                        is_most_relevant,
                        user_id
                    )
                    copied_count += 1
                else:
                    skipped_count += 1
            
            return {
                "message": f"成功複製 {copied_count} 筆記錄到學年期 {target_academic_year}-{target_academic_term}",
                "copied_count": copied_count,
                "skipped_count": skipped_count,
                "deleted_count": deleted_count
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"複製課程記錄失敗: {str(e)}"
            )

    @staticmethod
    async def export_course_entries_to_csv(conn, academic_year: int, academic_term: int) -> str:
        """匯出指定學年期的課程資料為 CSV 格式"""
        # 1. 查詢該學年期的主題設定
        theme_settings = await SchoolYearThemeSettingsDAO.get_school_year_theme_settings_by_year(
            conn, academic_year, academic_term
        )
        
        if not theme_settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"學年 {academic_year} 學期 {academic_term} 沒有找到主題設定"
            )
        
        # 2. 查詢所有課程和課程填寫記錄
        all_entries = await CourseEntriesDAO.get_all_course_entries_by_academic_year_term(
            conn, academic_year, academic_term
        )
        
        # 3. 組織資料：按課程分組
        courses_dict = defaultdict(lambda: {
            'subj_no': '',
            'ps_class_nbr': '',
            'course_chinese_name': '',
            'entries_by_sub_theme': {}
        })
        
        for entry in all_entries:
            course_key = (entry['subj_no'], entry['ps_class_nbr'])
            courses_dict[course_key]['subj_no'] = entry['subj_no']
            courses_dict[course_key]['ps_class_nbr'] = entry['ps_class_nbr']
            # 取得課程中文名稱（如果有的話）
            if entry.get('course_chinese_name'):
                courses_dict[course_key]['course_chinese_name'] = entry['course_chinese_name']
            courses_dict[course_key]['entries_by_sub_theme'][entry['sub_theme_code']] = entry
        
        # 4. 建立 CSV 欄位結構
        # 基本欄位
        csv_columns = ['學年期', 'OPMS_COURSE_NO', 'PS_CLASS_NBR', '課程名稱']
        
        # 週次欄位映射（子主題代碼 -> 週次欄位名稱）
        week_column_map = {}
        
        # 主題欄位結構：{theme_code: [column_info, ...]}
        theme_columns = {}
        
        # SDGs 子主題名稱映射（用於生成欄位名稱）
        sdgs_number_map = {
            '01': '1.消除貧窮', '02': '2.消除飢餓', '03': '3.健康與福祉',
            '04': '4.教育品質', '05': '5.性別平等', '06': '6.淨水與衛生',
            '07': '7.可負擔能源', '08': '8.就業與經濟成長', '09': '9.工業、創新基礎建設',
            '10': '10.減少不平等', '11': '11.永續城市', '12': '12.責任消費與生產',
            '13': '13.氣候行動', '14': '14.海洋生態', '15': '15.陸地生態',
            '16': '16.和平與正義制度', '17': '17.全球夥伴'
        }
        
        # 週次欄位名稱映射（根據 import_course_data_from_csv.py 的映射）
        week_name_map = {
            ('A301', '1020'): '實作週次',
            ('A301', '1080'): '人文關懷週次',
            ('A301', '1120'): '媒體識讀或資訊判讀週次',
            ('A301', '1130'): '媒體識讀或資訊判讀週次',
            ('A401', '1010'): '資訊科技週次',
            ('A501', '1010'): '在地關懷週次',
        }
        
        # 按主題順序處理（A101 -> A301 -> A401 -> A501 -> A601）
        theme_order = ['A101', 'A301', 'A401', 'A501', 'A601']
        
        for theme_code in theme_order:
            theme_setting = next((ts for ts in theme_settings if ts['theme_code'] == theme_code), None)
            if not theme_setting:
                continue
            
            theme_columns[theme_code] = []
            
            # 如果主題需要最相關子主題欄位（分為代碼和名稱兩個欄位）
            if theme_setting.get('select_most_relevant_sub_theme_enabled', False):
                theme_name = theme_setting.get('theme_name', '')
                most_relevant_code_col = f"{theme_name}最相關子主題代碼"
                most_relevant_name_col = f"{theme_name}最相關子主題名稱"
                csv_columns.append(most_relevant_code_col)
                csv_columns.append(most_relevant_name_col)
                theme_columns[theme_code].append({
                    'type': 'most_relevant_code',
                    'column_name': most_relevant_code_col
                })
                theme_columns[theme_code].append({
                    'type': 'most_relevant_name',
                    'column_name': most_relevant_name_col
                })
            
            # 處理每個啟用的子主題
            for sub_theme in theme_setting.get('sub_themes', []):
                if not sub_theme.get('enabled', False):
                    continue
                
                sub_theme_code = sub_theme['sub_theme_code']
                sub_theme_name = sub_theme['sub_theme_name']
                
                # 生成欄位名稱
                if theme_code == 'A101':
                    # SDGs 使用數字前綴格式
                    column_name = sdgs_number_map.get(sub_theme_code, sub_theme_name)
                elif theme_code == 'A401':
                    # UCAN 使用 UCAN 前綴
                    if sub_theme_name != '資訊科技':
                        column_name = f"UCAN{sub_theme_name}"
                    else:
                        column_name = '資訊科技(UCAN)'
                elif theme_code == 'A501':
                    # USR 使用 (USR) 後綴
                    column_name = f"{sub_theme_name}(USR)"
                elif theme_code == 'A601':
                    # STEAM 使用 STEAM 前綴
                    column_name = f"STEAM{sub_theme_name}"
                else:
                    # A301 主題使用 (主題:指標主題) 後綴
                    column_name = f"{sub_theme_name}(主題:指標主題)"
                
                # 添加指標值欄位
                csv_columns.append(column_name)
                theme_columns[theme_code].append({
                    'type': 'indicator',
                    'column_name': column_name,
                    'sub_theme_code': sub_theme_code
                })
                
                # 如果主題需要填寫週次，添加週次欄位
                if theme_setting.get('fill_in_week_enabled', False):
                    # 查找週次欄位名稱
                    week_col_name = week_name_map.get((theme_code, sub_theme_code))
                    if not week_col_name:
                        # 預設使用子主題名稱 + 週次
                        week_col_name = f"{sub_theme_name}週次"
                    
                    # 檢查是否已經添加過這個週次欄位（可能多個子主題共用同一個週次欄位）
                    if week_col_name not in csv_columns:
                        csv_columns.append(week_col_name)
                    
                    week_column_map[sub_theme_code] = week_col_name
                    
                    theme_columns[theme_code].append({
                        'type': 'week',
                        'column_name': week_col_name,
                        'sub_theme_code': sub_theme_code
                    })
        
        # 5. 生成 CSV 內容
        output = io.StringIO()
        # 使用 UTF-8-sig 編碼（帶 BOM）以確保 Excel 能正確開啟
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        
        # 寫入標題行
        writer.writerow(csv_columns)
        
        # 寫入資料行
        year_term_str = f"{academic_year}{academic_term}"
        
        for course_key in sorted(courses_dict.keys()):
            course_data = courses_dict[course_key]
            row = [year_term_str, course_data['subj_no'], course_data['ps_class_nbr'], course_data.get('course_chinese_name', '')]
            
            # 按主題順序填充資料
            for theme_code in theme_order:
                if theme_code not in theme_columns:
                    continue
                
                entries_by_sub_theme = course_data['entries_by_sub_theme']
                
                # 預先查找該主題下最相關的子主題（避免重複查找）
                most_relevant_sub_theme = None
                for entry in entries_by_sub_theme.values():
                    if (entry.get('theme_code') == theme_code and 
                        entry.get('is_most_relevant', False)):
                        most_relevant_sub_theme = entry
                        break
                
                for col_info in theme_columns[theme_code]:
                    if col_info['type'] == 'most_relevant_code':
                        # 添加 sub_theme_code
                        if most_relevant_sub_theme:
                            row.append(most_relevant_sub_theme.get('sub_theme_code', ''))
                        else:
                            row.append('')
                    
                    elif col_info['type'] == 'most_relevant_name':
                        # 添加 sub_theme_name
                        if most_relevant_sub_theme:
                            row.append(most_relevant_sub_theme.get('sub_theme_name', ''))
                        else:
                            row.append('')
                    
                    elif col_info['type'] == 'indicator':
                        sub_theme_code = col_info['sub_theme_code']
                        entry = entries_by_sub_theme.get(sub_theme_code)
                        if entry:
                            row.append(entry.get('indicator_value', ''))
                        else:
                            row.append('')
                    
                    elif col_info['type'] == 'week':
                        sub_theme_code = col_info['sub_theme_code']
                        entry = entries_by_sub_theme.get(sub_theme_code)
                        if entry and entry.get('week_numbers'):
                            week_numbers = entry['week_numbers']
                            if isinstance(week_numbers, list):
                                week_str = ','.join(str(w) for w in week_numbers)
                                row.append(week_str)
                            else:
                                row.append('')
                        else:
                            row.append('')
            
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        # 添加 UTF-8 BOM（用於 Excel 正確顯示中文）
        return '\ufeff' + csv_content

    @staticmethod
    async def export_course_entries_to_csv_with_filters(
        conn,
        academic_year_start: int,
        academic_term_start: int,
        academic_year_end: int,
        academic_term_end: int,
        department: str = None,
        has_class: str = None,
        theme_code: str = None,
        sub_theme_code: str = None
    ) -> str:
        """
        匯出課程資料為 CSV 格式（支援篩選條件）
        
        匯出欄位包含：
        - 序號、學年期、選課號碼、開課系所、科目內碼、課程名稱
        - 學分、選課人數、開課人數、成班與否
        - 必選修、全/半年、是否合班、授課群、英文EMI、課程含自主學習
        - 主題勾選欄位（主題簡稱-細項主題名稱）
        """
        # 1. 從 COFOPMS 查詢課程基本資料
        courses = await CourseEntriesDAO.get_courses_from_cofopms_with_filters(
            conn,
            academic_year_start, academic_term_start,
            academic_year_end, academic_term_end,
            department, has_class, theme_code, sub_theme_code
        )
        
        if not courses:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="沒有找到符合條件的課程資料"
            )
        
        # 2. 查詢學年期範圍內的主題設定（取第一個學年期的設定作為欄位結構）
        theme_settings = await SchoolYearThemeSettingsDAO.get_school_year_theme_settings_by_year(
            conn, academic_year_start, academic_term_start
        )
        
        if not theme_settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"學年 {academic_year_start} 學期 {academic_term_start} 沒有找到主題設定"
            )
        
        # 3. 查詢課程填寫記錄
        all_entries = await CourseEntriesDAO.get_course_entries_with_filters(
            conn,
            academic_year_start, academic_term_start,
            academic_year_end, academic_term_end,
            theme_code, sub_theme_code
        )
        
        # 按 PS_CLASS_NBR + 學年期分組
        entries_by_course = defaultdict(lambda: defaultdict(dict))
        for entry in all_entries:
            course_key = (entry['ps_class_nbr'], entry['academic_year'], entry['academic_term'])
            entries_by_course[course_key][entry['sub_theme_code']] = entry
        
        # 4. 建立 CSV 欄位結構
        # 基本欄位（來自 COFOPMS）
        csv_columns = [
            '序號',
            '學年期',
            '選課號碼',
            '開課系所',
            '選課系所',
            '科目內碼',
            '課程名稱',
            '教師姓名',
            '實習教師',
            '學分',
            '選課人數',
            '開課人數',
            '成班與否',
            '必選修',
            '全/半年',
            '是否合班',
            '授課群',
            '英文EMI',
            '課程含自主學習'
        ]
        
        # 主題欄位結構
        theme_columns = {}
        theme_order = ['A101', 'A301', 'A401', 'A501', 'A601']
        
        # 必選修別對照
        course_kind_map = {'1': '必修', '2': '選修'}
        # 全/半年對照
        kind_code_map = {'1': '半年', '2': '全年'}
        
        for theme_code_iter in theme_order:
            theme_setting = next((ts for ts in theme_settings if ts['theme_code'] == theme_code_iter), None)
            if not theme_setting:
                continue
            
            # 如果有指定篩選主題，只處理該主題
            if theme_code and theme_code_iter != theme_code:
                continue
            
            theme_columns[theme_code_iter] = []
            theme_short_name = theme_setting.get('theme_short_name', theme_setting.get('theme_name', ''))
            
            # 如果主題需要最相關子主題欄位
            if theme_setting.get('select_most_relevant_sub_theme_enabled', False):
                most_relevant_col = f"{theme_short_name}-最相關"
                csv_columns.append(most_relevant_col)
                theme_columns[theme_code_iter].append({
                    'type': 'most_relevant',
                    'column_name': most_relevant_col
                })
            
            # 處理每個啟用的子主題
            for sub_theme in theme_setting.get('sub_themes', []):
                if not sub_theme.get('enabled', False):
                    continue
                
                # 如果有指定篩選細項主題，只處理該細項
                if sub_theme_code and sub_theme['sub_theme_code'] != sub_theme_code:
                    continue
                
                sub_theme_code_value = sub_theme['sub_theme_code']
                sub_theme_name = sub_theme['sub_theme_name']
                
                # 欄位名稱：主題簡稱-細項主題名稱
                column_name = f"{theme_short_name}-{sub_theme_name}"
                csv_columns.append(column_name)
                theme_columns[theme_code_iter].append({
                    'type': 'indicator',
                    'column_name': column_name,
                    'sub_theme_code': sub_theme_code_value
                })
        
        # 5. 生成 CSV 內容
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        
        # 寫入標題行
        writer.writerow(csv_columns)
        
        # 寫入資料行
        row_num = 1
        for course in courses:
            year_term = f"{course['opms_acadm_year']}{course['opms_acadm_term']}"
            ps_class_nbr = course['ps_class_nbr']
            academic_year = int(course['opms_acadm_year']) if course['opms_acadm_year'] else 0
            academic_term = int(course['opms_acadm_term']) if course['opms_acadm_term'] else 0
            
            # 基本欄位
            row = [
                row_num,  # 序號
                year_term,  # 學年期
                course.get('opms_serial_no', ''),  # 選課號碼
                course.get('dept_name', ''),  # 開課系所
                course.get('dept_name_sel', ''),  # 選課系所
                course.get('opms_course_no', ''),  # 科目內碼
                course.get('course_name', ''),  # 課程名稱
                course.get('teacher_name', ''),  # 教師姓名
                course.get('expr_name', ''),  # 實習教師
                course.get('opms_credit', ''),  # 學分
                course.get('opms_sel_students', ''),  # 選課人數
                course.get('opms_students', ''),  # 開課人數
                course.get('opms_code', ''),  # 成班與否
                course_kind_map.get(course.get('opms_course_kind', ''), course.get('opms_course_kind', '')),  # 必選修
                kind_code_map.get(course.get('opms_kind_code', ''), course.get('opms_kind_code', '')),  # 全/半年
                course.get('opms_class_group', ''),  # 是否合班
                course.get('opms_teacher_group', ''),  # 授課群
                course.get('opms_english_group', ''),  # 英文EMI
                course.get('opms_agree', '')  # 課程含自主學習
            ]
            
            # 主題欄位
            course_key = (ps_class_nbr, academic_year, academic_term)
            course_entries = entries_by_course.get(course_key, {})
            
            for theme_code_iter in theme_order:
                if theme_code_iter not in theme_columns:
                    continue
                
                # 找出該主題的最相關細項
                most_relevant_entry = None
                for entry in course_entries.values():
                    if entry.get('theme_code') == theme_code_iter and entry.get('is_most_relevant', False):
                        most_relevant_entry = entry
                        break
                
                for col_info in theme_columns[theme_code_iter]:
                    if col_info['type'] == 'most_relevant':
                        if most_relevant_entry:
                            row.append(most_relevant_entry.get('sub_theme_name', ''))
                        else:
                            row.append('')
                    elif col_info['type'] == 'indicator':
                        sub_theme_code_val = col_info['sub_theme_code']
                        entry = course_entries.get(sub_theme_code_val)
                        if entry:
                            row.append(entry.get('indicator_value', ''))
                        else:
                            row.append('')
            
            writer.writerow(row)
            row_num += 1
        
        csv_content = output.getvalue()
        output.close()
        
        # 添加 UTF-8 BOM
        return '\ufeff' + csv_content
