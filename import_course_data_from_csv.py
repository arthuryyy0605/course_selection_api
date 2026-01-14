#!/usr/bin/env python3
"""
匯入 CSV 課程資料到 Oracle 資料庫
包含完整流程：
1. 檢查並建立缺失的主題和細項主題
2. 建立學年期主題設定和細項主題設定
3. 匯入課程填寫記錄
"""

import csv
import asyncio
import sys
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from io import StringIO

import oracledb
from course_selection_api.config import get_settings
from course_selection_api.data_access_object.db import Database, get_database_dsn
from course_selection_api.data_access_object.theme_dao import ThemeDAO, SubThemeDAO
from course_selection_api.data_access_object.school_year_settings_dao import (
    SchoolYearThemeSettingsDAO,
    SchoolYearSubThemeSettingsDAO,
    CourseEntriesDAO
)

# 設定
settings = get_settings()

# CSV 欄位到主題和細項主題的映射
# 格式: {csv_column_name: (theme_code, sub_theme_code, week_column_name)}
FIELD_MAPPING = {
    # SDGs (A101)
    '1.消除貧窮': ('A101', '01', None),
    '2.消除飢餓': ('A101', '02', None),
    '3.健康與福祉': ('A101', '03', None),
    '4.教育品質': ('A101', '04', None),
    '5.性別平等': ('A101', '05', None),
    '6.淨水與衛生': ('A101', '06', None),
    '7.可負擔能源': ('A101', '07', None),
    '8.就業與經濟成長': ('A101', '08', None),
    '9.工業、創新基礎建設': ('A101', '09', None),
    '10.減少不平等': ('A101', '10', None),
    '11.永續城市': ('A101', '11', None),
    '12.責任消費與生產': ('A101', '12', None),
    '13.氣候行動': ('A101', '13', None),
    '14.海洋生態': ('A101', '14', None),
    '15.陸地生態': ('A101', '15', None),
    '16.和平與正義制度': ('A101', '16', None),
    '17.全球夥伴': ('A101', '17', None),
    
    # 主題 (A301)
    # 注意：資料庫中 A301 使用 1012 (跨域)，因為 1010 已被 A401 使用
    '跨域(主題:指標主題)': ('A301', '1012', None),
    '實作(主題:指標主題)': ('A301', '1020', '實作週次'),
    '行動導向(主題:指標主題)': ('A301', '1030', None),
    '氣候變遷(主題:指標主題)': ('A301', '1040', None),
    '淨零排放(主題:指標主題)': ('A301', '1050', None),
    '永續發展(主題:指標主題)': ('A301', '1060', None),
    '情緒管理(主題:指標主題)': ('A301', '1070', None),
    '人文關懷(主題:指標主題)': ('A301', '1080', '人文關懷週次'),
    '性別平等(主題:指標主題)': ('A301', '1090', None),
    '生命教育(主題:指標主題)': ('A301', '1100', None),
    '資訊安全(主題:指標主題)': ('A301', '1110', None),
    '資訊判讀(主題:指標主題)': ('A301', '1120', '媒體識讀或資訊判讀週次'),
    '媒體識讀(主題:指標主題)': ('A301', '1130', '媒體識讀或資訊判讀週次'),
    '智慧財產(主題:指標主題)': ('A301', '1140', None),
    '臺灣文學(主題:指標主題)': ('A301', '1150', None),
    '走讀台中山水遊學(主題:指標主題)': ('A301', '1160', None),
    '空間綠化設計(主題:指標主題)': ('A301', '1170', None),
    '生活環境創意美學(主題:指標主題)': ('A301', '1180', None),
    '運算思維程式設計(主題:指標主題)': ('A301', '1190', None),
    '創新創意(主題:指標主題)': ('A301', '1200', None),
    '設計思考(主題:指標主題)': ('A301', '1210', None),
    '生成式AI(主題:指標主題)': ('A301', '1220', None),
    '職涯發展(主題:指標主題)': ('A301', '1230', None),
    
    # UCAN (A401)
    # 注意：sub_theme_code 必須全局唯一，使用 2010-2080 範圍
    '資訊科技(UCAN)': ('A401', '1010', '資訊科技週次'),  # 已存在
    'UCAN創新': ('A401', '2010', None),
    'UCAN問題解決': ('A401', '2020', None),
    'UCAN人際互動': ('A401', '2030', None),
    'UCAN工作責任及紀律': ('A401', '2040', None),
    'UCAN持續學習': ('A401', '2050', None),
    'UCAN團隊合作': ('A401', '2060', None),
    'UCAN溝通表達': ('A401', '2070', None),
    'UCAN資訊科技應用': ('A401', '2080', None),
    
    # USR (A501)
    # 注意：sub_theme_code 必須全局唯一，使用 3010-3070 範圍
    '在地關懷(USR)': ('A501', '3010', '在地關懷週次'),
    '文化永續(USR)': ('A501', '3020', None),
    '健康促進(USR)': ('A501', '3030', None),
    '永續環境(USR)': ('A501', '3040', None),
    '產業鏈結與經濟永續(USR)': ('A501', '3050', None),
    '食品安全(USR)': ('A501', '3060', None),
    '社會實踐(USR)': ('A501', '3070', None),
    
    # STEAM (A601)
    # 注意：sub_theme_code 必須全局唯一，使用 4010-4050 範圍
    'STEAM科學': ('A601', '4010', None),
    'STEAM科技': ('A601', '4020', None),
    'STEAM工程': ('A601', '4030', None),
    'STEAM數學': ('A601', '4040', None),
    'STEAM藝術': ('A601', '4050', None),
}

