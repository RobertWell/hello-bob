# 🧪 本地 CI/CD 驗證系統

## 問題陳述

**核心問題**: API 簡單檢查不足以發現深層資料問題
- 資料類型錯誤（Series vs float）
- NaN 值污染
- 格式化失敗（TypeError）
- 依賴超時導致假陰性

## 解決方案：三層測試架構

```
┌─────────────────────────────────────┐
│  L1: 快速檢查 (<5 秒)                │  ← 語法 + 檔案完整性
├─────────────────────────────────────┤
│  L2: 資料驗證 (<30 秒)              │  ← API 回應 + 資料類型
├─────────────────────────────────────┤
│  L3: 服務健康 (<10 秒)              │  ← Streamlit 健康檢查
└─────────────────────────────────────┘
```

## 快速開始

### 1. 快速 CI 檢查（推薦）

```bash
cd /home/openclaw/.openclaw/workspace-stock/hello-bob
./check_ci.sh
```

**輸出範例**:
```
======================================
🧪 CI 檢查
======================================
1. 語法檢查...
  ✓ app_v5.py
  ✓ commodities_analyzer.py
  ✓ market_dashboard.py

2. 服務健康...
  ✓ Streamlit 運行正常

======================================
✅ CI 檢查完成
======================================
```

### 2. 完整驗證

```bash
python3 local_ci.py
```

### 3. 提交前自動檢查

Git hook 會自動執行 L1 檢查：
```bash
git commit -m "feat: 新增功能"
# 自動執行 pre-commit hook
```

## 測試清單

### L1: 快速檢查
- [x] Python 語法檢查
- [x] 必要檔案存在性
- [x] 模組導入測試
- [x] 基本格式化測試

### L2: 資料驗證
- [x] 原物料 API 回應結構
- [x] 全球期貨 API 回應結構
- [x] 資料類型檢查（int/float）
- [x] NaN 值檢測
- [x] 格式化測試（f-string）

### L3: 服務健康
- [x] Streamlit 健康檢查
- [x] HTTP 端口可訪問
- [x] 進程運行狀態

## 檔案結構

```
hello-bob/
├── check_ci.sh           # 快速 CI 檢查腳本
├── local_ci.py           # 完整 CI 驗證系統
├── run_ci.sh             # 定期監控腳本
├── CI.md                 # CI 流程文檔
├── TESTING.md            # 測試策略說明
├── CI_CD_GUIDE.md        # 本文件
├── .git/hooks/pre-commit # Git hook
└── tests/
    ├── test_l1_syntax.py     # L1 測試
    ├── test_l2_integration.py # L2 測試
    └── fixtures/             # 測試資料
```

## 開發流程

### 日常開發

```bash
# 1. 修改程式碼
# 2. 執行快速檢查
./check_ci.sh

# 3. 如果通過，提交
git add -A
git commit -m "feat: 新增功能"

# 4. 推送
git push
```

### 發布前驗證

```bash
# 執行完整驗證
python3 local_ci.py

# 檢查服務健康
curl http://localhost:8501/_stcore/health
```

## 錯誤處理

### P0: 嚴重錯誤（立即修復）
- 語法錯誤
- 服務無法啟動
- 關鍵模組缺失

### P1: 資料錯誤（停止更新）
- 資料類型錯誤
- NaN 值污染
- API 回應異常

### P2: 輕微問題（記錄跟蹤）
- UI 顯示問題
- 非關鍵警告
- 效能問題

## 監控與通知

### 即時監控
```bash
# 每 5 分鐘檢查一次
curl -s http://localhost:8501/_stcore/health

# 檢查日誌
tail -100 streamlit_v5.log | grep -i error
```

### 定期報告
```bash
# 每天執行一次完整檢查
0 8 * * * /home/openclaw/.openclaw/workspace-stock/hello-bob/run_ci.sh
```

## 與 GitHub Actions 比較

| 特性 | 本地 CI | GitHub Actions |
|------|---------|----------------|
| 費用 | 免費 | 需付費 |
| 速度 | 快（本地） | 慢（雲端） |
| 隱私 | 高 | 中 |
| 整合 | 簡單 | 需配置 |
| 通知 | 自定義 | 內建 |

**結論**: 對於本地開發和測試，本地 CI 更適合。

## 最佳實踐

1. **每次提交前執行** `./check_ci.sh`
2. **每天執行一次完整驗證** `python3 local_ci.py`
3. **保留所有測試記錄** `ci_logs/`
4. **定期檢視測試覆蓋率**

## 擴充測試

### 新增測試用例

在 `tests/` 目錄下新增測試檔案：

```python
# tests/test_custom.py
def test_my_feature():
    """測試我的功能"""
    # 測試邏輯
    assert True
```

### 整合到現有流程

```bash
# 在現有腳本中加入
./check_ci.sh || exit 1
```

## 故障排除

### 問題：測試超時
**解法**: 減少測試天數或樣本數

### 問題：API 限制
**解法**: 使用 mock 資料或減少呼叫頻率

### 問題：服務未運行
**解法**: 重啟 Streamlit `pkill -9 -f streamlit && ...`

## 參考資源

- [TESTING.md](TESTING.md) - 測試策略詳情
- [CI.md](CI.md) - CI 流程詳情
- [tests/](tests/) - 測試用例範例
