#!/bin/bash
# 本地 CI/CD 監控腳本
# 定期執行測試並記錄結果

set -e

WORKSPACE="/home/openclaw/.openclaw/workspace-stock/hello-bob"
LOG_DIR="$WORKSPACE/ci_logs"
REPORT_FILE="$WORKSPACE/ci_report.json"

mkdir -p "$LOG_DIR"

echo "========================================"
echo "🤖 本地 CI/CD 監控啟動"
echo "========================================"
echo "工作目錄：$WORKSPACE"
echo "日誌目錄：$LOG_DIR"
echo ""

# 執行測試
cd "$WORKSPACE"
python3 local_ci.py

# 保存結果
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp "$REPORT_FILE" "$LOG_DIR/report_$TIMESTAMP.json" 2>/dev/null || true

echo ""
echo "========================================"
echo "✅ CI/CD 流程完成"
echo "========================================"
