# Token 認證使用指南

## 概述

本系統在所有 `create` 和 `update` API 操作中新增了簡單的 token 認證機制，用於追蹤資料的創建者和修改者。

## Token 生成方式

Token 使用 **MD5** 加密生成，包含當前日期：

```
token = MD5(user_id + "nchu" + 年月日)
```

其中年月日格式為 `YYYYMMDD`（例如：20251211）

## 使用方法

### 1. 生成 Token

使用 Python 生成 token 範例：

```python
import hashlib
from datetime import datetime

def generate_token(user_id: str) -> str:
    """生成認證 token"""
    current_date = datetime.now().strftime('%Y%m%d')
    content = f"{user_id}nchu{current_date}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()

# 範例
user_id = "user123"
token = generate_token(user_id)
print(f"Token: {token}")
```

使用 JavaScript/Node.js 生成 token 範例：

```javascript
const crypto = require("crypto");

function generateToken(userId) {
  const currentDate = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const content = userId + "nchu" + currentDate;
  return crypto.createHash("md5").update(content).digest("hex");
}

// 範例
const userId = "user123";
const token = generateToken(userId);
console.log(`Token: ${token}`);
```

### 2. API 請求範例

#### 創建主題 (Create Theme)

```bash
curl -X POST "http://localhost:8000/themes/" \
  -H "Content-Type: application/json" \
  -d '{
    "theme_code": "A101",
    "theme_name": "聯合國全球永續發展目標",
    "theme_short_name": "SDGs",
    "theme_english_name": "SDGs",
    "chinese_link": "https://globalgoals.tw/",
    "english_link": null,
    "user_id": "user123",
    "token": "e10adc3949ba59abbe56e057f20f883e"
  }'
```

#### 更新主題 (Update Theme)

```bash
curl -X PUT "http://localhost:8000/themes/A101" \
  -H "Content-Type: application/json" \
  -d '{
    "theme_name": "聯合國全球永續發展目標 - 更新",
    "theme_short_name": "SDGs",
    "theme_english_name": "SDGs - Updated",
    "user_id": "user123",
    "token": "e10adc3949ba59abbe56e057f20f883e"
  }'
```

#### 創建學年期主題設定 (Create School Year Theme Setting)

```bash
curl -X POST "http://localhost:8000/school-year-theme-settings" \
  -H "Content-Type: application/json" \
  -d '{
    "school_year_semester": "1132",
    "theme_code": "A101",
    "fill_in_week_enabled": true,
    "scale_max": 5,
    "user_id": "user123",
    "token": "e10adc3949ba59abbe56e057f20f883e"
  }'
```

## 資料庫欄位

所有主要表格都新增了以下欄位：

- `created_by`: 記錄創建者的 user_id
- `updated_by`: 記錄最後修改者的 user_id

### 影響的表格

1. `themes` - 主題表
2. `sub_themes` - 細項主題表
3. `school_year_theme_settings` - 學年期主題設定表
4. `school_year_sub_theme_settings` - 學年期細項主題設定表
5. `course_entries` - 課程填寫記錄表

## 資料庫遷移

執行以下 SQL 腳本以新增必要欄位：

```bash
psql -U your_username -d your_database -f add_audit_fields.sql
```

## 錯誤處理

### Token 驗證失敗

如果 token 驗證失敗，API 會返回：

```json
{
  "detail": "Token 驗證失敗"
}
```

HTTP 狀態碼：`401 Unauthorized`

### 常見錯誤原因

1. **Token 不正確**：user_id 與 token 不匹配
2. **缺少參數**：未提供 user_id 或 token
3. **格式錯誤**：token 格式不符合 MD5 格式

## 測試工具

### Python 測試腳本

```python
import requests
import hashlib
from datetime import datetime

def generate_token(user_id: str) -> str:
    current_date = datetime.now().strftime('%Y%m%d')
    content = f"{user_id}nchu{current_date}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def create_theme(base_url: str, user_id: str):
    token = generate_token(user_id)

    data = {
        "theme_code": "TEST01",
        "theme_name": "測試主題",
        "theme_short_name": "測試",
        "theme_english_name": "Test Theme",
        "user_id": user_id,
        "token": token
    }

    response = requests.post(f"{base_url}/themes/", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

# 使用範例
create_theme("http://localhost:8000", "user123")
```

## DELETE 操作 Token 驗證

所有 DELETE 操作現在都需要提供 user_id 和 token：

### 刪除主題範例

```bash
curl -X DELETE "http://localhost:8000/themes/A101" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "token": "e10adc3949ba59abbe56e057f20f883e"
  }'
```

### 刪除學年期主題設定範例

```bash
curl -X DELETE "http://localhost:8000/school-year-theme-settings/1132/A101" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "token": "e10adc3949ba59abbe56e057f20f883e"
  }'
```

## Token 驗證 API

用於前端確認用戶登入狀態：

```bash
curl -X POST "http://localhost:8000/token/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "token": "e10adc3949ba59abbe56e057f20f883e"
  }'
```

回應：

```json
{
  "result": {
    "valid": true
  }
}
```

## 課程記錄檢查 API

檢查指定課程在指定學年期是否已有填寫記錄：

```bash
curl -X GET "http://localhost:8000/course-entries/exists?course_id=CS101&school_year_semester=1132"
```

回應：

```json
{
  "exists": true
}
```

## 課程資料複製功能

將課程記錄從一個學年期複製到另一個學年期：

```bash
curl -X POST "http://localhost:8000/course-entries/copy" \
  -H "Content-Type: application/json" \
  -d '{
    "source_school_year_semester": "1131",
    "target_school_year_semester": "1132",
    "course_id": "CS101",
    "user_id": "user123",
    "token": "e10adc3949ba59abbe56e057f20f883e"
  }'
```

回應：

```json
{
  "message": "成功複製 5 筆課程記錄到學年期 1132",
  "copied_count": 5,
  "skipped_count": 2,
  "deleted_count": 3
}
```

### 複製邏輯說明

1. **驗證 Token**：確認操作者身份
2. **檢查來源資料**：確認來源學年期有該課程的填寫記錄
3. **過濾目標設定**：只複製目標學年期有啟用的 theme/sub_theme
4. **刪除舊資料**：如果目標學年期已有該課程資料，先刪除
5. **複製記錄**：逐筆複製，更新 created_by 和 updated_by 為當前用戶
6. **返回統計**：
   - `copied_count`: 成功複製的記錄數
   - `skipped_count`: 跳過的記錄數（目標學年期無此設定）
   - `deleted_count`: 刪除的舊記錄數

## 注意事項

1. **安全性**：此 token 機制主要用於追蹤操作者，不應作為主要的身份驗證機制
2. **Token 有效期**：Token 包含日期資訊，每天會不同，增加安全性
3. **唯讀操作**：查詢 (GET) 操作不需要提供 user_id 和 token
4. **刪除操作**：所有 DELETE 操作現在都需要 token 認證
5. **複製時事務性**：複製過程中的刪除和插入在同一連線中執行
6. **時區考量**：Token 使用伺服器端的當前日期生成，請確保客戶端和伺服器端時區一致

## 與現有認證系統的關係

此 token 認證是**獨立於** JWT 認證系統的：

- **JWT 認證**：用於登入、會話管理、權限控制
- **MD5 Token**：用於追蹤資料的創建者和修改者

兩個系統可以並存使用，互不干擾。
