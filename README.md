# 課程選擇系統 API

基於 FastAPI 框架開發的課程主題維護與管理系統。
ssh hostadm@140.120.3.145
hy12345
# 資料庫設定（Oracle）
db_host=140.120.3.90
db_port=1521
db_user=schoolsdgs
db_password=Sdgs2025
db_name=nchu

## 專案結構

```
course_selection_api/
├── course_selection_api/          # 主要應用程式目錄
│   ├── __init__.py
│   ├── main.py                    # FastAPI 應用程式入口
│   ├── config.py                  # 配置設定
│   ├── endpoints/                 # API 端點
│   │   ├── __init__.py
│   │   ├── auth.py               # 認證相關 API
│   │   └── theme.py              # 主題管理 API
│   ├── business_model/           # 業務邏輯層
│   │   ├── __init__.py
│   │   ├── auth_business.py      # 認證業務邏輯
│   │   └── theme_business.py     # 主題業務邏輯
│   ├── data_access_object/       # 數據訪問層
│   │   ├── __init__.py
│   │   ├── db.py                 # 資料庫連接
│   │   ├── users_dao.py          # 用戶數據存取
│   │   └── theme_dao.py          # 主題數據存取
│   ├── schema/                   # Pydantic 資料模型
│   │   ├── __init__.py
│   │   ├── auth.py               # 認證相關模型
│   │   └── theme.py              # 主題相關模型
│   ├── lib/                      # 通用庫
│   │   ├── __init__.py
│   │   ├── auth_library/         # 認證庫
│   │   ├── base_exception.py     # 基礎異常
│   │   ├── dao_factory.py        # DAO 工廠
│   │   ├── logger.py             # 日誌處理
│   │   ├── response.py           # 回應格式
│   │   └── setting.py            # 設定處理
│   └── utils/                    # 工具函數
│       ├── __init__.py
│       ├── email_generator.py
│       └── privacy_protection.py
├── database_schema.sql           # 資料庫表格建立腳本
├── poetry.lock                   # Poetry 鎖定檔案
├── pyproject.toml               # 專案配置與依賴
└── README.md                    # 專案說明
```

## 功能特性

### 主題管理 (Section 1)

- **新增主題**: `POST /themes/`
- **查詢所有主題**: `GET /themes/`
- **更新主題**: `PUT /themes/{theme_code}`
- **刪除主題**: `DELETE /themes/{theme_code}`

### 細項主題管理 (Section 2)

- **查詢細項主題**: `GET /sub_themes/?school_year_semester={學年期}`
- **新增細項主題**: `POST /sub_themes/`
- **更新細項主題**: `PUT /sub_themes/{school_year_semester}/{theme_code}/{sub_theme_code}`
- **刪除細項主題**: `DELETE /sub_themes/{school_year_semester}/{theme_code}/{sub_theme_code}`

## 環境設定

### 環境變數

建立 `.env` 檔案並設定以下變數：

```env
# 資料庫設定
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=your_password
DB_NAME=course_selection

# API 文件設定（開發環境）
ENABLE_API_DOCS=true

# JWT 設定
JWT_PUBLIC_KEY=your_jwt_public_key
JWT_PRIVATE_KEY=your_jwt_private_key
```

### 資料庫設定

1. 安裝 PostgreSQL
2. 建立資料庫：
   ```sql
   CREATE DATABASE course_selection;
   ```
3. 執行資料庫結構腳本：
   ```bash
   psql -U postgres -d course_selection -f database_schema.sql
   ```

## 安裝與運行

### 使用 Poetry

1. 安裝依賴：

   ```bash
   poetry install
   ```

2. 運行開發伺服器：

   ```bash
   poetry run python -m course_selection_api.main
   ```

3. 或使用 uvicorn：
   ```bash
   poetry run uvicorn course_selection_api.main:app --reload --host 0.0.0.0 --port 8000
   ```

### 部署

根據記憶中的配置 [[memory:5334109]]，使用以下命令進行部署：