# 主題定義
THEMES = {
    'A101': {
        'theme_name': '聯合國全球永續發展目標',
        'theme_short_name': 'SDGs',
        'theme_english_name': 'SDGs',
        'chinese_link': 'https://globalgoals.tw/',
        'english_link': None,
    },
    'A301': {
        'theme_name': '主導項目',
        'theme_short_name': '主導',
        'theme_english_name': 'Theme Project',
        'chinese_link': None,
        'english_link': None,
    },
    'A401': {
        'theme_name': 'UCAN',
        'theme_short_name': 'UCAN',
        'theme_english_name': 'UCAN',
        'chinese_link': None,
        'english_link': None,
    },
    'A501': {
        'theme_name': '大學社會責任實踐(USR)',
        'theme_short_name': 'USR',
        'theme_english_name': 'University Social Responsibility USR',
        'chinese_link': 'https://usr.moe.gov.tw/about/us',
        'english_link': None,
    },
    'A601': {
        'theme_name': 'STEAM',
        'theme_short_name': 'STEAM',
        'theme_english_name': 'STEAM',
        'chinese_link': None,
        'english_link': None,
    },
}

# SDGs 細項主題定義
SDGS_SUB_THEMES = {
    '01': {'name': '消除貧窮', 'english_name': 'No Poverty'},
    '02': {'name': '消除飢餓', 'english_name': 'Zero Hunger'},
    '03': {'name': '健康與福祉', 'english_name': 'Good Health and Well-being'},
    '04': {'name': '優質教育', 'english_name': 'Quality Education'},
    '05': {'name': '性別平等', 'english_name': 'Gender Equality'},
    '06': {'name': '淨水與衛生', 'english_name': 'Clean Water and Sanitation'},
    '07': {'name': '可負擔的潔淨能源', 'english_name': 'Affordable and Clean Energy'},
    '08': {'name': '尊嚴就業與經濟發展', 'english_name': 'Decent Work and Economic Growth'},
    '09': {'name': '產業創新與基礎設施', 'english_name': 'Industry, Innovation and Infrastructure'},
    '10': {'name': '減少不平等', 'english_name': 'Reduced Inequalities'},
    '11': {'name': '永續城市與社區', 'english_name': 'Sustainable Cities and Communities'},
    '12': {'name': '負責任的消費與生產', 'english_name': 'Responsible Consumption and Production'},
    '13': {'name': '氣候行動', 'english_name': 'Climate Action'},
    '14': {'name': '保育海洋生態', 'english_name': 'Life Below Water'},
    '15': {'name': '保育陸域生態', 'english_name': 'Life on Land'},
    '16': {'name': '和平正義與健全制度', 'english_name': 'Peace, Justice and Strong Institutions'},
    '17': {'name': '全球夥伴', 'english_name': 'Partnerships for the Goals'},
}

