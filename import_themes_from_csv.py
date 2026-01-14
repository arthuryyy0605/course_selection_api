#!/usr/bin/env python3
"""
從 CSV 檔案匯入主題和細項主題資料到 Oracle 資料庫

執行方式:
    poetry run python import_themes_from_csv.py
"""

from __future__ import annotations

import asyncio
import csv
import sys
from typing import Dict, List, Tuple

import oracledb
from course_selection_api.config import get_settings
from course_selection_api.data_access_object.db import get_database_dsn
from course_selection_api.data_access_object.theme_dao import ThemeDAO, SubThemeDAO

# 設定
settings = get_settings()

# 英文名稱映射（如果 CSV 中沒有提供）
ENGLISH_NAME_MAPPING = {
    # A101 - SDGs
    '消除貧窮': 'No Poverty',
    '消除飢餓': 'Zero Hunger',
    '健康與福祉': 'Good Health and Well-being',
    '教育品質': 'Quality Education',
    '性別平等': 'Gender Equality',
    '淨水與衛生': 'Clean Water and Sanitation',
    '可負擔能源': 'Affordable and Clean Energy',
    '就業與經濟成長': 'Decent Work and Economic Growth',
    '工業、創新基礎建設': 'Industry, Innovation and Infrastructure',
    '減少不平等': 'Reduced Inequalities',
    '永續城市': 'Sustainable Cities and Communities',
    '責任消費與生產': 'Responsible Consumption and Production',
    '氣候行動': 'Climate Action',
    '海洋生態': 'Life Below Water',
    '陸地生態': 'Life on Land',
    '和平與正義制度': 'Peace, Justice and Strong Institutions',
    '全球夥伴': 'Partnerships for the Goals',
    # A201 - 高教深耕指標
    '在地關懷(USR)': 'Local Care (USR)',
    '實作': 'Practice',
    '跨域': 'Interdisciplinary',
    '資訊科技(UCAN)': 'Information Technology (UCAN)',
    '媒體識讀': 'Media Literacy',
    '資訊判讀': 'Information Literacy',
    '資訊安全': 'Information Security',
    '行動導向': 'Action-Oriented',
    '職涯發展': 'Career Development',
    # A301 - AI課程
    '生成式AI': 'Generative AI',
    # A401 - 主題指標
    '氣候變遷': 'Climate Change',
    '淨零排放': 'Net Zero Emissions',
    '永續發展': 'Sustainable Development',
    '情緒管理': 'Emotion Management',
    '生命教育': 'Life Education',
    '智慧財產': 'Intellectual Property',
    '臺灣文學': 'Taiwan Literature',
    '走讀台中山水遊學': 'Taichung Landscape Study Tour',
    '空間綠化設計': 'Space Greening Design',
    '生活環境創意美學': 'Living Environment Creative Aesthetics',
    '運算思維程式設計': 'Computational Thinking Programming',
    '創新創意': 'Innovation and Creativity',
    '設計思考': 'Design Thinking',
    # A501 - USR
    '文化永續(USR)': 'Cultural Sustainability (USR)',
    '健康促進(USR)': 'Health Promotion (USR)',
    '永續環境(USR)': 'Sustainable Environment (USR)',
    '產業鏈結與經濟永續(USR)': 'Industry Linkage and Economic Sustainability (USR)',
    '食品安全(USR)': 'Food Safety (USR)',
    '社會實踐(USR)': 'Social Practice (USR)',
    # A601 - UCAN
    'UCAN創新': 'UCAN Innovation',
    'UCAN問題解決': 'UCAN Problem Solving',
    'UCAN人際互動': 'UCAN Interpersonal Interaction',
    'UCAN工作責任及紀律': 'UCAN Work Responsibility and Discipline',
    'UCAN持續學習': 'UCAN Continuous Learning',
    'UCAN團隊合作': 'UCAN Teamwork',
    'UCAN溝通表達': 'UCAN Communication',
    'UCAN資訊科技應用': 'UCAN Information Technology Application',
    # A701 - STEAM
    'STEAM科學': 'STEAM Science',
    'STEAM科技': 'STEAM Technology',
    'STEAM工程': 'STEAM Engineering',
    'STEAM數學': 'STEAM Mathematics',
    'STEAM藝術': 'STEAM Arts',
}


