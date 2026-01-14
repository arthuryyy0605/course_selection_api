# Verify API 修復指南

## 問題描述

`http://140.120.3.145/api/token/verify` API 卡住，沒有返回響應。

## 已修復的問題

### 1. 添加超時保護

- 使用 `asyncio.wait_for` 設置 5 秒超時
- 確保即使出現問題也能返回響應

### 2. 異步處理優化

- 使用 `asyncio.to_thread` 將同步函數轉為異步執行
- 避免阻塞事件循環

### 3. 輸入驗證

- 檢查 `user_id` 和 `token` 是否存在
- 提前返回，避免無效請求

### 4. 改進錯誤處理

- 區分不同類型的異常
- 添加詳細的日誌記錄（包括堆棧跟踪）

## 部署步驟

### 1. 重新部署到服務器

```bash
# 在專案根目錄執行
poetry run ./node_modules/.bin/serverless deploy
```

或者如果使用傳統部署方式：

```bash
# SSH 到服務器
ssh user@140.120.3.145

# 進入專案目錄
cd /path/to/course_selection_api

# 拉取最新代碼（如果使用 git）
git pull

# 重啟服務
sudo systemctl restart fastapi
# 或
sudo systemctl restart uvicorn
# 或根據你的部署方式重啟
```

### 2. 檢查服務器日誌

```bash
# 查看應用日誌
sudo journalctl -u fastapi -f
# 或
tail -f /var/log/fastapi/app.log
# 或根據你的日誌配置查看
```

### 3. 測試 API

#### 方法 1: 使用 curl

```bash
# 生成 token（Python）
python3 -c "
import hashlib
from datetime import datetime
user_id = 'test_user'
current_date = datetime.now().strftime('%Y%m%d')
content = f'{user_id}nchu{current_date}'
token = hashlib.md5(content.encode('utf-8')).hexdigest()
print(f'Token: {token}')
"

# 測試 verify API（替換 YOUR_TOKEN）
curl -X POST "http://140.120.3.145/api/token/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "token": "YOUR_TOKEN"
  }' \
  -v \
  --max-time 10
```

#### 方法 2: 使用 Python requests

```python
import requests
import hashlib
from datetime import datetime

def generate_token(user_id: str) -> str:
    current_date = datetime.now().strftime('%Y%m%d')
    content = f"{user_id}nchu{current_date}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()

# 測試
user_id = "test_user"
token = generate_token(user_id)

response = requests.post(
    "http://140.120.3.145/api/token/verify",
    json={"user_id": user_id, "token": token},
    timeout=10
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

### 4. 檢查服務器狀態

```bash
# 檢查服務是否運行
sudo systemctl status fastapi

# 檢查端口是否監聽
sudo netstat -tlnp | grep 8000
# 或
sudo ss -tlnp | grep 8000

# 檢查進程
ps aux | grep uvicorn
ps aux | grep fastapi
```

## 可能的其他問題

### 1. Nginx 配置問題

如果使用 Nginx 作為反向代理，檢查配置：

```bash
# 檢查 Nginx 配置
sudo nginx -t

# 查看 Nginx 錯誤日誌
sudo tail -f /var/log/nginx/error.log

# 重啟 Nginx
sudo systemctl restart nginx
```

### 2. 防火牆問題

確保端口已開放：

```bash
# 檢查防火牆規則
sudo ufw status
# 或
sudo firewall-cmd --list-all
```

### 3. 服務器資源問題

檢查服務器資源使用情況：

```bash
# 檢查 CPU 和內存
top
# 或
htop

# 檢查磁盤空間
df -h

# 檢查系統日誌
sudo dmesg | tail
```

## 調試建議

### 1. 啟用詳細日誌

確保日誌級別設置為 DEBUG 或 INFO，查看詳細的請求處理過程。

### 2. 檢查請求頭

確保請求包含正確的 Content-Type：

```
Content-Type: application/json
```

### 3. 檢查 CORS 設置

如果從瀏覽器發起請求，檢查 CORS 配置是否正確。

### 4. 直接測試服務器

繞過代理，直接測試應用：

```bash
# 如果應用運行在 8000 端口
curl -X POST "http://localhost:8000/api/token/verify" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "token": "test"}' \
  -v
```

## 預期響應

### 成功響應（Token 有效）

```json
{
  "result": {
    "valid": true
  }
}
```

### 失敗響應（Token 無效）

```json
{
  "result": {
    "valid": false
  }
}
```

## 如果問題仍然存在

1. **檢查服務器日誌**：查看是否有錯誤訊息
2. **檢查網絡連接**：確認服務器可訪問
3. **檢查服務狀態**：確認服務正在運行
4. **檢查依賴**：確認所有 Python 依賴已安裝
5. **重啟服務**：嘗試重啟整個服務

## 聯繫信息

如果問題持續存在，請提供：

- 服務器日誌
- 錯誤訊息
- 請求詳情（Headers, Body）
- 服務器配置信息