# 主題細項主題定義（A301）
# 注意：資料庫中已有 1012 (跨域)，由於 1010 已被 A401 使用，A301 使用 1012
THEME_SUB_THEMES = {
    '1012': {'name': '跨域', 'english_name': 'Interdisciplinary'},  # 使用 1012 因為 1010 被 A401 使用
    '1020': {'name': '實作', 'english_name': 'Practice'},
    '1030': {'name': '行動導向', 'english_name': 'Action-Oriented'},
    '1040': {'name': '氣候變遷', 'english_name': 'Climate Change'},
    '1050': {'name': '淨零排放', 'english_name': 'Net Zero Emissions'},
    '1060': {'name': '永續發展', 'english_name': 'Sustainable Development'},
    '1070': {'name': '情緒管理', 'english_name': 'Emotion Management'},
    '1080': {'name': '人文關懷', 'english_name': 'Humanistic Care'},
    '1090': {'name': '性別平等', 'english_name': 'Gender Equality'},
    '1100': {'name': '生命教育', 'english_name': 'Life Education'},
    '1110': {'name': '資訊安全', 'english_name': 'Information Security'},
    '1120': {'name': '資訊判讀', 'english_name': 'Information Literacy'},
    '1130': {'name': '媒體識讀', 'english_name': 'Media Literacy'},
    '1140': {'name': '智慧財產', 'english_name': 'Intellectual Property'},
    '1150': {'name': '臺灣文學', 'english_name': 'Taiwan Literature'},
    '1160': {'name': '走讀台中山水遊學', 'english_name': 'Taichung Landscape Study Tour'},
    '1170': {'name': '空間綠化設計', 'english_name': 'Space Greening Design'},
    '1180': {'name': '生活環境創意美學', 'english_name': 'Living Environment Creative Aesthetics'},
    '1190': {'name': '運算思維程式設計', 'english_name': 'Computational Thinking Programming'},
    '1200': {'name': '創新創意', 'english_name': 'Innovation and Creativity'},
    '1210': {'name': '設計思考', 'english_name': 'Design Thinking'},
    '1220': {'name': '生成式AI', 'english_name': 'Generative AI'},
    '1230': {'name': '職涯發展', 'english_name': 'Career Development'},
}

# UCAN 細項主題定義（A401）
# 注意：sub_theme_code 必須全局唯一
UCAN_SUB_THEMES = {
    '1010': {'name': '資訊科技', 'english_name': 'Information Technology'},  # 已存在
    '2010': {'name': '創新', 'english_name': 'Innovation'},  # 使用新 code
    '2020': {'name': '問題解決', 'english_name': 'Problem Solving'},  # 使用新 code
    '2030': {'name': '人際互動', 'english_name': 'Interpersonal Interaction'},  # 使用新 code
    '2040': {'name': '工作責任及紀律', 'english_name': 'Work Responsibility and Discipline'},  # 使用新 code
    '2050': {'name': '持續學習', 'english_name': 'Continuous Learning'},  # 使用新 code
    '2060': {'name': '團隊合作', 'english_name': 'Teamwork'},  # 使用新 code
    '2070': {'name': '溝通表達', 'english_name': 'Communication'},  # 使用新 code
    '2080': {'name': '資訊科技應用', 'english_name': 'Information Technology Application'},  # 使用新 code
}

# USR 細項主題定義（A501）
# 注意：sub_theme_code 必須全局唯一，使用 3010-3070 範圍
USR_SUB_THEMES = {
    '3010': {'name': '在地關懷', 'english_name': 'Local Care'},  # 使用新 code
    '3020': {'name': '文化永續', 'english_name': 'Cultural Sustainability'},  # 使用新 code
    '3030': {'name': '健康促進', 'english_name': 'Health Promotion'},  # 使用新 code
    '3040': {'name': '永續環境', 'english_name': 'Sustainable Environment'},  # 使用新 code
    '3050': {'name': '產業鏈結與經濟永續', 'english_name': 'Industry Linkage and Economic Sustainability'},  # 使用新 code
    '3060': {'name': '食品安全', 'english_name': 'Food Safety'},  # 使用新 code
    '3070': {'name': '社會實踐', 'english_name': 'Social Practice'},  # 使用新 code
}

