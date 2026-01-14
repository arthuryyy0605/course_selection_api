-- Oracle 資料庫建表腳本 (課程選擇系統) - UUID ID 版本
-- 使用者: schoolsdgs_app
-- 資料庫: nchu
-- 注意: 此版本使用 UUID 作為主鍵，THEME_CODE 和 SUB_THEME_CODE 為可修改的顯示欄位

-- ============================================
-- 清理現有表格 (如果存在)
-- ============================================
BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE course_entries CASCADE CONSTRAINTS';
EXCEPTION
   WHEN OTHERS THEN NULL;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE academic_year_coures_sub_theme_settings CASCADE CONSTRAINTS';
EXCEPTION
   WHEN OTHERS THEN NULL;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE academic_year_coures_themes_setting CASCADE CONSTRAINTS';
EXCEPTION
   WHEN OTHERS THEN NULL;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE coures_sub_themes CASCADE CONSTRAINTS';
EXCEPTION
   WHEN OTHERS THEN NULL;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE coures_themes CASCADE CONSTRAINTS';
EXCEPTION
   WHEN OTHERS THEN NULL;
END;
/

-- 刪除序列 (不再需要，改用 UUID)
BEGIN
   EXECUTE IMMEDIATE 'DROP SEQUENCE seq_acad_year_themes_setting';
EXCEPTION
   WHEN OTHERS THEN NULL;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP SEQUENCE seq_acad_year_sub_themes';
EXCEPTION
   WHEN OTHERS THEN NULL;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP SEQUENCE seq_course_entries';
EXCEPTION
   WHEN OTHERS THEN NULL;
END;
/

