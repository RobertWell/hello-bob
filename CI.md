# Stock Analysis CI/CD 文件

## 📋 測試流程

### 1. 本地測試
```bash
# 執行所有測試
python3 tests/test_all.py

# 或執行 CI 流水線
./ci.sh
```

### 2. CI 流水線步驟

#### 步驟 1: 環境檢查
- ✓ Python 3.10+
- ✓ 必要套件（pandas, numpy, yfinance, plotly, streamlit）

#### 步驟 2: 語法檢查
- ✓ `app_v5.py` 語法
- ✓ `commodities_analyzer.py` 語法
- ✓ `market_dashboard.py` 語法
- ✓ `ptt_sentiment.py` 語法

#### 步驟 3: 單元測試
- ✓ 原物料資料載入測試
- ✓ 全球期貨資料載入測試
- ✓ 大盤資料測試
- ✓ 漲跌比測試
- ✓ PTT 情緒測試
- ✓ 格式化測試（避免 TypeError）

#### 步驟 4: 服務健康檢查
- ✓ Streamlit 健康檢查
- ✓ Worker 進程檢查

#### 步驟 5: 資料完整性
- ✓ 檢查所有 `latest` 為數值類型
- ✓ 檢查無 NaN 值
- ✓ 檢查必要欄位存在

### 3. 測試用例清單

#### 資料載入測試
- [x] 原物料資料載入（黃金、白銀、原油）
- [x] 全球期貨資料載入（S&P、Nasdaq、Dow）
- [x] 台股資料載入（0050.TW）
- [x] PTT 文章抓取

#### 資料品質測試
- [x] 檢查 `latest` 為 `int` 或 `float`
- [x] 檢查 `change` 為 `int` 或 `float`
- [x] 檢查無 NaN 值
- [x] 檢查必要欄位存在（'data', 'latest', 'change'）

#### 格式化測試
- [x] `f"{value:.2f}"` 格式化測試
- [x] `f"{value:+.2f}%"` 格式化測試

#### 整合測試
- [x] Streamlit 服務健康檢查
- [x] HTTP 端口檢查

### 4. 防止的問題

#### 已修復問題
1. **TypeError: unsupported format string** 
   - 原因：`latest` 是 pandas Series 而非數值
   - 解法：改用 `float(latest_row['close'])`

2. **NaN 值導致顯示錯誤**
   - 原因：資料未清洗
   - 解法：完整 ffill/bfill/dropna

3. **資料類型不一致**
   - 原因：有時回傳 Series，有時回傳 float
   - 解法：統一轉為 float

### 5. 開發流程

```bash
# 1. 修改程式碼
# 2. 執行測試
python3 tests/test_all.py

# 3. 如果通過，提交
git add -A
git commit -m "feat: 新增功能"
git push

# 4. CI 自動執行
# - GitHub Actions 會自動執行測試
# - 通過後才會合併
```

### 6. 監控

- 服務健康檢查：`curl http://localhost:8501/_stcore/health`
- 日誌：`streamlit_v5.log`
- 進程：`ps aux | grep streamlit`
