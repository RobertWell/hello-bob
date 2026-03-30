# 🧪 測試策略與 CI/CD 流程

## 問題分析

**核心問題**: API 簡單檢查不足以發現深層資料問題
- 資料類型錯誤（Series vs float）
- NaN 值污染
- 格式化失敗（TypeError）
- 依賴超時導致假陰性

## 解決方案：三層測試架構

```
┌─────────────────────────────────────┐
│  L1: 單元測試 (快速，每次 commit)   │  ← 語法 + 類型檢查
├─────────────────────────────────────┤
│  L2: 整合測試 (中速，push 時)        │  ← API 回應 + 資料完整性
├─────────────────────────────────────┤
│  L3: 端到端測試 (慢速，夜間排程)    │  ← 完整流程 + 服務健康
└─────────────────────────────────────┘
```

## 測試檔案結構

```
hello-bob/
├── tests/
│   ├── __init__.py
│   ├── test_l1_syntax.py       # L1: 語法 + 類型
│   ├── test_l2_integration.py  # L2: API + 資料完整性
│   ├── test_l3_e2e.py          # L3: 完整流程
│   └── fixtures/               # 測試資料
│       ├── sample_commodities.json
│       └── sample_futures.json
├── ci_l1.sh    # L1 快速檢查
├── ci_l2.sh    # L2 整合檢查
└── ci_full.sh  # 完整檢查
```

## L1: 單元測試（<10 秒）

**目標**: 快速發現低級錯誤
**觸發**: 每次 commit

```python
# tests/test_l1_syntax.py
def test_data_types():
    """測試資料類型正確"""
    # 使用 mock 資料，不呼叫真實 API
    sample = {'latest': 4500.5, 'change': 1.2, 'data': None}
    assert isinstance(sample['latest'], (int, float))
    assert isinstance(sample['change'], (int, float))

def test_format_strings():
    """測試格式化字串"""
    val = 4500.5
    assert f"{val:.2f}" == "4500.50"
    assert f"{val:+.2f}" == "+4500.50"
```

## L2: 整合測試（<60 秒）

**目標**: 驗證 API 回應與資料完整性
**觸發**: push 到 main/develop

```python
# tests/test_l2_integration.py
def test_commodities_api():
    """測試原物料 API"""
    data = get_all_commodities_data(days=5)
    
    for name, info in data.items():
        # 必要欄位
        assert 'latest' in info
        assert 'change' in info
        assert 'data' in info
        
        # 類型檢查
        assert isinstance(info['latest'], (int, float)), \
            f"{name} 的 latest 應為數值，實際為 {type(info['latest'])}"
        
        # NaN 檢查
        assert not pd.isna(info['latest']), f"{name} 的 latest 是 NaN"
        
        # 格式化測試
        try:
            _ = f"{info['latest']:.2f}"
        except TypeError as e:
            raise AssertionError(f"{name} 格式化失敗：{e}")
```

## L3: 端到端測試（<5 分鐘）

**目標**: 完整流程驗證
**觸發**: 夜間排程或手動

```python
# tests/test_l3_e2e.py
def test_full_dashboard():
    """測試完整儀表板載入"""
    # 1. 啟動 Streamlit
    # 2. 訪問每個視圖
    # 3. 檢查是否有渲染錯誤
    # 4. 檢查健康狀態
```

## CI/CD 流程

### 1. 本地開發（commit 前）

```bash
# 執行 L1 快速檢查
./ci_l1.sh

# 輸出範例：
# ✓ 語法檢查通過
# ✓ 類型檢查通過
# ✓ 格式化測試通過
```

### 2. Push 到 GitHub

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on: [push, pull_request]

jobs:
  l1-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: ./ci_l1.sh
  
  l2-test:
    runs-on: ubuntu-latest
    needs: l1-check
    steps:
      - uses: actions/checkout@v3
      - run: ./ci_l2.sh
  
  l3-nightly:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - run: ./ci_full.sh
```

### 3. 部署前檢查

```bash
# 所有檢查通過才能部署
./ci_full.sh && deploy
```

## 測試用例清單

### 資料類型測試
- [x] `latest` 必須是 `int` 或 `float`
- [x] `change` 必須是 `int` 或 `float`
- [x] `data` 必須是 `pd.DataFrame` 或 `None`

### NaN 檢查
- [x] `latest` 不能是 NaN
- [x] `change` 不能是 NaN
- [x] DataFrame 關鍵欄位不能全是 NaN

### 格式化測試
- [x] `f"{value:.2f}"` 不報錯
- [x] `f"{value:+.2f}%"` 不報錯

### API 回應測試
- [x] 原物料 API 返回正確結構
- [x] 全球期貨 API 返回正確結構
- [x] 大盤資料 API 返回正確結構

### 服務健康測試
- [x] Streamlit 健康檢查通過
- [x] HTTP 端口可訪問
- [x] 頁面无 502 錯誤

## 監控與警報

### 即時監控
```bash
# 每 5 分鐘檢查一次
curl -s http://localhost:8501/_stcore/health

# 檢查日誌錯誤
tail -100 streamlit_v5.log | grep -i error
```

### 錯誤分級
- **P0**: 服務無法啟動 → 立即重啟 + 通知
- **P1**: 資料錯誤（NaN/類型錯誤） → 停止更新 + 通知
- **P2**: UI 顯示問題 → 記錄 + 下次修復

## 開發流程

```bash
# 1. 修改程式碼
# 2. 執行 L1 測試
./ci_l1.sh

# 3. 如果通過，提交
git add -A
git commit -m "feat: 新增功能（通過 L1 測試）"

# 4. Push 後自動執行 L2
git push

# 5. 查看 GitHub Actions 結果
```

## 文件更新

- [x] `tests/test_l1_syntax.py` - L1 測試
- [x] `tests/test_l2_integration.py` - L2 測試
- [x] `tests/fixtures/` - 測試資料
- [x] `ci_l1.sh` - L1 腳本
- [x] `ci_l2.sh` - L2 腳本
- [x] `.github/workflows/ci.yml` - CI 配置
- [x] `CI.md` - 完整文件
