#!/bin/bash
# 配置 HTTPS (SSL) 的腳本
# 在虛擬機上執行：bash setup_https.sh

set -e

echo "=========================================="
echo "配置 HTTPS (SSL)"
echo "=========================================="
echo ""

DOMAIN="140.120.3.145"
NGINX_CONFIG="/etc/nginx/sites-available/course_selection_api"

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. 檢查 Certbot 是否安裝
echo "1. 檢查 Certbot..."
if ! command -v certbot &> /dev/null; then
    echo "安裝 Certbot..."
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
    echo -e "${GREEN}✓ Certbot 已安裝${NC}"
else
    echo -e "${GREEN}✓ Certbot 已安裝${NC}"
fi
echo ""

# 2. 檢查證書是否已存在
echo "2. 檢查現有證書..."
if [ -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
    echo -e "${GREEN}✓ SSL 證書已存在${NC}"
    echo "證書位置: /etc/letsencrypt/live/$DOMAIN/"
    ls -la /etc/letsencrypt/live/$DOMAIN/
else
    echo -e "${YELLOW}⚠ SSL 證書不存在${NC}"
    echo ""
    echo "選項："
    echo "  1. 使用 Let's Encrypt 申請證書（需要域名可訪問）"
    echo "  2. 使用自簽名證書（僅用於測試）"
    echo "  3. 取消"
    echo ""
    read -p "請選擇 (1/2/3): " choice
    
    case $choice in
        1)
            echo "申請 Let's Encrypt 證書..."
            echo "注意：需要提供有效的 email 地址"
            read -p "請輸入 email 地址: " email
            
            if [ -z "$email" ]; then
                echo -e "${RED}✗ Email 地址不能為空${NC}"
                exit 1
            fi
            
            # 申請證書
            sudo certbot certonly --nginx \
                -d $DOMAIN \
                --non-interactive \
                --agree-tos \
                --email "$email" \
                --preferred-challenges http || {
                echo -e "${RED}✗ 證書申請失敗${NC}"
                echo "可能原因："
                echo "  1. 域名無法從外部訪問（防火牆未開放）"
                echo "  2. 域名解析問題"
                echo "  3. Let's Encrypt 無法驗證域名"
                exit 1
            }
            ;;
        2)
            echo "生成自簽名證書（僅用於測試）..."
            sudo mkdir -p /etc/letsencrypt/live/$DOMAIN
            
            # 生成自簽名證書
            sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout /etc/letsencrypt/live/$DOMAIN/privkey.pem \
                -out /etc/letsencrypt/live/$DOMAIN/fullchain.pem \
                -subj "/C=TW/ST=State/L=City/O=Organization/CN=$DOMAIN"
            
            echo -e "${GREEN}✓ 自簽名證書已生成${NC}"
            echo -e "${YELLOW}注意：瀏覽器會顯示安全警告，這是正常的${NC}"
            ;;
        3)
            echo "取消操作"
            exit 0
            ;;
        *)
            echo "無效選擇"
            exit 1
            ;;
    esac
fi
echo ""

# 3. 配置 Nginx 使用 HTTPS
echo "3. 配置 Nginx 使用 HTTPS..."
if [ -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
    # 備份當前配置
    sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    
    # 創建 HTTPS 配置
    sudo tee "$NGINX_CONFIG" > /dev/null << EOF
# Nginx 配置：HTTP 和 HTTPS
# 部署位置：/etc/nginx/sites-available/course_selection_api

# HTTP 伺服器（重定向到 HTTPS）
server {
    listen 80;
    listen [::]:80;
    server_name _;

    # Let's Encrypt 驗證路徑
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # 其他所有請求重定向到 HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS 伺服器配置
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name _;

    # SSL 證書配置
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 日誌配置
    access_log /var/log/nginx/course_selection_api_access.log;
    error_log /var/log/nginx/course_selection_api_error.log;

    # 客戶端請求體大小限制
    client_max_body_size 10M;

    # API 路徑反向代理到 FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        
        # 保留原始主機和協議信息
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;

        # WebSocket 支持（如果需要）
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超時設置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # 緩衝區設置
        proxy_buffering off;
    }

    # 健康檢查端點
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # 根路徑
    location / {
        return 404;
    }
}
EOF

    echo -e "${GREEN}✓ Nginx 配置已更新${NC}"
else
    echo -e "${RED}✗ SSL 證書不存在，無法配置 HTTPS${NC}"
    exit 1
fi
echo ""

# 4. 測試配置
echo "4. 測試 Nginx 配置..."
if sudo nginx -t; then
    echo -e "${GREEN}✓ 配置語法正確${NC}"
else
    echo -e "${RED}✗ 配置語法有錯誤${NC}"
    exit 1
fi
echo ""

# 5. 重新載入 Nginx
echo "5. 重新載入 Nginx..."
sudo systemctl reload nginx
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Nginx 已重新載入${NC}"
else
    echo -e "${RED}✗ Nginx 重新載入失敗${NC}"
    exit 1
fi
echo ""

# 6. 檢查端口監聽
echo "6. 檢查端口監聽..."
echo "端口 443 (HTTPS):"
if sudo ss -tlnp | grep -q ":443"; then
    echo -e "${GREEN}✓ 端口 443 正在監聽${NC}"
    sudo ss -tlnp | grep ":443"
else
    echo -e "${RED}✗ 端口 443 未監聽${NC}"
fi
echo ""

# 7. 測試連接
echo "7. 測試連接..."
echo "測試 HTTPS (localhost):"
if curl -k -s -o /dev/null -w "%{http_code}" --connect-timeout 2 https://localhost/health | grep -q "200"; then
    echo -e "${GREEN}✓ 本地 HTTPS 連接正常${NC}"
else
    echo -e "${YELLOW}⚠ 本地 HTTPS 連接異常${NC}"
fi
echo ""

# 8. 總結
echo "=========================================="
echo "HTTPS 配置完成"
echo "=========================================="
echo ""
echo "測試命令："
echo "  # 使用 -k 參數跳過證書驗證（自簽名證書）"
echo "  curl -k https://$DOMAIN/health"
echo "  curl -k https://$DOMAIN/api/themes/"
echo ""
echo -e "${YELLOW}重要提醒：${NC}"
echo "  1. 如果使用自簽名證書，瀏覽器會顯示安全警告"
echo "  2. 確保雲服務商安全組已開放端口 443"
echo "  3. Let's Encrypt 證書會自動續期"
echo ""
echo "檢查安全組規則："
echo "  - 端口 443 (HTTPS) 必須開放"
echo "  - 端口 80 (HTTP) 用於重定向，也建議開放"







