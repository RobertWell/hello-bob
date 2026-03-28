# 綜合技術分析指南

## 📊 系統特色

這個綜合分析系統解決了傳統技術分析「各說各話」的問題，透過：

1. **多時間框架分析** - 短中長期 MA 綜合判斷
2. **動態加權評分** - 依市場狀態調整權重
3. **情境分析** - 提供多種可能情境與對應策略
4. **綜合建議** - 明確的進出場建議

## 🎯 核心概念

### 1. 多時間框架移動平均分析

傳統 MA 分析只看單一时间點，我們分析三個時間框架：

| 時間框架 | 均線 | 用途 |
|---------|------|------|
| **短期** | 5 日、10 日 | 捕捉即時動能 |
| **中期** | 20 日、60 日 | 判斷主要趨勢 |
| **長期** | 120 日 | 確認長期方向 |

**綜合判斷**：
- 短中長期都多頭 → 強烈多頭訊號
- 短中長期不一致 → 觀望
- 短中長期都空頭 → 強烈空頭訊號

### 2. 市場狀態偵測

系統自動偵測目前市場狀態：

| 市場狀態 | 特徵 | 策略 |
|---------|------|------|
| **多頭強勢** | MA 多頭排列 + ADX > 25 | 積極操作，趨勢跟隨 |
| **多頭弱勢** | MA 多頭但 ADX < 25 | 保守操作，區間交易 |
| **空頭強勢** | MA 空頭排列 + ADX > 25 | 停損停利，降低部位 |
| **空頭弱勢** | MA 空頭但 ADX < 25 | 觀望，等待反轉 |
| **盤整** | MA 糾結 | 區間操作，突破加碼 |

### 3. 動態加權評分

根據市場狀態調整各指標權重：

**多頭強勢市場**：
- 趨勢指標：40%
- 動能指標：30%
- 成交量：20%
- 波動度：10%

**盤整市場**：
- 趨勢指標：20%
- 動能指標：30%
- 成交量：20%
- 波動度：30%

### 4. 綜合評分系統

```
綜合評分 = 趨勢分數 × 權重 + 動能分數 × 權重 + 成交量分數 × 權重 + 波動度分數 × 權重
```

**評分對應訊號**：
- > 0.70: STRONG BUY（強烈買進）
- 0.55-0.70: BUY（買進）
- 0.45-0.55: HOLD（觀望）
- 0.30-0.45: SELL（賣出）
- < 0.30: STRONG SELL（強烈賣出）

## 💻 使用方式

### 基本使用

```python
from analysis.composite_analysis import analyze_composite

# 分析單一股票
result = analyze_composite('2330')

# 查看結果
print(result['signal'])           # 訊號
print(result['composite_score'])  # 綜合評分
print(result['confidence'])       # 信心水準
```

### 進階使用

```python
from analysis.composite_analysis import CompositeAnalyzer
from indicators.indicator_base import calculate_all_indicators
import yfinance as yf

# 載入資料
ticker = yf.Ticker('2330.TW')
df = ticker.history(period='3mo')
df = calculate_all_indicators(df)

# 建立分析器
analyzer = CompositeAnalyzer()

# 完整分析
result = analyzer.full_analysis(df, '2330')

# 查看時間框架分析
tf = result['timeframe_analysis']
print(f"短期：{tf['short_term']['signal']}")
print(f"中期：{tf['medium_term']['signal']}")
print(f"長期：{tf['long_term']['signal']}")

# 查看均線排列
ma = tf['ma_alignment']
print(f"MA 排列：{ma['alignment']}")
if ma['golden_cross']:
    print("黃金交叉！")
elif ma['death_cross']:
    print("死亡交叉！")

# 查看情境分析
for scenario in result['scenarios']:
    print(f"{scenario['name']}: {scenario['action']}")
```

### 批量分析

```python
from analysis.composite_analysis import analyze_composite

stocks = ['2330', '2317', '2454', '2800', '1301']

results = []
for symbol in stocks:
    result = analyze_composite(symbol)
    results.append(result)

# 排序
sorted_results = sorted(results, key=lambda x: x['composite_score'], reverse=True)

for r in sorted_results:
    print(f"{r['symbol']}: {r['signal']} (評分：{r['composite_score']:.2f})")
```

## 📊 報告解讀

### 綜合評分報告

```
代號   訊號         評分   市場狀態     短期   中期   長期
2330   BUY          0.68   bull_weak    BULL   BULL   BEAR
```

