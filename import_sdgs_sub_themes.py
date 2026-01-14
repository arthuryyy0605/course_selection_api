#!/usr/bin/env python3
"""
匯入 SDGs 細項主題資料到 Oracle 資料庫
從 PostgreSQL 格式的 SQL 轉換為 Oracle 格式
"""

import oracledb
from datetime import datetime
import re
import uuid

# 連線資訊
USERNAME = "schoolsdgs"
PASSWORD = "Sdgs2025"
DSN = "140.120.3.90:1521/nchu"

# 資料（從 SQL 檔案解析）
data = [
    ('A101', '01', '消除貧窮', 'No Poverty', 
     '消除各地一切形式的貧窮。確保所有男女，特別是貧窮與弱勢族群，享有平等獲取經濟資源的權利，以及基本服務、土地與財產所有權與控制權、自然資源、新技術與金融服務。',
     'End poverty in all its forms everywhere. Ensure that all men and women have equal rights to economic resources and access to basic services, ownership and control over land and other forms of property, natural resources, appropriate new technology and financial services.',
     '2025-12-13 09:15:25.798757', '2025-12-13 09:34:15.5545'),
    ('A101', '02', '消除飢餓', 'Zero Hunger',
     '消除飢餓，實現糧食安全，改善營養狀況和促進永續農業。確保所有人都能獲得安全、營養和充足的食物，特別關注貧窮和弱勢群體。',
     'End hunger, achieve food security and improved nutrition and promote sustainable agriculture. Ensure access for all people to safe, nutritious and sufficient food all year round, with particular attention to the poor and vulnerable.',
     '2025-12-13 09:15:25.798757', '2025-12-13 09:34:15.5545'),
    ('A101', '03', '健康與福祉', 'Good Health and Well-being',
     '確保健康的生活方式，促進各年齡層人群的福祉。降低孕產婦和兒童死亡率，終結傳染病，對抗非傳染性疾病，促進心理健康和幸福感。',
     'Ensure healthy lives and promote well-being for all at all ages. Reduce maternal and child mortality, end epidemics of communicable diseases, combat non-communicable diseases, promote mental health and well-being.',
     '2025-12-13 09:34:15.5545', '2025-12-13 09:34:15.5545'),
    ('A101', '04', '優質教育', 'Quality Education',
     '確保包容和公平的優質教育，讓全民終身享有學習機會。消除教育中的性別差距，確保弱勢群體平等獲得各級教育和職業培訓。',
     'Ensure inclusive and equitable quality education and promote lifelong learning opportunities for all. Eliminate gender disparities in education and ensure equal access to all levels of education and vocational training for the vulnerable.',
     '2025-12-13 09:34:15.5545', '2025-12-13 09:34:15.5545'),
    ('A101', '05', '性別平等', 'Gender Equality',
     '實現性別平等，增強所有婦女和女童的權能。消除對婦女和女孩的一切形式歧視和暴力，確保婦女全面有效參與各級決策領導工作。',
     'Achieve gender equality and empower all women and girls. End all forms of discrimination and violence against women and girls, ensure full participation in leadership and decision-making at all levels.',
     '2025-12-13 09:34:15.5545', '2025-12-13 09:34:15.5545'),
    ('A101', '06', '淨水與衛生', 'Clean Water and Sanitation',
     '確保人人都能享有水資源、衛生及永續管理。實現人人普遍和公平獲得安全和負擔得起的飲用水，改善水質，提高用水效率。',
     'Ensure availability and sustainable management of water and sanitation for all. Achieve universal and equitable access to safe and affordable drinking water, improve water quality, and increase water-use efficiency.',
     '2025-12-13 09:34:15.5545', '2025-12-13 09:34:15.5545'),
    ('A101', '07', '可負擔的潔淨能源', 'Affordable and Clean Energy',
     '確保人人都能享有可負擔、可靠、永續及現代的能源。大幅提高再生能源比例，提高能源效率，加強能源基礎設施和清潔能源技術。',
     'Ensure access to affordable, reliable, sustainable and modern energy for all. Increase substantially the share of renewable energy, improve energy efficiency, and enhance energy infrastructure and clean energy technology.',
     '2025-12-13 09:34:15.5545', '2025-12-13 09:34:15.5545'),
    ('A101', '08', '尊嚴就業與經濟發展', 'Decent Work and Economic Growth',
     '促進包容且永續的經濟成長，提升勞動生產力，確保全面有生產力的就業，讓所有人都有一份好工作。保護勞工權益和安全的工作環境。',
     'Promote sustained, inclusive and sustainable economic growth, full and productive employment and decent work for all. Protect labour rights and promote safe and secure working environments for all workers.',
     '2025-12-13 09:34:15.5545', '2025-12-13 09:34:15.5545'),
    ('A101', '09', '產業創新與基礎設施', 'Industry, Innovation and Infrastructure',
     '建立具有韌性的基礎設施，促進包容且永續的工業化，並加速創新。發展可靠、永續且具韌性的基礎設施，促進產業升級和創新。',
     'Build resilient infrastructure, promote inclusive and sustainable industrialization and foster innovation. Develop quality, reliable, sustainable and resilient infrastructure, promote industrial upgrading and innovation.',
     '2025-12-13 09:34:15.5545', '2025-12-13 09:34:15.5545'),
    ('A101', '10', '減少不平等', 'Reduced Inequalities',
     '減少國內及國家間的不平等。促進社會、經濟和政治包容，確保機會平等，減少結果不平等，消除歧視性的法律、政策和做法。',
     'Reduce inequality within and among countries. Promote social, economic and political inclusion, ensure equal opportunity and reduce inequalities of outcome, eliminate discriminatory laws, policies and practices.',
     '2025-12-13 09:34:15.5545', '2025-12-13 09:34:15.5545'),
    ('A101', '11', '永續城市與社區', 'Sustainable Cities and Communities',
     '建構具包容、安全、韌性及永續特質的城市與鄉村。確保所有人獲得適當、安全和負擔得起的住房，改善貧民窟，提供安全的交通系統。',
     'Make cities and human settlements inclusive, safe, resilient and sustainable. Ensure access for all to adequate, safe and affordable housing, upgrade slums, provide safe and affordable transport systems.',
     '2025-12-13 09:34:15.5545', '2025-12-13 09:34:15.5545'),
    ('A101', '12', '負責任的消費與生產', 'Responsible Consumption and Production',
     '確保永續消費及生產模式。實現自然資源的永續管理和有效利用，減少糧食浪費，妥善管理化學品和廢棄物，大幅減少廢棄物的產生。',
     'Ensure sustainable consumption and production patterns. Achieve sustainable management and efficient use of natural resources, reduce food waste, manage chemicals and waste responsibly, substantially reduce waste generation.',
     '2025-12-13 09:34:15.5545', '2025-12-13 09:34:15.5545'),
    ('A101', '13', '氣候行動', 'Climate Action',
     '採取緊急措施以因應氣候變遷及其影響。將應對氣候變化的措施納入國家政策、戰略和規劃，提高氣候變化減緩、適應、減少影響和預警能力。',
     'Take urgent action to combat climate change and its impacts. Integrate climate change measures into national policies, strategies and planning, improve capacity on climate change mitigation, adaptation, impact reduction and early warning.',
     '2025-12-13 09:34:15.5545', '2025-12-13 09:34:15.5545'),
    ('A101', '14', '保育海洋生態', 'Life Below Water',
     '保育及永續利用海洋生態系，以確保生物多樣性並防止海洋環境劣化。預防和大幅減少各類海洋污染，永續管理和保護海洋和沿海生態系統。',
     'Conserve and sustainably use the oceans, seas and marine resources for sustainable development. Prevent and significantly reduce marine pollution, sustainably manage and protect marine and coastal ecosystems.',
     '2025-12-13 09:34:15.5545', '2025-12-13 09:34:15.5545'),
    ('A101', '15', '保育陸域生態', 'Life on Land',
     '保育及永續利用陸域生態系，確保生物多樣性並防止土地劣化。保護、恢復和促進陸地生態系統的永續利用，永續管理森林，防治荒漠化。',
     'Protect, restore and promote sustainable use of terrestrial ecosystems, sustainably manage forests, combat desertification, halt and reverse land degradation and halt biodiversity loss.',
     '2025-12-13 09:34:15.5545', '2025-12-13 09:34:15.5545'),
    ('A101', '16', '和平正義與健全制度', 'Peace, Justice and Strong Institutions',
     '促進和平且包容的社會，提供司法管道，建立有效且負責的體制。大幅減少各種暴力和相關死亡，促進法治，確保公共機構的透明和問責。',
     'Promote peaceful and inclusive societies for sustainable development, provide access to justice for all and build effective, accountable and inclusive institutions. Reduce violence, promote rule of law, ensure transparent institutions.',
     '2025-12-13 09:34:15.5545', '2025-12-13 09:34:15.5545'),
    ('A101', '17', '全球夥伴', 'Partnerships for the Goals',
     '建立多元夥伴關係，協力促進永續願景。加強全球夥伴關係，調動和分享知識、專業技術、技術和財政資源，支持各國實現永續發展目標。',
     'Strengthen the means of implementation and revitalize the Global Partnership for Sustainable Development. Strengthen global partnership, mobilize and share knowledge, expertise, technology and financial resources to support achieving SDGs.',
     '2025-12-13 09:15:25.798757', '2025-12-13 09:34:15.5545'),
]

