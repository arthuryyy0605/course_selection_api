#!/bin/bash
# 檢查 API 日誌腳本
# 用於查看服務器上的 API 日誌，特別是 verify API 的問題

VM_HOST="${1:-140.120.3.145}"
SSH_USER="${2:-hostadm}"

echo "=========================================="
echo "檢查 API 日誌 - Verify API 問題診斷"
echo "=========================================="
echo "服務器: $SSH_USER@$VM_HOST"
echo ""

# 檢查 SSH 連接
if ! ssh -o ConnectTimeout=5 "$SSH_USER@$VM_HOST" "echo 'SSH 連接成功'" 2>/dev/null; then
    echo "錯誤：無法連接到 $SSH_USER@$VM_HOST"
    exit 1
fi

echo "1. 檢查服務狀態..."
echo "----------------------------------------"
ssh "$SSH_USER@$VM_HOST" "sudo systemctl status course-selection-api.service --no-pager -l | head -20"
echo ""

echo "2. 查看最近的應用日誌（最後 50 行，包含 verify）..."
echo "----------------------------------------"
ssh "$SSH_USER@$VM_HOST" "sudo journalctl -u course-selection-api.service -n 50 --no-pager | grep -i verify || sudo journalctl -u course-selection-api.service -n 50 --no-pager"
echo ""

echo "3. 查看最近的錯誤日誌..."
echo "----------------------------------------"
ssh "$SSH_USER@$VM_HOST" "sudo journalctl -u course-selection-api.service -p err -n 30 --no-pager"
echo ""

echo "4. 查看 Nginx 錯誤日誌（最後 30 行）..."
echo "----------------------------------------"
ssh "$SSH_USER@$VM_HOST" "sudo tail -30 /var/log/nginx/course_selection_api_error.log 2>/dev/null || echo 'Nginx 錯誤日誌文件不存在'"
echo ""

echo "5. 查看 Nginx 訪問日誌中的 verify 請求（最後 20 行）..."
echo "----------------------------------------"
ssh "$SSH_USER@$VM_HOST" "sudo tail -100 /var/log/nginx/course_selection_api_access.log 2>/dev/null | grep -i verify | tail -20 || echo '未找到 verify 相關請求'"
echo ""

echo "6. 檢查服務是否正在運行..."
echo "----------------------------------------"
ssh "$SSH_USER@$VM_HOST" "ps aux | grep -E 'uvicorn|fastapi|course_selection' | grep -v grep || echo '未找到相關進程'"
echo ""

echo "7. 檢查端口監聽情況..."
echo "----------------------------------------"
ssh "$SSH_USER@$VM_HOST" "sudo netstat -tlnp | grep 8000 || sudo ss -tlnp | grep 8000 || echo '端口 8000 未監聽'"
echo ""

echo "=========================================="
echo "實時監控日誌（按 Ctrl+C 退出）"
echo "=========================================="
echo "執行以下命令查看實時日誌："
echo ""
echo "  ssh $SSH_USER@$VM_HOST 'sudo journalctl -u course-selection-api.service -f'"
echo ""
echo "或查看包含 verify 的日誌："
echo ""
echo "  ssh $SSH_USER@$VM_HOST 'sudo journalctl -u course-selection-api.service -f | grep -i verify'"
echo ""