def parse_csv_file(csv_file: str):
    """
    解析 CSV 檔案，返回主題和子主題資料
    
    Returns:
        (themes_dict, sub_themes_dict)
        themes_dict: {theme_code: {name, short_name, english_name, ...}}
        sub_themes_dict: {theme_code: [(sub_code, sub_name), ...]}
    """
    themes_dict = {}
    sub_themes_dict = {}
    
    with open(csv_file, 'r', encoding='big5') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    # 找出每個主題的範圍
    theme_ranges = {}
    for col_idx in range(len(rows[0])):
        cell = rows[0][col_idx]
        if cell and cell.startswith('A'):
            theme_code = cell
            theme_name = rows[1][col_idx] if col_idx < len(rows[1]) else ''
            
            # 找出這個主題的範圍
            start_col = col_idx
            end_col = len(rows[0])
            
            # 找下一個主題的位置
            for next_col in range(col_idx + 1, len(rows[0])):
                next_cell = rows[0][next_col]
                if next_cell and next_cell.startswith('A'):
                    end_col = next_col
                    break
            
            theme_ranges[theme_code] = {
                'name': theme_name,
                'start': start_col,
                'end': end_col
            }
    
    # 處理每個主題
    for theme_code, info in theme_ranges.items():
        theme_name = info['name']
        
        # 生成主題的簡稱和英文名稱
        theme_short_name = theme_code
        theme_english_name = theme_name
        
        # 根據主題代碼設定簡稱和英文名稱
        if theme_code == 'A101':
            theme_short_name = 'SDGs'
            theme_english_name = 'SDGs'
        elif theme_code == 'A201':
            theme_short_name = '深耕'
            theme_english_name = 'Higher Education Sprout Project'
        elif theme_code == 'A301':
            theme_short_name = 'AI'
            theme_english_name = 'AI Courses'
        elif theme_code == 'A401':
            theme_short_name = '指標'
            theme_english_name = 'Theme Indicators'
        elif theme_code == 'A501':
            theme_short_name = 'USR'
            theme_english_name = 'University Social Responsibility (USR)'
        elif theme_code == 'A601':
            theme_short_name = 'UCAN'
            theme_english_name = 'UCAN'
        elif theme_code == 'A701':
            theme_short_name = 'STEAM'
            theme_english_name = 'STEAM'
        
        themes_dict[theme_code] = {
            'theme_name': theme_name,
            'theme_short_name': theme_short_name,
            'theme_english_name': theme_english_name,
            'chinese_link': None,
            'english_link': None,
        }
        
        # 提取子主題（包括主題代碼欄位本身，因為第一個子主題可能在那裡）
        sub_themes = []
        for col_idx in range(info['start'], info['end']):
            if col_idx < len(rows[2]) and col_idx < len(rows[3]):
                sub_code = rows[2][col_idx]
                sub_name = rows[3][col_idx]
                # 跳過標題行
                if sub_code == '子代碼' or sub_name == '子主題':
                    continue
                # 只處理有代碼和名稱的欄位
                if sub_code and sub_name:
                    # 清理子主題名稱（移除前面的數字和點）
                    clean_name = sub_name
                    if '.' in sub_name and sub_name[0].isdigit():
                        parts = sub_name.split('.', 1)
                        if len(parts) > 1:
                            clean_name = parts[1]
                    sub_themes.append((sub_code, clean_name))
        
        if sub_themes:
            sub_themes_dict[theme_code] = sub_themes
    
    return themes_dict, sub_themes_dict