# STEAM 細項主題定義（A601）
# 注意：sub_theme_code 必須全局唯一，使用 4010-4050 範圍
STEAM_SUB_THEMES = {
    '4010': {'name': '科學', 'english_name': 'Science'},  # 使用新 code
    '4020': {'name': '科技', 'english_name': 'Technology'},  # 使用新 code
    '4030': {'name': '工程', 'english_name': 'Engineering'},  # 使用新 code
    '4040': {'name': '數學', 'english_name': 'Mathematics'},  # 使用新 code
    '4050': {'name': '藝術', 'english_name': 'Arts'},  # 使用新 code
}

# 所有細項主題定義的映射
ALL_SUB_THEMES = {
    'A101': SDGS_SUB_THEMES,
    'A301': THEME_SUB_THEMES,
    'A401': UCAN_SUB_THEMES,
    'A501': USR_SUB_THEMES,
    'A601': STEAM_SUB_THEMES,
}


def parse_academic_year_term(year_term_str: str) -> Tuple[int, int]:
    """解析學年期字串（例如 '1141' -> 學年 114, 學期 1）"""
    if len(year_term_str) != 4:
        raise ValueError(f"無效的學年期格式: {year_term_str}")
    academic_year = int(year_term_str[:3])
    academic_term = int(year_term_str[3])
    return academic_year, academic_term


def parse_week_numbers(week_str: Optional[str]) -> Optional[List[int]]:
    """解析週次字串（例如 '2,3,4,5' -> [2, 3, 4, 5]）"""
    if not week_str or not week_str.strip():
        return None
    try:
        weeks = [int(w.strip()) for w in week_str.split(',') if w.strip()]
        return weeks if weeks else None
    except ValueError:
        return None


async def check_and_create_themes(conn) -> Dict[str, int]:
    """檢查並建立缺失的主題"""
    print("\n" + "=" * 60)
    print("階段 1: 檢查並建立主題")
    print("=" * 60)
    
    # 查詢現有主題
    existing_themes = await ThemeDAO.get_all_themes(conn)
    existing_theme_codes = {t['theme_code'] for t in existing_themes}
    
    print(f"現有主題數: {len(existing_themes)}")
    for theme in existing_themes:
        print(f"  - {theme['theme_code']}: {theme['theme_name']}")
    
    # 建立缺失的主題
    created_count = 0
    for theme_code, theme_info in THEMES.items():
        if theme_code not in existing_theme_codes:
            try:
                await ThemeDAO.create_theme(
                    conn,
                    theme_code=theme_code,
                    theme_name=theme_info['theme_name'],
                    theme_short_name=theme_info['theme_short_name'],
                    theme_english_name=theme_info['theme_english_name'],
                    chinese_link=theme_info.get('chinese_link'),
                    english_link=theme_info.get('english_link'),
                    created_by='csv_import'
                )
                print(f"  ✓ 建立主題: {theme_code} - {theme_info['theme_name']}")
                created_count += 1
            except Exception as e:
                error_str = str(e).lower()
                if 'unique constraint' in error_str or 'ora-00001' in error_str:
                    print(f"  ℹ️  主題已存在: {theme_code}")
                else:
                    print(f"  ❌ 建立主題失敗 {theme_code}: {e}")
    
    print(f"\n新建主題數: {created_count}")
    return {'created': created_count, 'existing': len(existing_themes)}