def parse_timestamp(ts_str):
    """解析時間戳字串為 datetime 物件"""
    try:
        # 處理 PostgreSQL 格式的時間戳
        # '2025-12-13 09:15:25.798757' -> datetime
        if '.' in ts_str:
            dt_str, micro = ts_str.split('.')
            dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            # 添加微秒（只取前6位）
            dt = dt.replace(microsecond=int(micro[:6].ljust(6, '0')[:6]))
        else:
            dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
        return dt
    except Exception as e:
        print(f"警告: 無法解析時間戳 '{ts_str}': {e}")
        return datetime.now()

def import_data():
    """匯入資料到 Oracle 資料庫"""
    try:
        print("🔌 連接到 Oracle 資料庫...")
        conn = oracledb.connect(user=USERNAME, password=PASSWORD, dsn=DSN)
        cursor = conn.cursor()
        print("✅ 連線成功！\n")
        
        conn.autocommit = False
        
        print(f"📝 開始匯入 {len(data)} 筆 SDGs 細項主題資料...\n")
        
        success_count = 0
        update_count = 0
        skip_count = 0
        
        for theme_code, sub_theme_code, sub_theme_name, sub_theme_english_name, \
            sub_theme_content, sub_theme_english_content, created_at_str, updated_at_str in data:
            
            try:
                # 解析時間戳
                created_at = parse_timestamp(created_at_str)
                updated_at = parse_timestamp(updated_at_str)
                
                # 先通過 theme_code 獲取 theme_id
                cursor.execute("""
                    SELECT id FROM coures_themes WHERE theme_code = :1
                """, (theme_code,))
                theme_result = cursor.fetchone()
                if not theme_result:
                    print(f"  ❌ 錯誤: 主題代碼 '{theme_code}' 不存在")
                    continue
                coures_themes_id = theme_result[0]
                
                # 檢查是否已存在
                cursor.execute("""
                    SELECT COUNT(*) FROM coures_sub_themes
                    WHERE coures_themes_id = :1 AND sub_theme_code = :2
                """, (coures_themes_id, sub_theme_code))
                
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    # 更新現有記錄
                    cursor.execute("""
                        UPDATE coures_sub_themes
                        SET sub_theme_name = :1,
                            sub_theme_english_name = :2,
                            sub_theme_content = :3,
                            sub_theme_english_content = :4,
                            updated_at = :5,
                            updated_by = :6
                        WHERE coures_themes_id = :7 AND sub_theme_code = :8
                    """, (sub_theme_name, sub_theme_english_name, sub_theme_content, 
                          sub_theme_english_content, updated_at, None, coures_themes_id, sub_theme_code))
                    update_count += 1
                    print(f"  ✓ 更新: {sub_theme_code} - {sub_theme_name}")
                else:
                    # 插入新記錄（使用 UUID）
                    import uuid
                    sub_theme_id = str(uuid.uuid4())
                    
                    cursor.execute("""
                        INSERT INTO coures_sub_themes
                        (id, coures_themes_id, sub_theme_code, sub_theme_name, sub_theme_english_name,
                         sub_theme_content, sub_theme_english_content, created_at, updated_at, created_by, updated_by)
                        VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11)
                    """, (sub_theme_id, coures_themes_id, sub_theme_code, sub_theme_name, sub_theme_english_name,
                          sub_theme_content, sub_theme_english_content, created_at, updated_at, None, None))
                    success_count += 1
                    print(f"  ✓ 新增: {sub_theme_code} - {sub_theme_name}")
                    
            except Exception as e:
                error_str = str(e)
                if 'ORA-00001' in error_str or 'unique constraint' in error_str.lower():
                    skip_count += 1
                    print(f"  ℹ️  跳過: {sub_theme_code} - {sub_theme_name} (已存在)")
                else:
                    print(f"  ❌ 錯誤: {sub_theme_code} - {sub_theme_name}: {error_str[:100]}")
        
        # 提交變更
        conn.commit()
        
        print(f"\n" + "=" * 60)
        print(f"📊 匯入結果:")
        print(f"  ✓ 新增: {success_count} 筆")
        print(f"  ✓ 更新: {update_count} 筆")
        print(f"  ℹ️  跳過: {skip_count} 筆")
        print(f"  📝 總計: {len(data)} 筆")
        print("=" * 60)
        
        # 驗證
        cursor.execute("""
            SELECT COUNT(*) FROM coures_sub_themes st
            JOIN coures_themes t ON st.coures_themes_id = t.id
            WHERE t.theme_code = 'A101'
        """)
        total_count = cursor.fetchone()[0]
        print(f"\n✅ A101 主題的細項主題總數: {total_count}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False

if __name__ == "__main__":
    print("🚀 開始匯入 SDGs 細項主題資料...")
    print("=" * 60)
    print()
    
    success = import_data()
    
    if success:
        print("\n✅ 匯入完成！")
        exit(0)
    else:
        print("\n❌ 匯入失敗")
        exit(1)




