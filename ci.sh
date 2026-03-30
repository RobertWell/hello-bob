#!/bin/bash
# CI/CD 流水線 - 自動化測試與品質檢查
# 使用方式：./ci.sh 或 ./ci.sh --verbose

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 輸出函數
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✓  $1${NC}"; }
log_error() { echo -e "${RED}✗  $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# 錯誤處理
handle_error() {
    log_error "流水線失敗於：$1"
    exit 1
}

# 步驟 1: 環境檢查
step_check_env() {
    log_info "步驟 1/5: 環境檢查..."
    
    # 檢查 Python
    if ! command -v python3 &> /dev/null; then
        handle_error "未找到 Python3"
    fi
    log_success "Python3: $(python3 --version)"
    
    # 檢查必要套件
    python3 -c "import pandas, numpy, yfinance, plotly, streamlit" || handle_error "缺少必要套件"
    log_success "必要套件已安裝"
}

# 步驟 2: 語法檢查
step_syntax() {
    log_info "步驟 2/5: 語法檢查..."
    
    for file in app_v5.py commodities_analyzer.py market_dashboard.py ptt_sentiment.py; do
        if [ -f "$file" ]; then
            python3 -m py_compile "$file" || handle_error "$file 語法錯誤"
            log_success "$file 語法正確"
        fi
    done
}

# 步驟 3: 執行測試
step_test() {
    log_info "步驟 3/5: 執行測試..."
    
    if [ -f "tests/test_all.py" ]; then
        python3 tests/test_all.py || handle_error "測試失敗"
        log_success "所有測試通過"
    else
        log_warn "找不到測試檔案，跳過"
    fi
}

# 步驟 4: 服務健康檢查
step_health() {
    log_info "步驟 4/5: 服務健康檢查..."
    
    # 檢查 Streamlit
    if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        log_success "Streamlit 運行正常"
    else
        log_warn "Streamlit 未運行或無法訪問"
    fi
    
    # 檢查 Worker
    if pgrep -f "worker.py" > /dev/null 2>&1; then
        log_success "Worker 運行正常"
    else
        log_warn "Worker 未運行"
    fi
}

# 步驟 5: 資料完整性檢查
step_data_integrity() {
    log_info "步驟 5/5: 資料完整性檢查..."
    
    python3 << 'EOF'
import sys
sys.path.append('/home/openclaw/.openclaw/workspace-stock/hello-bob')
from commodities_analyzer import get_all_commodities_data, get_all_futures_data

# 快速測試
comm = get_all_commodities_data(days=5)
for name, info in comm.items():
    assert isinstance(info['latest'], (int, float)), f"{name} 資料類型錯誤"
    assert not str(info['latest']).lower() == 'nan', f"{name} 包含 NaN"

fut = get_all_futures_data(days=5)
for name, info in fut.items():
    assert isinstance(info['latest'], (int, float)), f"{name} 資料類型錯誤"
    assert not str(info['latest']).lower() == 'nan', f"{name} 包含 NaN"

print("資料完整性檢查通過")
EOF
    log_success "資料完整性檢查通過"
}

# 主程式
main() {
    echo "========================================"
    echo "🚀 CI/CD 流水線啟動"
    echo "========================================"
    echo ""
    
    START_TIME=$(date +%s)
    
    step_check_env
    echo ""
    
    step_syntax
    echo ""
    
    step_test
    echo ""
    
    step_health
    echo ""
    
    step_data_integrity
    echo ""
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo "========================================"
    log_success "✅ 所有檢查通過！"
    echo "⏱️  執行時間：${DURATION}秒"
    echo "========================================"
}

# 執行
main "$@"
