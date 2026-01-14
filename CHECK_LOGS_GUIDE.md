# 檢查 API 日誌指南

## 快速檢查

執行以下命令來檢查服務器上的 API 日誌：

```bash
./check_api_logs.sh
```

或者指定服務器地址和用戶：

```bash
./check_api_logs.sh 140.120.3.145 hostadm
```

## 手動檢查步驟

### 1. SSH 連接到服務器

```bash
ssh hostadm@140.120.3.145
```

### 2. 檢查服務狀態

```bash
sudo systemctl status course-selection-api.service
```

### 3. 查看應用日誌（實時）

```bash
# 查看所有日誌
sudo journalctl -u course-selection-api.service -f

# 只查看包含 "verify" 的日誌
sudo journalctl -u course-selection-api.service -f | grep -i verify

# 查看最近的 100 行日誌
sudo journalctl -u course-selection-api.service -n 100

# 查看錯誤級別的日誌
sudo journalctl -u course-selection-api.service -p err -n 50
```

### 4. 查看 Nginx 日誌

```bash
# Nginx 錯誤日誌
sudo tail -f /var/log/nginx/course_selection_api_error.log

# Nginx 訪問日誌（查找 verify 請求）
sudo tail -f /var/log/nginx/course_selection_api_access.log | grep verify

# 查看最近的 verify 請求
sudo grep -i verify /var/log/nginx/course_selection_api_access.log | tail -20
```

### 5. 檢查進程狀態

```bash
# 查看 uvicorn 進程
ps aux | grep uvicorn

# 查看端口監聽
sudo netstat -tlnp | grep 8000
# 或
sudo ss -tlnp | grep 8000
```

### 6. 測試 API 並同時查看日誌

在一個終端查看日誌：

```bash
sudo journalctl -u course-selection-api.service -f
```

在另一個終端測試 API：

```bash
curl -X POST "http://140.120.3.145/api/token/verify" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "token": "test"}' \
  -v
```

## 常見問題診斷

### 問題 1: 服務未運行

如果服務未運行，啟動服務：

```bash
sudo systemctl start course-selection-api.service
sudo systemctl status course-selection-api.service
```

### 問題 2: 服務崩潰

查看崩潰原因：

```bash
sudo journalctl -u course-selection-api.service -n 100 --no-pager
```

### 問題 3: 請求沒有到達應用

檢查 Nginx 配置和日誌：

```bash
# 檢查 Nginx 配置
sudo nginx -t

# 查看 Nginx 錯誤日誌
sudo tail -50 /var/log/nginx/course_selection_api_error.log

# 重啟 Nginx
sudo systemctl restart nginx
```

### 問題 4: 應用收到請求但沒有響應

查看應用日誌中的錯誤：

```bash
# 查看最近的錯誤
sudo journalctl -u course-selection-api.service -p err -n 50

# 查看所有日誌
sudo journalctl -u course-selection-api.service -n 200
```

## 日誌級別

日誌配置在 `course_selection_api/lib/logger.py` 中，默認級別是 INFO。

如果需要更詳細的日誌，可以設置環境變數：

```bash
# 在 .env 文件中添加
LOGGING_LEVEL=DEBUG
```

然後重啟服務：

```bash
sudo systemctl restart course-selection-api.service
```

## 日誌位置總結

- **應用日誌**: systemd journal (`journalctl -u course-selection-api.service`)
- **Nginx 訪問日誌**: `/var/log/nginx/course_selection_api_access.log`
- **Nginx 錯誤日誌**: `/var/log/nginx/course_selection_api_error.log`

## 下一步

根據日誌內容，我們可以：

1. 確認請求是否到達服務器
2. 確認請求是否到達應用
3. 確認應用是否處理請求
4. 確認是否有錯誤發生
5. 確認響應是否發送

請執行檢查腳本或手動檢查，然後分享日誌內容，我可以幫你分析問題。
