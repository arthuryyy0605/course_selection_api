#!/bin/bash
# 設置 systemd service 腳本
# 在虛擬機上執行此腳本來設置 FastAPI 服務

set -e

echo "=========================================="
echo "設置 FastAPI systemd service"
echo "=========================================="

cd ~/backend_api

# 檢查必要文件
if [ ! -f deploy/fastapi.service ]; then
    echo "錯誤：找不到 deploy/fastapi.service 文件"
    exit 1
fi

# 檢測當前用戶和 home 目錄
CURRENT_USER=$(whoami)
CURRENT_HOME=$(eval echo ~$CURRENT_USER)

echo "當前用戶: $CURRENT_USER"
echo "Home 目錄: $CURRENT_HOME"
echo ""

# 創建 systemd service 文件
echo "創建 systemd service 文件..."
sed "s|User=www-data|User=$CURRENT_USER|g; s|Group=www-data|Group=$CURRENT_USER|g; s|HOME_PATH|$CURRENT_HOME|g" deploy/fastapi.service | sudo tee /etc/systemd/system/course-selection-api.service > /dev/null

# 重新載入 systemd
echo "重新載入 systemd daemon..."
sudo systemctl daemon-reload

# 啟用服務（開機自動啟動）
echo "啟用服務..."
sudo systemctl enable course-selection-api.service

# 顯示服務文件內容（確認）
echo ""
echo "Service 文件內容："
echo "----------------------------------------"
sudo cat /etc/systemd/system/course-selection-api.service

echo ""
echo "=========================================="
echo "Service 設置完成！"
echo "=========================================="
echo ""
echo "現在可以啟動服務："
echo "  sudo systemctl start course-selection-api"
echo ""
echo "檢查服務狀態："
echo "  sudo systemctl status course-selection-api"
echo ""
echo "查看日誌："
echo "  sudo journalctl -u course-selection-api -f"