```bash
poetry run ./node_modules/.bin/serverless deploy
```

## API 文件

### 互動式文檔（開發環境）

當設定 `ENABLE_API_DOCS=true` 時，可以存取以下端點：

- **Swagger UI**: `http://localhost:8000/api/spec/doc`
- **ReDoc**: `http://localhost:8000/api/spec/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/spec/swagger.json`

### 前端整合文檔

為方便前端開發者快速對接 API，我們提供了完整的文檔：

#### 📚 主要文檔

- **[前端 API 更新指南 (2024)](FRONTEND_API_UPDATE_2024.md)** - 2024 年 API 變更說明，包含：
  - 課程識別欄位變更（移除 course_id，改為 subj_no 和 ps_class_nbr）
  - 最相關科目功能
  - 所有 API 端點的變更說明
  - 完整的 JavaScript 範例

#### 📖 參考資源

- **[Token 認證指南](TOKEN_AUTH_GUIDE.md)** - Token 生成和驗證的詳細說明
- **[Token 需求總覽](API_TOKEN_REQUIREMENTS.md)** - 哪些 API 需要 Token 的完整列表

## API 使用範例

### 創建主題

```bash
curl -X POST "http://localhost:8000/themes/" \
     -H "Content-Type: application/json" \
     -d '{
       "theme_code": "A101",
       "theme_name": "聯合國全球永續發展目標",
       "theme_short_name": "SDGs",
       "theme_english_name": "SDGs",
       "chinese_link": "https://globalgoals.tw/",
       "english_link": null
     }'
```

### 查詢所有主題

```bash
curl -X GET "http://localhost:8000/themes/"
```

### 更新主題

```bash
curl -X PUT "http://localhost:8000/themes/A101" \
     -H "Content-Type: application/json" \
     -d '{
       "theme_name": "更新後的主題名稱"
     }'
```

### 刪除主題

```bash
curl -X DELETE "http://localhost:8000/themes/A101"
```

### 查詢細項主題

```bash
curl -X GET "http://localhost:8000/sub_themes/?school_year_semester=1132"
```

### 創建細項主題

```bash
curl -X POST "http://localhost:8000/sub_themes/" \
     -H "Content-Type: application/json" \
     -d '{
       "school_year_semester": "1132",
       "theme_code": "A101",
       "sub_theme_code": "01",
       "sub_theme_name": "消除貧窮",
       "sub_theme_english_name": "No Poverty",
       "enabled": "Y",
       "fill_in_week_enabled": "Y"
     }'
```

## 業務邏輯規則

### 主題刪除限制

- 當主題有相關的細項主題時，無法刪除該主題
- 系統會自動檢查外鍵約束並回傳適當的錯誤訊息

### 細項主題刪除限制

- 當細項主題已有填寫相關資料時，無法刪除該細項主題
- 透過 `course_sub_theme_mapping` 表檢查是否有相關課程資料

## 錯誤處理

API 遵循 RESTful 原則，使用標準 HTTP 狀態碼：

- `200`: 成功
- `201`: 創建成功
- `400`: 請求錯誤（如業務邏輯限制）
- `404`: 資源不存在
- `409`: 衝突（如重複的主題代碼）
- `500`: 伺服器內部錯誤

錯誤回應格式：

```json
{
  "message": "錯誤訊息",
  "code": "錯誤代碼"
}
```

## 開發注意事項

1. **程式碼結構**: 專案採用分層架構，請遵循以下分層：

   - `endpoints`: API 端點定義
   - `business_model`: 業務邏輯處理
   - `data_access_object`: 資料存取層
   - `schema`: 資料模型定義
   - `lib`: 通用工具庫

2. **資料庫遷移**: 修改資料庫結構時，請更新 `database_schema.sql` 檔案

3. **測試**: 建議為每個業務邏輯添加適當的測試

4. **日誌**: 使用 `course_selection_api.lib.logger` 進行日誌記錄

## 授權

此專案依據相關授權條款發佈。