**解讀**：
- 綜合評分 0.68，介於 0.55-0.70 之間 → BUY 訊號
- 市場狀態：多頭弱勢（bull_weak）
- 短期多頭、中期多頭、長期空頭 → 短多長空，需留意

### 時間框架分析

```
短期 (5-10 日):  BULLISH (Score: 0.75)
中期 (20-60 日): BULLISH (Score: 0.65)
長期 (120 日):   BEARISH (Score: 0.35)
```

**解讀**：
- 短期動能強
- 中期趨勢向上
- 長期仍處空頭
- 綜合判斷：短多格局，但長期未翻多

### 情境分析

```
Bull Case (30%):
  目標價：185.00
  停損價：165.00
  操作：突破 178 加碼

Bear Case (30%):
  目標價：165.00
  停損價：185.00
  操作：跌破 172 減碼

Sideways Case (40%):
  目標價：178.00
  停損價：172.00
  操作：區間操作
```

## 🎯 實戰應用

### 情境 1：選股

```python
from analysis.composite_analysis import analyze_composite

# 分析所有成分股
stocks = ['2330', '2317', '2454', '2800', '1301', '1101', '0050']
results = [analyze_composite(s) for s in stocks]

# 找出最佳買點
best_buy = max(results, key=lambda x: x['composite_score'])
print(f"最佳買點：{best_buy['symbol']} ({best_buy['signal']})")

# 找出最弱股票
worst = min(results, key=lambda x: x['composite_score'])
print(f"最弱股票：{worst['symbol']} ({worst['signal']})")
```

### 情境 2：進場時機判斷

```python
result = analyze_composite('2330')

# 檢查是否為黃金交叉
if result['timeframe_analysis']['ma_alignment']['golden_cross']:
    print("黃金交叉！考虑進場")

# 檢查短中長期是否一致
tf = result['timeframe_analysis']
if (tf['short_term']['signal'] == 'BULLISH' and
    tf['medium_term']['signal'] == 'BULLISH' and
    tf['long_term']['signal'] == 'BULLISH'):
    print("三多格局！強烈買進訊號")

# 檢查是否有 MACD 交叉
if result['momentum_analysis']['macd']['crossover']:
    print("MACD 多頭交叉！動能轉強")
```

### 情境 3：風險控管

```python
result = analyze_composite('2330')

# 如果綜合評分低但持有部位
if result['composite_score'] < 0.3:
    print("綜合評分過低，考慮減碼或停損")

# 如果短中長期不一致
tf = result['timeframe_analysis']
if tf['short_term']['signal'] != tf['medium_term']['signal']:
    print("短中期訊號不一致，建議觀望")

# 如果市場進入盤整
if result['market_regime'].value == 'sideways':
    print("盤整格局，區間操作或等待突破")
```

## 📈 範例輸出

執行以下指令查看完整分析：

```bash
cd /home/openclaw/.openclaw/workspace-stock/hello-bob
python3 examples/composite_demo.py 2330
```

完整輸出包含：
1. 綜合評分與訊號
2. 短中長期分析
3. MA 排列與交叉
4. 動能指標（RSI、MACD、Stochastic）
5. 組成評分與權重
6. 情境分析
7. 綜合建議

## 🔧 進階設定

### 調整時間框架

```python
from analysis.composite_analysis import CompositeAnalyzer

analyzer = CompositeAnalyzer()

# 自訂 MA 組合
analyzer.SHORT_MAS = ['sma_3', 'sma_5', 'sma_10']
analyzer.MEDIUM_MAS = ['sma_20', 'sma_60']
analyzer.LONG_MAS = ['sma_120', 'sma_240']
```

### 調整權重

```python
# 自訂市場狀態權重
analyzer.REGIME_WEIGHTS[MarketRegime.BULL_STRONG] = {
    'trend': 0.5,      # 增加趨勢權重
    'momentum': 0.2,   # 降低動能權重
    'volume': 0.2,
    'volatility': 0.1
}
```

## 📝 注意事項

1. **資料品質**：確保有足夠歷史資料（至少 30 筆）
2. **市場狀態**：不同市場狀態下指標可信度不同
3. **綜合判斷**：不要只看單一指標
4. **風險控管**：訊號僅供參考，需搭配停損停利
5. **即時更新**：市場瞬息萬變，建議每日更新分析

## 🚀 下一步

1. 執行範例：`python3 examples/composite_demo.py`
2. 查看報告：`reports/composite_analysis_full.md`
3. 整合到你的策略中
4. 回測驗證績效

---

*Last updated: 2026-03-28*
*Version: 1.0.0*