async def check_and_create_sub_themes(conn) -> Dict[str, int]:
    """檢查並建立缺失的細項主題"""
    print("\n" + "=" * 60)
    print("階段 2: 檢查並建立細項主題")
    print("=" * 60)
    
    # 查詢現有細項主題
    existing_sub_themes = await SubThemeDAO.get_all_sub_themes(conn)
    existing_sub_theme_keys = {(st['theme_code'], st['sub_theme_code']) for st in existing_sub_themes}
    
    print(f"現有細項主題數: {len(existing_sub_themes)}")
    
    # 建立缺失的細項主題
    created_count = 0
    failed_count = 0
    for theme_code, sub_themes_dict in ALL_SUB_THEMES.items():
        theme_missing = []
        for sub_theme_code, sub_theme_info in sub_themes_dict.items():
            key = (theme_code, sub_theme_code)
            if key not in existing_sub_theme_keys:
                theme_missing.append((sub_theme_code, sub_theme_info))
        
        if theme_missing:
            # 先獲取主題ID
            theme = await ThemeDAO.get_theme_by_code(conn, theme_code)
            if not theme:
                print(f"  ❌ 主題 {theme_code} 不存在，跳過")
                continue
            
            print(f"\n  處理主題 {theme_code}，需要建立 {len(theme_missing)} 個細項主題:")
            for sub_theme_code, sub_theme_info in theme_missing:
                try:
                    await SubThemeDAO.create_sub_theme(
                        conn,
                        coures_themes_id=theme['id'],
                        sub_theme_code=sub_theme_code,
                        sub_theme_name=sub_theme_info['name'],
                        sub_theme_english_name=sub_theme_info['english_name'],
                        created_by='csv_import'
                    )
                    print(f"    ✓ 建立: {sub_theme_code} - {sub_theme_info['name']}")
                    created_count += 1
                except Exception as e:
                    error_str = str(e).lower()
                    if 'unique constraint' in error_str or 'ora-00001' in error_str:
                        print(f"    ℹ️  已存在: {sub_theme_code} - {sub_theme_info['name']}")
                    else:
                        print(f"    ❌ 失敗: {sub_theme_code} - {sub_theme_info['name']}: {e}")
                        failed_count += 1
    
    print(f"\n新建細項主題數: {created_count}")
    return {'created': created_count, 'existing': len(existing_sub_themes)}


