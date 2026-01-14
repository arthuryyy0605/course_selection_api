# CSV 匯出功能 API 變更文件

## 變更日期

2025-12-26

## 變更概述

新增支援篩選條件的 CSV 匯出 API，可從 COFOPMS 獲取完整課程資訊。

---

## 新增 API

### POST `/school-years/export-csv`

**用途**: 匯出課程資料為 CSV，支援多種篩選條件

**HTTP Method**: `POST`

**Content-Type**: `application/json`

#### Request Body

```json
{
  "academic_year_start": 114, // 必填：學年期起（學年）
  "academic_term_start": 1, // 必填：學年期起（學期）
  "academic_year_end": 114, // 必填：學年期訖（學年）
  "academic_term_end": 1, // 必填：學年期訖（學期）
  "department": "U36", // 可選：開課單位代碼
  "has_class": "Y", // 可選：成班與否 (Y/N)
  "theme_code": "A101", // 可選：主題代碼（過濾有填寫該主題的課程）
  "sub_theme_code": "01" // 可選：細項主題代碼（過濾有填寫該細項的課程）
}
```

#### 參數說明

| 參數                  | 類型   | 必填 | 說明                                       |
| --------------------- | ------ | ---- | ------------------------------------------ |
| `academic_year_start` | int    | ✓    | 學年期起（學年），例如: 114                |
| `academic_term_start` | int    | ✓    | 學年期起（學期），1=上學期, 2=下學期       |
| `academic_year_end`   | int    | ✓    | 學年期訖（學年），例如: 114                |
| `academic_term_end`   | int    | ✓    | 學年期訖（學期），1=上學期, 2=下學期       |
| `department`          | string |      | 開課單位代碼（對應 COFOPMS.OPMS_SET_DEPT） |
| `has_class`           | string |      | 成班與否，"Y" 或 "N"                       |
| `theme_code`          | string |      | 主題代碼，例如 "A101"、"A301"、"A401" 等   |
| `sub_theme_code`      | string |      | 細項主題代碼                               |

#### Response

- **Content-Type**: `text/csv; charset=utf-8-sig`
- **Content-Disposition**: `attachment; filename=course_entries_{start}_{end}.csv`

回傳 CSV 檔案下載。

#### CSV 欄位說明

| 欄位名稱              | 資料來源                                  | 說明                   |
| --------------------- | ----------------------------------------- | ---------------------- |
| 序號                  | 自動生成                                  | 流水號                 |
| 學年期                | COFOPMS.OPMS_ACADM_YEAR + OPMS_ACADM_TERM | 例如: "1141"           |
| 選課號碼              | COFOPMS.OPMS_SERIAL_NO                    |                        |
| 開課系所              | DEPTTRAN.SNAME                            | JOIN DEPTTRAN          |
| 科目內碼              | COFOPMS.OPMS_COURSE_NO                    |                        |
| 課程名稱              | COFSUBJ.SUBJ_CHN_NAME                     | JOIN COFSUBJ           |
| 教師姓名              | PSFEMPL.EMPL_CHN_NAME                     | JOIN PERSON.PSFEMPL    |
| 學分                  | COFOPMS.OPMS_CREDIT                       |                        |
| 選課人數              | COFOPMS.OPMS_SEL_STUDENTS                 |                        |
| 開課人數              | COFOPMS.OPMS_STUDENTS                     |                        |
| 成班與否              | COFOPMS.OPMS_CODE                         | Y/N                    |
| 必選修                | COFOPMS.OPMS_COURSE_KIND                  | 1→ 必修, 2→ 選修       |
| 全/半年               | COFOPMS.OPMS_KIND_CODE                    | 1→ 半年, 2→ 全年       |
| 是否合班              | COFOPMS.OPMS_CLASS_GROUP                  | Y 表示合班             |
| 授課群                | COFOPMS.OPMS_TEACHER_GROUP                | Y/N                    |
| 英文 EMI              | COFOPMS.OPMS_ENGLISH_GROUP                | Y/N                    |
| 課程含自主學習        | COFOPMS.OPMS_AGREE                        | Y/N                    |
| {主題簡稱}-最相關     | course_entries                            | 該主題最相關的細項名稱 |
| {主題簡稱}-{細項名稱} | course_entries.indicator_value            | 勾選值 (L/M/H 或 Y/N)  |

---

## 原有 API（保留向後兼容）

### GET `/school-years/{academic_year}/{academic_term}/export-csv`

**說明**: 舊版 API，不含 COFOPMS 完整欄位，建議使用新版 POST API。

**變更**: 無變更，保持向後兼容。

---

## 前端修改指南

### 1. 新增匯出表單頁面

建議新增一個匯出表單頁面，包含以下篩選元件：

