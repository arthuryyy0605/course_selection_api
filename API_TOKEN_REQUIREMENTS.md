# API Token 需求快速參考表

## 📊 所有 API Token 需求總覽

### ✅ 需要 Token 的 API（必須提供 user_id 和 token）

| HTTP 方法 | Endpoint | 說明 | Request Body 需要 |
|-----------|----------|------|------------------|
| **POST** | `/themes/` | 創建主題 | ✅ user_id, token |
| **PUT** | `/themes/{theme_code}` | 更新主題 | ✅ user_id, token |
| **DELETE** | `/themes/{theme_code}` | 刪除主題 | ✅ user_id, token |
| **POST** | `/sub_themes/` | 創建細項主題 | ✅ user_id, token |
| **PUT** | `/sub_themes/{theme_code}/{sub_theme_code}` | 更新細項主題 | ✅ user_id, token |
| **DELETE** | `/sub_themes/{theme_code}/{sub_theme_code}` | 刪除細項主題 | ✅ user_id, token |
| **POST** | `/school-year-theme-settings` | 創建學年期主題設定 | ✅ user_id, token |
| **PUT** | `/school-year-theme-settings/{school_year_semester}/{theme_code}` | 更新學年期主題設定 | ✅ user_id, token |
| **DELETE** | `/school-year-theme-settings/{school_year_semester}/{theme_code}` | 刪除學年期主題設定 | ✅ user_id, token |
| **POST** | `/school-year-sub-theme-settings` | 創建學年期細項設定 | ✅ user_id, token |
| **PUT** | `/school-year-sub-theme-settings/{...}/{theme_code}/{sub_theme_code}` | 更新學年期細項設定 | ✅ user_id, token |
| **DELETE** | `/school-year-sub-theme-settings/{...}/{theme_code}/{sub_theme_code}` | 刪除學年期細項設定 | ✅ user_id, token |
| **POST** | `/course-entries/single` | 創建單一課程記錄 | ✅ user_id, token |
| **POST** | `/course-entries` | 批量創建課程記錄 | ✅ user_id, token（外層） |
| **PUT** | `/course-entries/{entry_id}` | 更新課程記錄 | ✅ user_id, token |
| **POST** | `/course-entries/copy` | 複製課程記錄 | ✅ user_id, token |

### ⭕ 不需要 Token 的 API（唯讀操作）

| HTTP 方法 | Endpoint | 說明 |
|-----------|----------|------|
| **GET** | `/themes/` | 獲取所有主題 |
| **GET** | `/sub_themes/` | 獲取所有細項主題 |
| **GET** | `/sub_themes/by_theme/{theme_code}` | 獲取指定主題的細項 |
| **GET** | `/school-year-theme-settings/{school_year_semester}` | 獲取學年期主題設定 |
| **GET** | `/school-year-theme-settings/{school_year_semester}/{theme_code}` | 獲取特定設定 |
| **GET** | `/school-year-sub-theme-settings/{school_year_semester}/{theme_code}` | 獲取細項設定 |
| **GET** | `/school-years/{school_year_semester}` | 獲取學年期完整資訊 |
| **GET** | `/courses/{course_id}/school-years/{school_year_semester}/form-data` | 獲取表單資料 |
| **GET** | `/course-entries/exists` | 檢查課程記錄是否存在 |
| **GET** | `/school-years/{...}/themes/{...}/sub-themes/{...}/courses` | 查詢課程列表 |
| **POST** | `/token/verify` | 驗證 token（此 API 本身用於驗證） |

---

## 🔑 Token 使用規則

### 規則 1: 所有寫入操作都需要 Token
- ✅ CREATE (POST)
- ✅ UPDATE (PUT)
- ✅ DELETE (DELETE)

### 規則 2: 所有讀取操作不需要 Token
- ⭕ READ (GET)

### 規則 3: Token 位置
- **CREATE/UPDATE**: 在 request body 中加入 `user_id` 和 `token`
- **DELETE**: 在 request body 中加入 `user_id` 和 `token`（⚠️ 注意：DELETE 也需要 body）

---

## 📋 特殊案例說明

### 批量創建課程記錄 (`POST /course-entries`)

**注意：** user_id 和 token 只需要在**最外層**提供，不用在每個 entry 中重複：

```javascript
// ✅ 正確寫法
{
  "entries": [
    { "course_id": "CS101", "theme_code": "A101", ... },
    { "course_id": "CS101", "theme_code": "A201", ... }
  ],
  "user_id": "user123",      // 只在這裡提供一次
  "token": "xxx"              // 只在這裡提供一次
}

// ❌ 錯誤寫法（不需要在每個 entry 中加）
{
  "entries": [
    { "course_id": "CS101", "user_id": "user123", "token": "xxx", ... }, // 多餘
    { "course_id": "CS101", "user_id": "user123", "token": "xxx", ... }  // 多餘
  ],
  "user_id": "user123",
  "token": "xxx"
}
```

---

## 🎯 前端實作優先順序

### 🔴 高優先級（必須完成）
1. **修改所有 DELETE 請求** - 加入 request body
2. **課程填寫功能** - 創建和更新都需要 token
3. **Token 生成功能** - 實作 MD5(user_id + "nchu" + 年月日)
4. **Token 管理** - 儲存和管理 user_id 和 token

### 🟡 中優先級（建議完成）
5. **Token 驗證 API** - 在應用初始化時驗證登入狀態
6. **課程記錄檢查** - 顯示課程是否已填寫

### 🟢 低優先級（增強使用體驗）
7. **課程複製功能** - 跨學年期複製課程記錄

---

## 🚨 重要提醒

**所有寫入操作（CREATE、UPDATE、DELETE）都必須提供 user_id 和 token！**

如果缺少這兩個欄位，API 將返回：
- **422 Unprocessable Entity**（缺少必要欄位）
- **401 Unauthorized**（token 驗證失敗）

---

## 📞 快速聯絡

- 完整文檔：`FRONTEND_API_CHANGES.md`
- Token 使用指南：`TOKEN_AUTH_GUIDE.md`
- API 測試範例：`test_token_auth.py`
- Swagger 文檔：http://localhost:8000/docs