async def create_school_year_settings(conn, academic_years_terms: Set[Tuple[int, int]]) -> Dict[str, int]:
    """建立學年期主題設定和細項主題設定"""
    print("\n" + "=" * 60)
    print("階段 3: 建立學年期設定")
    print("=" * 60)
    
    theme_settings_created = 0
    sub_theme_settings_created = 0
    
    # 主題設定配置（根據實際需求調整）
    # 注意: indicator_type 使用資料庫預設值 'LMH'，如需修改請使用 update 方法
    theme_settings_config = {
        'A101': {'fill_in_week_enabled': False, 'scale_max': 5},
        'A301': {'fill_in_week_enabled': True, 'scale_max': 5},
        'A401': {'fill_in_week_enabled': True, 'scale_max': 5},
        'A501': {'fill_in_week_enabled': True, 'scale_max': 5},
        'A601': {'fill_in_week_enabled': False, 'scale_max': 5},
    }
    
    for academic_year, academic_term in sorted(academic_years_terms):
        print(f"\n處理學年期: {academic_year}-{academic_term}")
        
        for theme_code in THEMES.keys():
            # 檢查主題設定是否已存在
            existing_setting = await SchoolYearThemeSettingsDAO.get_school_year_theme_setting_by_code(
                conn, academic_year, academic_term, theme_code
            )
            
            if not existing_setting:
                try:
                    config = theme_settings_config.get(theme_code, {
                        'fill_in_week_enabled': False,
                        'scale_max': 5
                    })
                    
                    await SchoolYearThemeSettingsDAO.create_school_year_theme_setting(
                        conn,
                        academic_year=academic_year,
                        academic_term=academic_term,
                        theme_code=theme_code,
                        fill_in_week_enabled=config['fill_in_week_enabled'],
                        scale_max=config['scale_max'],
                        select_most_relevant_sub_theme_enabled=False,
                        created_by='csv_import'
                    )
                    # 計算該主題的細項主題數量（由主題設定自動建立）
                    sub_themes = await SubThemeDAO.get_sub_themes_by_theme_code(conn, theme_code)
                    sub_theme_settings_created += len(sub_themes)
                    print(f"  ✓ 建立主題設定: {theme_code} (包含 {len(sub_themes)} 個細項主題設定)")
                    theme_settings_created += 1
                except Exception as e:
                    error_str = str(e).lower()
                    if 'unique constraint' in error_str or 'ora-00001' in error_str:
                        print(f"  ℹ️  主題設定已存在: {theme_code}")
                    else:
                        print(f"  ❌ 建立主題設定失敗 {theme_code}: {e}")
            else:
                print(f"  ℹ️  主題設定已存在: {theme_code}")
                # 檢查並建立缺失的細項主題設定
                try:
                    # 取得該主題的所有細項主題
                    all_sub_themes = await SubThemeDAO.get_sub_themes_by_theme_code(conn, theme_code)
                    print(f"    → 該主題共有 {len(all_sub_themes)} 個細項主題")
                    
                    # 取得已存在的細項主題設定
                    existing_sub_theme_settings = await SchoolYearSubThemeSettingsDAO.get_school_year_sub_theme_settings_by_year_and_theme(
                        conn, academic_year, academic_term, theme_code
                    )
                    # 只計算真正存在的細項主題設定（created_at 不為 None 表示設定存在）
                    existing_sub_theme_codes = {
                        st['sub_theme_code'] for st in existing_sub_theme_settings 
                        if st.get('created_at') is not None
                    }
                    print(f"    → 已有 {len(existing_sub_theme_codes)} 個細項主題設定（共 {len(existing_sub_theme_settings)} 個細項主題）")
                    
                    # 找出缺失的細項主題設定
                    missing_sub_themes = [st for st in all_sub_themes if st['sub_theme_code'] not in existing_sub_theme_codes]
                    
                    if missing_sub_themes:
                        print(f"    → 需要建立 {len(missing_sub_themes)} 個缺失的細項主題設定")
                        # 建立缺失的細項主題設定
                        missing_count = 0
                        for sub_theme in missing_sub_themes:
                            try:
                                await SchoolYearSubThemeSettingsDAO.create_school_year_sub_theme_setting(
                                    conn,
                                    academic_year=academic_year,
                                    academic_term=academic_term,
                                    theme_code=theme_code,
                                    sub_theme_code=sub_theme['sub_theme_code'],
                                    enabled=True,
                                    created_by='csv_import'
                                )
                                missing_count += 1
                                print(f"      ✓ 建立: {sub_theme['sub_theme_code']} - {sub_theme['sub_theme_name']}")
                            except Exception as e:
                                error_str = str(e).lower()
                                if 'unique constraint' in error_str or 'ora-00001' in error_str:
                                    print(f"      ℹ️  已存在: {sub_theme['sub_theme_code']} - {sub_theme['sub_theme_name']}")
                                else:
                                    print(f"      ❌ 失敗: {sub_theme['sub_theme_code']} - {sub_theme['sub_theme_name']}: {e}")
                        
                        if missing_count > 0:
                            sub_theme_settings_created += missing_count
                            print(f"    → 成功建立 {missing_count} 個細項主題設定")
                    else:
                        print(f"    → 所有細項主題設定已存在")
                except Exception as e:
                    print(f"    ⚠️  檢查細項主題設定時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
    
    print(f"\n新建主題設定數: {theme_settings_created}")
    print(f"新建細項主題設定數: {sub_theme_settings_created} (由主題設定自動建立)")
    
    return {
        'theme_settings_created': theme_settings_created,
        'sub_theme_settings_created': sub_theme_settings_created
    }


def read_csv_file(file_path: str) -> List[Dict]:
    """讀取 CSV 檔案"""
    print("\n" + "=" * 60)
    print("階段 4: 讀取 CSV 檔案")
    print("=" * 60)
    
    rows = []
    # 嘗試多種編碼方式
    encodings = ['utf-8-sig', 'big5', 'big5-hkscs', 'cp950', 'utf-8']
    file_opened = False
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                # 讀取所有行
                all_lines = list(f)
                if not all_lines:
                    continue
                
                # 檢查第一行是否為有效的標題行
                # 有效的標題行應該包含「學年期」這個關鍵欄位
                first_line = all_lines[0].strip()
                header_line_index = 0
                
                # 檢查第一行是否包含「學年期」
                if '學年期' not in first_line:
                    # 如果第一行不包含「學年期」，檢查第二行
                    if len(all_lines) > 1:
                        second_line = all_lines[1].strip()
                        if '學年期' in second_line:
                            # 第二行是標題行，跳過第一行
                            print(f"  偵測到第一行為無效標題，跳過第一行，使用第二行作為標題行")
                            header_line_index = 1
                        else:
                            # 兩行都不包含「學年期」，可能編碼問題，嘗試正常讀取
                            print(f"  警告：無法確定標題行位置，使用第一行作為標題")
                    else:
                        # 只有一行，直接使用
                        pass
                # 第一行包含「學年期」，是有效的標題行，正常讀取
                
                # 從標題行開始讀取
                content = ''.join(all_lines[header_line_index:])
                reader = csv.DictReader(StringIO(content))
                
                for row in reader:
                    rows.append(row)
            print(f"使用編碼 {encoding} 成功讀取檔案")
            file_opened = True
            break
        except (UnicodeDecodeError, UnicodeError) as e:
            continue
        except Exception as e:
            print(f"使用編碼 {encoding} 讀取失敗: {e}")
            continue
    
    if not file_opened:
        raise Exception(f"無法使用任何編碼讀取檔案: {file_path}")
    
    print(f"讀取到 {len(rows)} 筆記錄")
    return rows


async def import_course_entries(conn, csv_rows: List[Dict]) -> Dict[str, int]:
    """匯入課程填寫記錄"""
    print("\n" + "=" * 60)
    print("階段 5: 匯入課程填寫記錄")
    print("=" * 60)
    
    success_count = 0
    skip_count = 0
    error_count = 0
    errors = []
    
    total_records = 0
    
    for row_idx, row in enumerate(csv_rows, 1):
        # 解析學年期
        try:
            academic_year, academic_term = parse_academic_year_term(row['學年期'])
        except Exception as e:
            error_count += 1
            errors.append(f"第 {row_idx} 行: 學年期解析失敗 - {e}")
            continue
        
        subj_no = row['OPMS_COURSE_NO']
        ps_class_nbr = row['PS_CLASS_NBR']
        
        # 讀取最相關的 SDGs（如果有的話）
        # 注意：CSV 欄位名稱可能是「最相關的 SDGs」或「最相關 SDGs」
        most_relevant_sdgs_code = None
        sdgs_field_name = None
        for field_name in ['最相關的 SDGs', '最相關 SDGs', 'SDGs']:
            if field_name in row and row[field_name] and row[field_name].strip():
                try:
                    sdgs_num = int(row[field_name].strip())
                    # 轉換為兩位數的 sub_theme_code（例如 4 -> '04', 11 -> '11'）
                    most_relevant_sdgs_code = f"{sdgs_num:02d}"
                    sdgs_field_name = field_name
                    break
                except (ValueError, TypeError):
                    # 如果無法解析，繼續嘗試下一個欄位名稱
                    continue
        
        # 處理每個有值的欄位
        for csv_column, (theme_code, sub_theme_code, week_column) in FIELD_MAPPING.items():
            if csv_column not in row:
                continue
            
            indicator_value = row[csv_column].strip() if row[csv_column] else None
            if not indicator_value or indicator_value == '':
                continue
            
            # 取得週次資料
            week_numbers = None
            if week_column and week_column in row:
                week_numbers = parse_week_numbers(row[week_column])
            
            # 判斷是否為最相關的 SDGs
            # 只有當 theme_code 是 A101 且 sub_theme_code 等於 most_relevant_sdgs_code 時才設為 True
            is_most_relevant = False
            if theme_code == 'A101' and most_relevant_sdgs_code and sub_theme_code == most_relevant_sdgs_code:
                is_most_relevant = True
            
            # 檢查記錄是否已存在
            existing_entry = await CourseEntriesDAO.get_course_entry(
                conn, subj_no, ps_class_nbr, academic_year, academic_term, sub_theme_code
            )
            
            if existing_entry:
                # 如果記錄已存在，檢查是否需要更新 is_most_relevant
                if is_most_relevant and not existing_entry.get('is_most_relevant', False):
                    # 需要更新 is_most_relevant
                    try:
                        await CourseEntriesDAO.update_course_entry(
                            conn,
                            subj_no=subj_no,
                            ps_class_nbr=ps_class_nbr,
                            academic_year=academic_year,
                            academic_term=academic_term,
                            sub_theme_code=sub_theme_code,
                            indicator_value=existing_entry['indicator_value'],
                            week_numbers=existing_entry.get('week_numbers'),
                            is_most_relevant=True,
                            updated_by='csv_import'
                        )
                        success_count += 1
                        total_records += 1
                    except Exception as e:
                        error_count += 1
                        error_msg = f"第 {row_idx} 行, 課程 {subj_no}-{ps_class_nbr}, 更新最相關 SDGs {sub_theme_code}: {e}"
                        errors.append(error_msg)
                        if len(errors) <= 10:
                            print(f"  ❌ {error_msg}")
                else:
                    skip_count += 1
                continue
            
            # 建立記錄
            try:
                await CourseEntriesDAO.create_course_entry(
                    conn,
                    subj_no=subj_no,
                    ps_class_nbr=ps_class_nbr,
                    academic_year=academic_year,
                    academic_term=academic_term,
                    sub_theme_code=sub_theme_code,
                    indicator_value=str(indicator_value),
                    week_numbers=week_numbers,
                    is_most_relevant=is_most_relevant,
                    created_by='csv_import'
                )
                success_count += 1
                total_records += 1
                
                if total_records % 100 == 0:
                    print(f"  已處理 {total_records} 筆記錄...")
                    
            except Exception as e:
                error_count += 1
                error_msg = f"第 {row_idx} 行, 課程 {subj_no}-{ps_class_nbr}, 細項主題 {sub_theme_code}: {e}"
                errors.append(error_msg)
                if len(errors) <= 10:  # 只記錄前 10 個錯誤
                    print(f"  ❌ {error_msg}")
    
    print(f"\n匯入結果:")
    print(f"  ✓ 成功匯入: {success_count} 筆")
    print(f"  ℹ️  跳過 (已存在): {skip_count} 筆")
    print(f"  ❌ 錯誤: {error_count} 筆")
    
    if errors and len(errors) > 10:
        print(f"\n前 10 個錯誤:")
        for error in errors[:10]:
            print(f"  - {error}")
    elif errors:
        print(f"\n錯誤詳情:")
        for error in errors:
            print(f"  - {error}")
    
    return {
        'success': success_count,
        'skip': skip_count,
        'error': error_count,
        'errors': errors
    }


async def main():
    """主函數"""
    csv_file_path = '塞入的資料.csv'
    
    print("=" * 60)
    print("CSV 課程資料匯入工具")
    print("=" * 60)
    
    # 連線資料庫
    dsn = get_database_dsn()
    conn = None
    try:
        print(f"\n連線資料庫: {dsn}")
        conn = await asyncio.to_thread(
            oracledb.connect,
            user=settings.db_user,
            password=settings.db_password,
            dsn=dsn
        )
        print("✓ 資料庫連線成功")
        
        # 階段 1: 檢查並建立主題
        theme_stats = await check_and_create_themes(conn)
        
        # 階段 2: 檢查並建立細項主題
        sub_theme_stats = await check_and_create_sub_themes(conn)
        
        # 階段 3: 讀取 CSV 並分析需要的學年期
        csv_rows = read_csv_file(csv_file_path)
        academic_years_terms = set()
        for row in csv_rows:
            try:
                academic_year, academic_term = parse_academic_year_term(row['學年期'])
                academic_years_terms.add((academic_year, academic_term))
            except:
                pass
        
        # 階段 4: 建立學年期設定
        settings_stats = await create_school_year_settings(conn, academic_years_terms)
        
        # 階段 5: 匯入課程記錄
        import_stats = await import_course_entries(conn, csv_rows)
        
        # 提交所有變更
        await asyncio.to_thread(conn.commit)
        print("\n✓ 所有變更已提交")
        
        # 輸出統計報告
        print("\n" + "=" * 60)
        print("匯入統計報告")
        print("=" * 60)
        print(f"主題:")
        print(f"  - 現有: {theme_stats['existing']}")
        print(f"  - 新建: {theme_stats['created']}")
        print(f"細項主題:")
        print(f"  - 現有: {sub_theme_stats['existing']}")
        print(f"  - 新建: {sub_theme_stats['created']}")
        print(f"學年期設定:")
        print(f"  - 主題設定新建: {settings_stats['theme_settings_created']}")
        print(f"  - 細項主題設定新建: {settings_stats['sub_theme_settings_created']}")
        print(f"課程記錄:")
        print(f"  - 成功匯入: {import_stats['success']}")
        print(f"  - 跳過: {import_stats['skip']}")
        print(f"  - 錯誤: {import_stats['error']}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            await asyncio.to_thread(conn.rollback)
        sys.exit(1)
    finally:
        if conn:
            await asyncio.to_thread(conn.close)
            print("\n資料庫連線已關閉")


if __name__ == "__main__":
    asyncio.run(main())