```html
<!-- 篩選表單範例 -->
<form id="exportForm">
  <!-- 學年期起 -->
  <div>
    <label>學年期起:</label>
    <input
      type="number"
      name="academic_year_start"
      required
      placeholder="114"
    />
    <select name="academic_term_start" required>
      <option value="1">上學期</option>
      <option value="2">下學期</option>
    </select>
  </div>

  <!-- 學年期訖 -->
  <div>
    <label>學年期訖:</label>
    <input type="number" name="academic_year_end" required placeholder="114" />
    <select name="academic_term_end" required>
      <option value="1">上學期</option>
      <option value="2">下學期</option>
    </select>
  </div>

  <!-- 開課單位（下拉選單） -->
  <div>
    <label>開課單位:</label>
    <select name="department">
      <option value="">全部</option>
      <!-- 從 DEPTTRAN 獲取選項 -->
    </select>
  </div>

  <!-- 成班與否 -->
  <div>
    <label>成班與否:</label>
    <select name="has_class">
      <option value="">全部</option>
      <option value="Y">已成班</option>
      <option value="N">未成班</option>
    </select>
  </div>

  <!-- 主題名稱（下拉選單） -->
  <div>
    <label>主題名稱:</label>
    <select name="theme_code">
      <option value="">全部</option>
      <option value="A101">SDGs 聯合國永續發展目標</option>
      <option value="A301">主題(指標主題)</option>
      <option value="A401">UCAN 共通職能</option>
      <option value="A501">USR 大學社會責任</option>
      <option value="A601">STEAM</option>
    </select>
  </div>

  <!-- 細項主題名稱（聯動下拉選單） -->
  <div>
    <label>細項主題名稱:</label>
    <select name="sub_theme_code">
      <option value="">全部</option>
      <!-- 根據選擇的主題動態載入 -->
    </select>
  </div>

  <button type="submit">匯出 CSV</button>
</form>
```

### 2. JavaScript 呼叫範例

```javascript
// 匯出 CSV 函數
async function exportCSV() {
  const formData = {
    academic_year_start: parseInt(
      document.querySelector('[name="academic_year_start"]').value
    ),
    academic_term_start: parseInt(
      document.querySelector('[name="academic_term_start"]').value
    ),
    academic_year_end: parseInt(
      document.querySelector('[name="academic_year_end"]').value
    ),
    academic_term_end: parseInt(
      document.querySelector('[name="academic_term_end"]').value
    ),
  };

  // 可選欄位
  const department = document.querySelector('[name="department"]').value;
  const has_class = document.querySelector('[name="has_class"]').value;
  const theme_code = document.querySelector('[name="theme_code"]').value;
  const sub_theme_code = document.querySelector(
    '[name="sub_theme_code"]'
  ).value;

  if (department) formData.department = department;
  if (has_class) formData.has_class = has_class;
  if (theme_code) formData.theme_code = theme_code;
  if (sub_theme_code) formData.sub_theme_code = sub_theme_code;

  try {
    const response = await fetch("/api/school-years/export-csv", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "匯出失敗");
    }

    // 下載 CSV 檔案
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `course_entries_${formData.academic_year_start}${formData.academic_term_start}_${formData.academic_year_end}${formData.academic_term_end}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
  } catch (error) {
    alert("匯出失敗: " + error.message);
  }
}

// 綁定表單提交事件
document.getElementById("exportForm").addEventListener("submit", (e) => {
  e.preventDefault();
  exportCSV();
});
```

### 3. React/Vue 範例

#### React 範例

```jsx
import { useState } from "react";

function ExportCSVForm() {
  const [filters, setFilters] = useState({
    academic_year_start: 114,
    academic_term_start: 1,
    academic_year_end: 114,
    academic_term_end: 1,
    department: "",
    has_class: "",
    theme_code: "",
    sub_theme_code: "",
  });
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    setLoading(true);

    // 過濾空值
    const payload = Object.fromEntries(
      Object.entries(filters).filter(([_, v]) => v !== "")
    );

    try {
      const response = await fetch("/api/school-years/export-csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) throw new Error("匯出失敗");

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `course_entries.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      alert(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* 表單欄位... */}
      <button onClick={handleExport} disabled={loading}>
        {loading ? "匯出中..." : "匯出 CSV"}
      </button>
    </div>
  );
}
```

### 4. 錯誤處理

API 可能回傳以下錯誤：

| HTTP Status | 錯誤訊息                       | 說明                   |
| ----------- | ------------------------------ | ---------------------- |
| 404         | 沒有找到符合條件的課程資料     | 篩選條件沒有匹配的資料 |
| 404         | 學年 X 學期 Y 沒有找到主題設定 | 該學年期沒有主題設定   |
| 500         | 匯出 CSV 失敗: {error}         | 伺服器錯誤             |

---

## 開課單位代碼對照表

前端可呼叫資料庫查詢或使用以下常見代碼：

| 代碼 | 名稱           |
| ---- | -------------- |
| U32  | 園藝學系       |
| U36  | 昆蟲學系       |
| U37  | 動物科學系     |
| U39  | 土壤環境科學系 |
| U42  | 水土保持學系   |
| U52  | 生命科學系     |
| U63  | 環境工程學系   |
| ...  | ...            |

建議：從 `SCHOOL.DEPTTRAN` 表格查詢完整的系所對照表。

---

## 主題代碼對照表

| 代碼 | 名稱                    | 簡稱  |
| ---- | ----------------------- | ----- |
| A101 | SDGs 聯合國永續發展目標 | SDGs  |
| A301 | 主題(指標主題)          | 主題  |
| A401 | UCAN 共通職能           | UCAN  |
| A501 | USR 大學社會責任        | USR   |
| A601 | STEAM                   | STEAM |

---

## 測試建議

1. **基本測試**: 只填寫必填欄位（學年期起訖）進行匯出
2. **篩選測試**: 測試各種篩選條件組合
3. **邊界測試**: 測試跨學年期匯出（例如 1141 到 1142）
4. **錯誤測試**: 測試無資料情況的錯誤處理
