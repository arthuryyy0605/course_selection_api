# 部署指南

本目錄包含將 FastAPI 應用部署到正式虛擬機的配置文件和腳本。

## 文件說明

- `nginx.conf` - Nginx 反向代理配置，將 HTTPS 443 port 的 `/api` 路徑代理到 FastAPI 8000 port
- `fastapi.service` - Systemd service 文件，用於管理 FastAPI 應用
- `setup_server.sh` - 伺服器環境設置腳本（首次部署時運行）
- `deploy.sh` - 主部署腳本，自動化部署流程
- `env.template` - 環境變數模板文件

## 部署步驟

### 1. 首次部署：設置伺服器環境

在虛擬機上運行（或通過 SSH）：

```bash
# 上傳 setup_server.sh 到虛擬機
scp deploy/setup_server.sh user@140.120.3.145:~/

# SSH 到虛擬機並執行
ssh user@140.120.3.145
chmod +x setup_server.sh
./setup_server.sh
```

這個腳本會安裝：
- Python 3.12
- Poetry
- Nginx
- Certbot (Let's Encrypt)

### 2. 配置環境變數

在虛擬機上：

```bash
cd ~/backend_api
cp deploy/env.template .env
nano .env  # 編輯並填入實際配置值
```

### 3. 執行部署

從本地機器運行：

```bash
cd /Users/phoenix/Desktop/project/course_selection_api
./deploy/deploy.sh 140.120.3.145 [SSH用戶名]
```

部署腳本會：
1. 上傳代碼到 `~/backend_api`
2. 安裝 Python 依賴（使用 Poetry）
3. 設置 systemd service
4. 配置 Nginx
5. 申請 SSL 證書（如果尚未申請）
6. 重啟服務

### 4. 驗證部署

```bash
# 檢查服務狀態
ssh user@140.120.3.145
sudo systemctl status course-selection-api
sudo systemctl status nginx

# 測試 API
curl https://140.120.3.145/api/themes/
```

## 服務管理

### 啟動/停止/重啟 FastAPI 服務

```bash
sudo systemctl start course-selection-api
sudo systemctl stop course-selection-api
sudo systemctl restart course-selection-api
sudo systemctl status course-selection-api
```

### 查看日誌

```bash
# FastAPI 應用日誌
sudo journalctl -u course-selection-api -f

# Nginx 訪問日誌
sudo tail -f /var/log/nginx/course_selection_api_access.log

# Nginx 錯誤日誌
sudo tail -f /var/log/nginx/course_selection_api_error.log
```

### 重新載入 Nginx 配置

```bash
sudo nginx -t  # 測試配置
sudo systemctl reload nginx
```

## SSL 證書管理

### 手動申請證書

```bash
sudo certbot --nginx -d 140.120.3.145
```

### 更新證書（自動續期）

Let's Encrypt 證書會自動續期，也可以手動測試：

```bash
sudo certbot renew --dry-run
```

## 故障排除

### FastAPI 服務無法啟動

1. 檢查日誌：`sudo journalctl -u course-selection-api -n 50`
2. 檢查環境變數：確認 `.env` 文件存在且配置正確
3. 檢查 Poetry 環境：`poetry env info`

### Nginx 502 Bad Gateway

1. 檢查 FastAPI 服務是否運行：`sudo systemctl status course-selection-api`
2. 檢查 FastAPI 是否監聽 8000 port：`sudo netstat -tlnp | grep 8000`
3. 檢查 Nginx 錯誤日誌：`sudo tail -f /var/log/nginx/course_selection_api_error.log`

### SSL 證書問題

1. 檢查證書文件：`sudo ls -la /etc/letsencrypt/live/140.120.3.145/`
2. 重新申請證書：`sudo certbot --nginx -d 140.120.3.145`

## 架構說明

```
Internet (HTTPS 443)
    ↓
Nginx (反向代理)
    ↓ /api/*
FastAPI (localhost:8000)
```

- 外部訪問：`https://140.120.3.145/api/*`
- FastAPI 監聽：`http://127.0.0.1:8000`
- 所有 API 路由都有 `/api` 前綴

## 注意事項

1. 確保虛擬機防火牆開放 80 和 443 port
2. 確保 `.env` 文件包含正確的資料庫連接和 JWT 密鑰
3. 生產環境建議將 `ENABLE_API_DOCS` 設為 `false`
4. 定期備份環境變數和配置文件