-- ============================================
-- 創建主題表 (coures_themes)
-- ============================================
CREATE TABLE coures_themes (
    id VARCHAR2(36) PRIMARY KEY,
    theme_code VARCHAR2(10) NOT NULL,
    theme_name VARCHAR2(200) NOT NULL,
    theme_short_name VARCHAR2(50) NOT NULL,
    theme_english_name VARCHAR2(200) NOT NULL,
    chinese_link VARCHAR2(500),
    english_link VARCHAR2(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR2(50),
    updated_by VARCHAR2(50),
    CONSTRAINT uk_coures_themes_code UNIQUE (theme_code)
);

COMMENT ON TABLE coures_themes IS '課程主題表';
COMMENT ON COLUMN coures_themes.id IS '主題ID (UUID 主鍵)';
COMMENT ON COLUMN coures_themes.theme_code IS '主題代碼 (可修改的顯示欄位)';
COMMENT ON COLUMN coures_themes.theme_name IS '主題名稱';
COMMENT ON COLUMN coures_themes.theme_short_name IS '主題簡稱';
COMMENT ON COLUMN coures_themes.theme_english_name IS '主題英文名稱';
COMMENT ON COLUMN coures_themes.chinese_link IS '中文說明連結';
COMMENT ON COLUMN coures_themes.english_link IS '英文說明連結';

-- ============================================
-- 創建細項主題表 (coures_sub_themes)
-- ============================================
CREATE TABLE coures_sub_themes (
    id VARCHAR2(36) PRIMARY KEY,
    coures_themes_id VARCHAR2(36) NOT NULL,
    sub_theme_code VARCHAR2(10) NOT NULL,
    sub_theme_name VARCHAR2(200) NOT NULL,
    sub_theme_english_name VARCHAR2(200) NOT NULL,
    sub_theme_content CLOB,
    sub_theme_english_content CLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR2(50),
    updated_by VARCHAR2(50),
    CONSTRAINT fk_sub_themes_theme FOREIGN KEY (coures_themes_id) REFERENCES coures_themes(id),
    CONSTRAINT uk_sub_themes_code UNIQUE (coures_themes_id, sub_theme_code)
);

COMMENT ON TABLE coures_sub_themes IS '課程細項主題表';
COMMENT ON COLUMN coures_sub_themes.id IS '細項主題ID (UUID 主鍵)';
COMMENT ON COLUMN coures_sub_themes.coures_themes_id IS '主題ID (外鍵)';
COMMENT ON COLUMN coures_sub_themes.sub_theme_code IS '細項主題代碼 (顯示用，可修改)';
COMMENT ON COLUMN coures_sub_themes.sub_theme_name IS '細項主題名稱';
COMMENT ON COLUMN coures_sub_themes.sub_theme_english_name IS '細項主題英文名稱';
COMMENT ON COLUMN coures_sub_themes.sub_theme_content IS '細項主題中文內容說明';
COMMENT ON COLUMN coures_sub_themes.sub_theme_english_content IS '細項主題英文內容說明';

-- ============================================
-- 創建學年期主題設定表 (academic_year_coures_themes_setting)
-- ============================================
CREATE TABLE academic_year_coures_themes_setting (
    id VARCHAR2(36) PRIMARY KEY,
    academic_year NUMBER(3) NOT NULL,
    academic_term NUMBER(1) NOT NULL,
    coures_themes_id VARCHAR2(36) NOT NULL,
    fill_in_week_enabled CHAR(1) DEFAULT 'Y' NOT NULL CHECK (fill_in_week_enabled IN ('Y', 'N')),
    indicator_type VARCHAR2(10) DEFAULT 'LMH' NOT NULL CHECK (indicator_type IN ('LMH', 'SCALE', 'BOOLEAN')),
    scale_max NUMBER(2) DEFAULT 3 NOT NULL CHECK (scale_max >= 1 AND scale_max <= 10),
    select_most_relevant_sub_theme_enabled CHAR(1) DEFAULT 'N' NOT NULL CHECK (select_most_relevant_sub_theme_enabled IN ('Y', 'N')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR2(50),
    updated_by VARCHAR2(50),
    CONSTRAINT fk_acad_themes_setting_theme FOREIGN KEY (coures_themes_id) REFERENCES coures_themes(id),
    CONSTRAINT uk_acad_year_theme UNIQUE (academic_year, academic_term, coures_themes_id)
);

COMMENT ON TABLE academic_year_coures_themes_setting IS '學年期主題設定表';
COMMENT ON COLUMN academic_year_coures_themes_setting.id IS '設定ID (UUID 主鍵)';
COMMENT ON COLUMN academic_year_coures_themes_setting.academic_year IS '學年 (例: 114)';
COMMENT ON COLUMN academic_year_coures_themes_setting.academic_term IS '學期 (例: 1=上學期, 2=下學期)';
COMMENT ON COLUMN academic_year_coures_themes_setting.coures_themes_id IS '主題ID (外鍵)';
COMMENT ON COLUMN academic_year_coures_themes_setting.fill_in_week_enabled IS '是否需要填寫週次 (Y/N)';
COMMENT ON COLUMN academic_year_coures_themes_setting.indicator_type IS '指標類型: LMH(低中高)/SCALE(數字分數)/BOOLEAN(是否)';
COMMENT ON COLUMN academic_year_coures_themes_setting.scale_max IS '指標最大值';
COMMENT ON COLUMN academic_year_coures_themes_setting.select_most_relevant_sub_theme_enabled IS '是否需要讓使用者勾選最相關科目 (Y/N)';

-- ============================================
-- 創建學年期細項主題設定表 (academic_year_coures_sub_theme_settings)
-- ============================================
CREATE TABLE academic_year_coures_sub_theme_settings (
    id VARCHAR2(36) PRIMARY KEY,
    academic_year NUMBER(3) NOT NULL,
    academic_term NUMBER(1) NOT NULL,
    coures_sub_themes_id VARCHAR2(36) NOT NULL,
    enabled CHAR(1) DEFAULT 'Y' NOT NULL CHECK (enabled IN ('Y', 'N')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR2(50),
    updated_by VARCHAR2(50),
    CONSTRAINT fk_acad_sub_setting_sub_theme FOREIGN KEY (coures_sub_themes_id) REFERENCES coures_sub_themes(id),
    CONSTRAINT uk_acad_year_sub_theme UNIQUE (academic_year, academic_term, coures_sub_themes_id)
);

COMMENT ON TABLE academic_year_coures_sub_theme_settings IS '學年期細項主題設定表';
COMMENT ON COLUMN academic_year_coures_sub_theme_settings.id IS '設定ID (UUID 主鍵)';
COMMENT ON COLUMN academic_year_coures_sub_theme_settings.academic_year IS '學年';
COMMENT ON COLUMN academic_year_coures_sub_theme_settings.academic_term IS '學期';
COMMENT ON COLUMN academic_year_coures_sub_theme_settings.coures_sub_themes_id IS '細項主題ID (外鍵)';
COMMENT ON COLUMN academic_year_coures_sub_theme_settings.enabled IS '是否啟用 (Y/N)';

-- ============================================
-- 創建課程填寫記錄表 (course_entries)
-- ============================================
CREATE TABLE course_entries (
    id VARCHAR2(36) PRIMARY KEY,
    SUBJ_NO VARCHAR2(50) NOT NULL,
    PS_CLASS_NBR VARCHAR2(50) NOT NULL,
    ACADEMIC_YEAR NUMBER NOT NULL,
    ACADEMIC_TERM NUMBER NOT NULL,
    coures_sub_themes_id VARCHAR2(36) NOT NULL,
    indicator_value VARCHAR2(10) NOT NULL,
    week_numbers CLOB,
    is_most_relevant CHAR(1) DEFAULT 'N' NOT NULL CHECK (is_most_relevant IN ('Y', 'N')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR2(50),
    updated_by VARCHAR2(50),
    CONSTRAINT fk_course_entries_sub_theme FOREIGN KEY (coures_sub_themes_id) REFERENCES coures_sub_themes(id),
    CONSTRAINT uk_course_entries_subj_ps_year_term_sub UNIQUE (SUBJ_NO, PS_CLASS_NBR, ACADEMIC_YEAR, ACADEMIC_TERM, coures_sub_themes_id)
);

COMMENT ON TABLE course_entries IS '課程填寫記錄表';
COMMENT ON COLUMN course_entries.id IS '記錄ID (UUID 主鍵)';
COMMENT ON COLUMN course_entries.SUBJ_NO IS '課程代碼 (對應 COFSUBJ.SUBJ_NO，可直接 JOIN 取得課程名稱)';
COMMENT ON COLUMN course_entries.PS_CLASS_NBR IS '課程流水號 (對應 SCHOOL.COFOPMS.PS_CLASS_NBR)';
COMMENT ON COLUMN course_entries.ACADEMIC_YEAR IS '學年';
COMMENT ON COLUMN course_entries.ACADEMIC_TERM IS '學期';
COMMENT ON COLUMN course_entries.coures_sub_themes_id IS '細項主題ID (外鍵)';
COMMENT ON COLUMN course_entries.indicator_value IS '指標值 (可以是 L/M/H 或 數字 或 Y/N)';
COMMENT ON COLUMN course_entries.week_numbers IS '週次列表 (JSON 格式)';
COMMENT ON COLUMN course_entries.is_most_relevant IS '標記該 sub_theme 是否為該課程在該主題下最相關的細項 (Y/N)';

-- ============================================
-- 創建索引提升查詢效能
-- ============================================
-- 注意: idx_coures_themes_code 和 idx_sub_themes_code 不需要，因為 UNIQUE 約束會自動創建索引
CREATE INDEX idx_coures_themes_name ON coures_themes(theme_name);
CREATE INDEX idx_sub_themes_theme_id ON coures_sub_themes(coures_themes_id);
CREATE INDEX idx_acad_themes_year_term ON academic_year_coures_themes_setting(academic_year, academic_term);
CREATE INDEX idx_acad_themes_theme_id ON academic_year_coures_themes_setting(coures_themes_id);
CREATE INDEX idx_acad_sub_themes_year_term ON academic_year_coures_sub_theme_settings(academic_year, academic_term);
CREATE INDEX idx_acad_sub_themes_sub_theme_id ON academic_year_coures_sub_theme_settings(coures_sub_themes_id);
CREATE INDEX idx_course_entries_subj_no ON course_entries(SUBJ_NO);
CREATE INDEX idx_course_entries_ps_class_nbr ON course_entries(PS_CLASS_NBR);
CREATE INDEX idx_course_entries_sub_theme_id ON course_entries(coures_sub_themes_id);
CREATE INDEX idx_course_entries_year_term ON course_entries(ACADEMIC_YEAR, ACADEMIC_TERM);
CREATE INDEX idx_course_entries_most_relevant ON course_entries(SUBJ_NO, PS_CLASS_NBR, ACADEMIC_YEAR, ACADEMIC_TERM, is_most_relevant);

-- ============================================
-- 創建更新時間觸發器
-- ============================================
CREATE OR REPLACE TRIGGER trg_coures_themes_updated
BEFORE UPDATE ON coures_themes
FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER trg_sub_themes_updated
BEFORE UPDATE ON coures_sub_themes
FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER trg_acad_themes_updated
BEFORE UPDATE ON academic_year_coures_themes_setting
FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER trg_acad_sub_themes_updated
BEFORE UPDATE ON academic_year_coures_sub_theme_settings
FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER trg_course_entries_updated
BEFORE UPDATE ON course_entries
FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

-- ============================================
-- 完成
-- ============================================
SELECT 'Oracle tables created successfully with UUID IDs!' AS status FROM DUAL;