def get_english_name(chinese_name: str) -> str:
    """根據中文名稱獲取英文名稱"""
    # 先嘗試直接匹配
    if chinese_name in ENGLISH_NAME_MAPPING:
        return ENGLISH_NAME_MAPPING[chinese_name]
    
    # 嘗試移除括號後匹配
    name_without_brackets = chinese_name.split('(')[0].strip()
    if name_without_brackets in ENGLISH_NAME_MAPPING:
        base_english = ENGLISH_NAME_MAPPING[name_without_brackets]
        # 保留括號內容
        if '(' in chinese_name:
            bracket_content = chinese_name[chinese_name.index('('):]
            return f"{base_english} {bracket_content}"
        return base_english
    
    # 如果找不到，返回中文名稱（稍後可以手動更新）
    return chinese_name


async def import_themes(conn, themes_dict: Dict[str, Dict]) -> Dict[str, int]:
    """匯入主題"""
    print("\n" + "=" * 60)
    print("步驟 1: 匯入主題")
    print("=" * 60)
    
    existing_themes = await ThemeDAO.get_all_themes(conn)
    existing_theme_codes = {t['theme_code'] for t in existing_themes}
    
    print(f"現有主題數: {len(existing_themes)}")
    
    created_count = 0
    updated_count = 0
    
    for theme_code, theme_info in themes_dict.items():
        if theme_code in existing_theme_codes:
            # 檢查是否需要更新
            existing_theme = await ThemeDAO.get_theme_by_code(conn, theme_code)
            needs_update = (
                existing_theme['theme_name'] != theme_info['theme_name'] or
                existing_theme['theme_short_name'] != theme_info['theme_short_name'] or
                existing_theme['theme_english_name'] != theme_info['theme_english_name']
            )
            
            if needs_update:
                try:
                    await ThemeDAO.update_theme(
                        conn,
                        existing_theme['id'],
                        theme_name=theme_info['theme_name'],
                        theme_short_name=theme_info['theme_short_name'],
                        theme_english_name=theme_info['theme_english_name'],
                        chinese_link=theme_info.get('chinese_link'),
                        english_link=theme_info.get('english_link'),
                        updated_by='csv_import'
                    )
                    print(f"  ✓ 更新主題: {theme_code} - {theme_info['theme_name']}")
                    updated_count += 1
                except Exception as e:
                    print(f"  ❌ 更新主題失敗 {theme_code}: {e}")
            else:
                print(f"  ℹ️  主題已存在: {theme_code} - {theme_info['theme_name']}")
        else:
            # 創建新主題
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
    print(f"更新主題數: {updated_count}")
    return {'created': created_count, 'updated': updated_count}


