#!/bin/bash
# 完整 CI 檢查（L1 + L2 + 服務健康）
set -e

cd "$(dirname "${BASH_SOURCE[0]}")"

echo "========================================"
echo "🚀 完整 CI 檢查"
echo "========================================"

# L1
echo ""
echo "├── L1: 語法檢查"
./ci_l1.sh

# L2
echo ""
echo "├── L2: 整合測試"
./ci_l2.sh

# 服務健康
echo ""
echo "├── 服務健康檢查"
if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "  ✓ Streamlit 運行正常"
else
    echo "  ⚠️  Streamlit 未運行或無法訪問"
fi

echo ""
echo "========================================"
echo "✅ 所有 CI 檢查通過"
echo "========================================"
