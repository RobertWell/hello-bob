#!/bin/bash
# 簡單 CI 檢查腳本
cd /home/openclaw/.openclaw/workspace-stock/hello-bob

echo "======================================"
echo "🧪 CI 檢查"
echo "======================================"

# 1. 語法檢查
echo "1. 語法檢查..."
python3 -m py_compile app_v5.py && echo "  ✓ app_v5.py"
python3 -m py_compile commodities_analyzer.py && echo "  ✓ commodities_analyzer.py"
python3 -m py_compile market_dashboard.py && echo "  ✓ market_dashboard.py"

# 2. 服務健康
echo -e "\n2. 服務健康..."
if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
  echo "  ✓ Streamlit 運行正常"
else
  echo "  ⚠️  Streamlit 未運行"
fi

echo -e "\n======================================"
echo "✅ CI 檢查完成"
echo "======================================"