async def import_sub_themes(conn, sub_themes_dict: Dict[str, List[Tuple[str, str]]]) -> Dict[str, int]:
    """匯入細項主題"""
    print("\n" + "=" * 60)
    print("步驟 2: 匯入細項主題")
    print("=" * 60)
    
    existing_sub_themes = await SubThemeDAO.get_all_sub_themes(conn)
    existing_theme_sub_theme_map = {(st['theme_code'], st['sub_theme_code']) for st in existing_sub_themes}
    
    print(f"現有細項主題數: {len(existing_sub_themes)}")
    
    created_count = 0
    updated_count = 0
    skipped_count = 0
    failed_count = 0
    
    for theme_code, sub_themes in sub_themes_dict.items():
        print(f"\n處理主題 {theme_code}:")
        
        for sub_code, sub_name in sub_themes:
            key = (theme_code, sub_code)
            english_name = get_english_name(sub_name)
            
            if key in existing_theme_sub_theme_map:
                # 檢查是否需要更新
                existing_sub_theme = await SubThemeDAO.get_sub_theme_by_code(conn, theme_code, sub_code)
                if existing_sub_theme:
                    needs_update = (
                        existing_sub_theme['sub_theme_name'] != sub_name or
                        existing_sub_theme['sub_theme_english_name'] != english_name
                    )
                    
                    if needs_update:
                        try:
                            await SubThemeDAO.update_sub_theme(
                                conn,
                                existing_sub_theme['id'],
                                sub_theme_name=sub_name,
                                sub_theme_english_name=english_name,
                                updated_by='csv_import'
                            )
                            print(f"    ✓ 更新: {sub_code} - {sub_name}")
                            updated_count += 1
                        except Exception as e:
                            print(f"    ❌ 更新失敗: {sub_code} - {e}")
                            failed_count += 1
                    else:
                        print(f"    ℹ️  已存在: {sub_code} - {sub_name}")
                        skipped_count += 1
            else:
                # 創建新細項主題
                try:
                    # 先獲取主題ID
                    theme = await ThemeDAO.get_theme_by_code(conn, theme_code)
                    if not theme:
                        print(f"    ❌ 主題 {theme_code} 不存在，跳過")
                        failed_count += 1
                        continue
                    
                    await SubThemeDAO.create_sub_theme(
                        conn,
                        coures_themes_id=theme['id'],
                        sub_theme_code=sub_code,
                        sub_theme_name=sub_name,
                        sub_theme_english_name=english_name,
                        created_by='csv_import'
                    )
                    print(f"    ✓ 建立: {sub_code} - {sub_name}")
                    created_count += 1
                    existing_theme_sub_theme_map.add(key)
                except Exception as e:
                    error_str = str(e).lower()
                    if 'unique constraint' in error_str or 'ora-00001' in error_str:
                        print(f"    ℹ️  已存在（唯一約束）: {sub_code} - {sub_name}")
                        skipped_count += 1
                    else:
                        print(f"    ❌ 建立失敗: {sub_code} - {sub_name}: {e}")
                        failed_count += 1
    
    print(f"\n新建細項主題數: {created_count}")
    print(f"更新細項主題數: {updated_count}")
    if skipped_count > 0:
        print(f"跳過數（已存在）: {skipped_count}")
    if failed_count > 0:
        print(f"失敗數: {failed_count}")
    
    return {
        'created': created_count,
        'updated': updated_count,
        'skipped': skipped_count,
        'failed': failed_count
    }


async def main():
    """主函數"""
    csv_file = '主題.csv'
    
    print("=" * 60)
    print("從 CSV 匯入主題和細項主題資料")
    print("=" * 60)
    
    # 解析 CSV
    print(f"\n📄 解析 CSV 檔案: {csv_file}")
    try:
        themes_dict, sub_themes_dict = parse_csv_file(csv_file)
        print(f"✓ 解析完成")
        print(f"  主題數: {len(themes_dict)}")
        total_sub_themes = sum(len(subs) for subs in sub_themes_dict.values())
        print(f"  細項主題總數: {total_sub_themes}")
    except Exception as e:
        print(f"❌ 解析 CSV 失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 連線資料庫
    dsn = get_database_dsn()
    conn = None
    try:
        print(f"\n🔌 連線資料庫: {dsn}")
        conn = await asyncio.to_thread(
            oracledb.connect,
            user=settings.db_user,
            password=settings.db_password,
            dsn=dsn
        )
        print("✓ 資料庫連線成功")
        
        # 匯入主題
        theme_stats = await import_themes(conn, themes_dict)
        
        # 匯入細項主題
        sub_theme_stats = await import_sub_themes(conn, sub_themes_dict)
        
        # 提交所有變更
        await asyncio.to_thread(conn.commit)
        print("\n✓ 所有變更已提交")
        
        # 輸出統計報告
        print("\n" + "=" * 60)
        print("統計報告")
        print("=" * 60)
        print(f"主題:")
        print(f"  - 新建: {theme_stats['created']}")
        print(f"  - 更新: {theme_stats['updated']}")
        print(f"細項主題:")
        print(f"  - 新建: {sub_theme_stats['created']}")
        print(f"  - 更新: {sub_theme_stats['updated']}")
        if sub_theme_stats.get('skipped', 0) > 0:
            print(f"  - 跳過: {sub_theme_stats['skipped']}")
        if sub_theme_stats.get('failed', 0) > 0:
            print(f"  - 失敗: {sub_theme_stats['failed']}")
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

