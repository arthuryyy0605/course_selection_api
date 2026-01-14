#!/bin/bash
# 伺服器環境設置腳本
# 在虛擬機上首次運行，安裝必要的依賴和工具

set -e

echo "=========================================="
echo "開始設置伺服器環境"
echo "=========================================="

# 更新系統套件
echo "更新系統套件..."
sudo apt-get update
sudo apt-get upgrade -y

# 安裝基本工具
echo "安裝基本工具..."
sudo apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    python-is-python3 \
    curl \
    git \
    nginx \
    certbot \
    python3-certbot-nginx

# 安裝 Poetry
echo "安裝 Poetry..."
if ! command -v poetry &> /dev/null; then
    curl -sSL https://install.python-poetry.org | python -
    export PATH="$HOME/.local/bin:$PATH"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
else
    echo "Poetry 已安裝"
fi

# 創建應用目錄（在用戶 home 目錄下）
echo "創建應用目錄..."
mkdir -p ~/backend_api

# 設置防火牆（如果使用 ufw）
if command -v ufw &> /dev/null; then
    echo "配置防火牆..."
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
fi

echo "=========================================="
echo "伺服器環境設置完成！"
echo "=========================================="
echo "請確保："
echo "1. Python 3.12 已安裝：$(python3.12 --version)"
echo "2. Poetry 已安裝：$(poetry --version 2>/dev/null || echo '未安裝')"
echo "3. Nginx 已安裝：$(nginx -v 2>&1)"
echo "4. Certbot 已安裝：$(certbot --version 2>/dev/null || echo '未安裝')"


