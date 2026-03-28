# 模組化技術指標分析系統

## 📦 架構概覽

```
hello-bob/
├── indicators/              # 指標計算模組
│   ├── __init__.py
│   └── indicator_base.py    # 20+ 技術指標實作
├── analysis/                # 分析引擎
│   ├── __init__.py
│   └── indicator_analysis.py
├── tests/                   # 測試套件
│   └── test_indicators.py
├── reports/                 # 分析報告
│   ├── indicator_analysis_full.md
│   ├── 7day_market_report.md
│   └── technical_analysis.md
├── config.py                # 股票清單設定
└── MODULE_GUIDE.md          # 本文件
```

## 🎯 20+ 技術指標清單

### 趨勢指標 (Trend Indicators)
1. **SMA(5, 10, 20, 60, 120)** - 簡單移动平均
2. **EMA(12, 26)** - 指數移动平均
3. **MACD(12, 26, 9)** - 移動平均收斂發散
4. **ADX(14)** - 平均趨向指數
5. **Aroon(25)** - 趨勢方向指標

### 動能指標 (Momentum Indicators)
6. **RSI(14)** - 相對強弱指標
7. **Stochastic(14, 3)** - 隨機指標
8. **CCI(20)** - 商品通道指標
9. **Williams %R(14)** - 威廉指標
10. **MFI(14)** - 資金流量指標

### 波動率指標 (Volatility Indicators)
11. **Bollinger Bands(20, 2)** - 布林通道
12. **ATR(14)** - 平均真實波動幅度
13. **Keltner Channel(20)** - 肯特納通道

### 成交量指標 (Volume Indicators)
14. **OBV** - 能量潮
15. **VWAP** - 成交量加權平均價
16. **Volume SMA** - 成交量均線

### 派生指標 (Derived Indicators)
17. **BB %B** - 布林帶位置
18. **BB Width** - 布林帶寬度
19. **Price to SMA20** - 股價相對於均線位置
20. **EMA 12-26 Diff** - 快慢均線差值

## 💻 使用方式

### 基本使用

```python
from indicators import calculate_all_indicators
import yfinance as yf

# 載入資料
ticker = yf.Ticker('2330.TW')
df = ticker.history(period='3mo')

# 計算所有指標
df = calculate_all_indicators(df)

# 查看指標
print(df.columns.tolist())
```

### 進階分析

```python
from analysis import IndicatorAnalyzer

# 建立分析器
analyzer = IndicatorAnalyzer()

# 載入並分析
df = analyzer.load_data('2330', period='3mo')
analysis = analyzer.analyze(df)

# 查看結果
print(analysis['signal']['signal'])  # 交易訊號
print(analysis['trend']['trend'])    # 趨勢
print(analysis['momentum']['rsi_value'])  # RSI
```

### 批量分析

```python
from analysis import IndicatorAnalyzer

analyzer = IndicatorAnalyzer()
stocks = ['2330', '2317', '2454', '2800']

# 一次分析多檔股票
results = analyzer.analyze_multiple(stocks)

for symbol, analysis in results.items():
    print(f"{symbol}: {analysis['signal']['signal']}")
```

### 生成報告

```python
from analysis import IndicatorAnalyzer

analyzer = IndicatorAnalyzer()
df = analyzer.load_data('2330', period='3mo')
analysis = analyzer.analyze(df)

# 生成人类可讀報告
report = analyzer.generate_report(analysis, '2330')
print(report)

# 儲存報告
with open('reports/2330_analysis.md', 'w') as f:
    f.write(report)
```

## 🧪 測試

### 執行所有測試

```bash
cd /home/openclaw/.openclaw/workspace-stock/hello-bob
python3 tests/test_indicators.py
```

### 測試項目

1. ✅ SMA 計算正確性
2. ✅ EMA 計算正確性
3. ✅ RSI 範圍與邏輯
4. ✅ MACD 組成完整
5. ✅ Bollinger Bands 區間
6. ✅ ATR 波動率反應
7. ✅ 無向後偏見 (No Lookahead Bias)
8. ✅ NaN 處理
9. ✅ 效能測試 (5000 筆 <5 秒)
10. ✅ 所有指標完整性

## 📊 分析報告內容

### 趨勢分析
- SMA 排列方向
- MACD 買賣訊號
- ADX 趨勢強度
- Aroon 趨勢方向

### 動能分析
- RSI 超買/超賣
- Stochastic 交叉
- CCI 極端值
- Williams %R 位置
- MFI 資金流向

### 波動率分析
- 布林帶位置
- 布林帶擠壓/擴張
- ATR 波動幅度
- Keltner 通道位置

### 成交量分析
- OBV 趨勢
- 成交量增減
- 成交量異常
- VWAP 位置

### 綜合評分
- 趨勢分數 (0-1)
- 動能分數 (0-1)
- 波動率分數 (0-1)
- 成交量分數 (0-1)
- 總體評分
- 交易訊號 (STRONG BUY/BUY/HOLD/SELL)
- 信心水準 (HIGH/MEDIUM)

## 🎯 訊號解釋

### STRONG BUY (強烈買進)
- 綜合評分 > 0.7
- 多項指標看多
- 信心水準 HIGH

### BUY (買進)
- 綜合評分 0.5-0.7
- 多頭略佔優勢
- 信心水準 MEDIUM

### HOLD (觀望)
- 綜合評分 0.3-0.5
- 多空交錯
- 建議觀望

### SELL (賣出)
- 綜合評分 < 0.3
- 空頭主導
- 信心水準依評分而定

## 📁 檔案說明

| 檔案 | 說明 |
|------|------|
| `indicators/indicator_base.py` | 20+ 指標實作 |
| `analysis/indicator_analysis.py` | 分析引擎 |
| `tests/test_indicators.py` | 測試套件 |
| `config.py` | 股票清單設定 |
| `reports/` | 分析報告目錄 |

## 🚀 快速開始

```python
# 1. 安裝依賴
pip install pandas numpy yfinance

# 2. 匯入模組
from analysis import IndicatorAnalyzer

# 3. 分析股票
analyzer = IndicatorAnalyzer()
result = analyzer.analyze_stock('2330')

# 4. 輸出結果
print(analyzer.generate_report(result, '2330'))
```

## 📝 注意事項

1. **資料品質**: 確保有足夠的歷史資料（至少 30 筆）
2. **NaN 處理**: 初期指標值可能為 NaN（正常現象）
3. **無向後偏見**: 所有指標只使用過去資料
4. **向量化運算**: 高效能，無迴圈
5. **投資風險**: 僅供參考，不構成投資建議

## 🔧 擴充

### 新增指標

```python
def my_custom_indicator(df):
    """自訂指標"""
    # 實作邏輯
    return result

# 加入 calculate_all_indicators()
```

### 自訂分析邏輯

```python
from analysis.indicator_analysis import IndicatorAnalyzer

class MyAnalyzer(IndicatorAnalyzer):
    def analyze_momentum(self, df):
        # 覆蓋或擴充既有邏輯
        result = super().analyze_momentum(df)
        # 加入自訂邏輯
        return result
```

## 📞 支援

- 問題反應：查看 `reports/` 目錄下的範例報告
- 測試驗證：執行 `python3 tests/test_indicators.py`
- 完整報告：查看 `reports/indicator_analysis_full.md`

---

*Last updated: 2026-03-28*
*Version: 1.0.0*
