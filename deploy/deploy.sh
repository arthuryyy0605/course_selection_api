#!/bin/bash
# 部署腳本：將 FastAPI 應用部署到正式虛擬機
# 使用方法：./deploy.sh [虛擬機IP] [SSH用戶名]
# 範例：./deploy.sh 140.120.3.145 hostadm

set -e

# 配置變數
VM_HOST="${1:-140.120.3.145}"
SSH_USER="${2:-hostadm}"
APP_DIR="~/backend_api"
DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$DEPLOY_DIR/.." && pwd)"

echo "=========================================="
echo "開始部署 FastAPI 應用到虛擬機"
echo "=========================================="
echo "虛擬機: $SSH_USER@$VM_HOST"
echo "應用目錄: $APP_DIR"
echo ""

# 檢查 SSH 連接
echo "檢查 SSH 連接..."
if ! ssh -o ConnectTimeout=5 "$SSH_USER@$VM_HOST" "echo 'SSH 連接成功'" 2>/dev/null; then
    echo "錯誤：無法連接到 $SSH_USER@$VM_HOST"
    echo "請確保："
    echo "1. SSH 金鑰已配置"
    echo "2. 虛擬機 IP 正確"
    echo "3. 防火牆允許 SSH 連接"
    exit 1
fi

# 上傳代碼
echo "上傳代碼到虛擬機..."
rsync -avz --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='*.log' \
    --exclude='node_modules' \
    "$PROJECT_DIR/" "$SSH_USER@$VM_HOST:$APP_DIR/"

# 在遠端執行部署步驟
echo "在遠端執行部署步驟..."
ssh "$SSH_USER@$VM_HOST" << 'ENDSSH'
set -e
cd ~/backend_api

echo "安裝 Python 依賴..."
# 確保 Poetry 在 PATH 中
export PATH="$HOME/.local/bin:$PATH"

# 確保 python 命令可用（安裝 python-is-python3）
if ! command -v python &> /dev/null; then
    echo "安裝 python-is-python3 以啟用 python 命令..."
    sudo apt-get update && sudo apt-get install -y python-is-python3
fi

# 安裝依賴
poetry install --without dev

# 清除 Python 緩存文件，確保使用最新代碼
echo "清除 Python 緩存文件..."
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# 檢查環境變數文件
if [ ! -f .env ]; then
    echo "警告：.env 文件不存在"
    echo "請從 env.template 創建 .env 文件並填入配置"
    echo "複製模板：cp deploy/env.template .env"
    echo "然後編輯 .env 文件"
    exit 1
fi

# 設置 systemd service
echo "設置 systemd service..."
# 檢測當前用戶（用於運行服務）
CURRENT_USER=$(whoami)
CURRENT_HOME=$(eval echo ~$CURRENT_USER)
# 創建臨時 service 文件，替換用戶名和路徑
sed "s|User=www-data|User=$CURRENT_USER|g; s|Group=www-data|Group=$CURRENT_USER|g; s|HOME_PATH|$CURRENT_HOME|g" deploy/fastapi.service | sudo tee /etc/systemd/system/course-selection-api.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable course-selection-api.service

# 配置 Nginx
echo "配置 Nginx..."
sudo cp deploy/nginx.conf /etc/nginx/sites-available/course_selection_api

# 檢查是否已啟用
if [ ! -L /etc/nginx/sites-enabled/course_selection_api ]; then
    sudo ln -s /etc/nginx/sites-available/course_selection_api /etc/nginx/sites-enabled/
fi

# 測試 Nginx 配置
sudo nginx -t

# 申請 SSL 證書（如果尚未申請）
if [ ! -f /etc/letsencrypt/live/140.120.3.145/fullchain.pem ]; then
    echo "申請 Let's Encrypt SSL 證書..."
    echo "注意：需要提供有效的 email 地址"
    echo "請手動運行：sudo certbot --nginx -d 140.120.3.145"
    echo "或修改此腳本中的 email 地址後重新運行"
    # sudo certbot certonly --nginx \
    #     -d 140.120.3.145 \
    #     --non-interactive \
    #     --agree-tos \
    #     --email your-email@example.com || echo "SSL 證書申請失敗，請手動申請"
else
    echo "SSL 證書已存在"
fi

# 重啟服務
echo "重啟服務..."
# 先停止服務，確保完全關閉
sudo systemctl stop course-selection-api.service || true
# 等待服務完全停止
sleep 2
# 啟動服務
sudo systemctl start course-selection-api.service
# 測試 Nginx 配置並重新載入（不中斷連接）
sudo nginx -t && sudo systemctl reload nginx || sudo systemctl restart nginx
# 等待服務啟動
sleep 3

# 檢查服務狀態
echo ""
echo "=========================================="
echo "服務狀態檢查"
echo "=========================================="
sudo systemctl status course-selection-api.service --no-pager -l || true
echo ""
sudo systemctl status nginx --no-pager -l || true

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo "API 端點：https://140.120.3.145/api/"
echo "健康檢查：https://140.120.3.145/health"
echo ""
echo "查看日誌："
echo "  sudo journalctl -u course-selection-api -f"
echo "  sudo tail -f /var/log/nginx/course_selection_api_error.log"
ENDSSH

echo ""
echo "=========================================="
echo "本地部署腳本執行完成"
echo "=========================================="

