# 台灣股票分析系統 - 完整每日行程

## 📊 系統概覽

### 股票範圍擴大
- **總計**: 200+ 檔台灣主要股票
- **科技股**: 50 檔（台積電、鴻海、聯發科等）
- **金融股**: 16 檔（國泰金、富邦金、兆豐金等）
- **傳產股**: 20 檔（台塑、南亞、台化等）
- **零售/服務**: 10 檔（統一超、遠百等）
- **ETF**: 5 檔（0050、006208、00888 等）

## ⏰ 每日自動化行程

### 1. 早晨例行工作 (6:00 AM)
```bash
python3 daily_schedule.py --morning
```
**工作內容**:
- 收集過夜資料
- 更新 PTT 情緒分析
- 生成晨報
- 發送盤前警訊

### 2. 開盤檢查 (9:00 AM - 交易日)
```bash
python3 daily_schedule.py --market-open
```
**工作內容**:
- 盤前最後檢查
- 分析主要股票趨勢
- 發送即時警訊
- 標的：2330, 2317, 2454, 2881, 1301

### 3. 中午更新 (12:00 PM - 交易日)
```bash
python3 daily_schedule.py --midday
```
**工作內容**:
- 快速市場檢查
- 更新 PTT 情緒
- 中午報告

### 4. 收盤分析 (6:00 PM - 交易日)
```bash
python3 daily_schedule.py --market-close
```
**工作內容**:
- 收集最終收盤資料
- 更新所有技術指標
- 生成收盤報告 (EOD Report)
- 儲存至 reports/eod_report_YYYYMMDD.md

### 5. 晚間分析 (10:00 PM)
```bash
python3 daily_schedule.py --evening
```
**工作內容**:
- 關聯性分析
- 趨勢深度分析
- 準備次日資料

## 📅 Cron 排程設定

### 安裝自動化
```bash
cd /home/openclaw/.openclaw/workspace-stock/hello-bob
./setup_cron.sh
```

### 完整排程表
```cron
# 6:00 AM - 早晨例行工作
0 6 * * * python3 daily_schedule.py --morning

# 9:00 AM - 開盤檢查 (交易日)
0 9 * * 1-5 python3 daily_schedule.py --market-open

# 12:00 PM - 中午更新 (交易日)
0 12 * * 1-5 python3 daily_schedule.py --midday

# 6:00 PM - 收盤分析 (交易日)
0 18 * * 1-5 python3 daily_schedule.py --market-close

# 10:00 PM - 晚間分析
0 22 * * * python3 daily_schedule.py --evening

# 每小時 - 快速資料更新
0 * * * * python3 data_collector.py --all-stocks --days 1

# 週日 10:00 AM - 完整歷史資料更新
0 10 * * 0 python3 data_collector.py --all-stocks --days 365

# 23:00 - 系統健康檢查
0 23 * * * python3 check_status.py
```

## 📊 報告產出

### 報告類型
1. **晨報** (Morning Report) - 每日 6:00 AM
2. **收盤報告** (EOD Report) - 每日 6:00 PM
3. **週報** (Weekly Report) - 每週一
4. **關聯性報告** - 每週日

### 報告內容
- 市場概覽
- 漲跌幅前五名
- PTT 情緒分析
- 技術指標摘要
- 交易警訊
- 關聯性分析

## 🔧 手動執行

### 單一功能
```bash
# 收集資料
python3 data_collector.py --all-stocks --days 1

# 生成報告
python3 daily_report.py --output reports/manual_report.md

# 趨勢分析
python3 trend_tracker.py --all

# 關聯性分析
python3 correlation_analysis.py

# 系統檢查
python3 check_status.py
```

### 完整流程
```bash
# 執行完整每日行程
python3 daily_schedule.py --run-all
```

## 📁 檔案結構
```
hello-bob/
├── config.py                    # 股票清單與設定
├── data_collector.py           # 資料收集
├── indicators.py               # 技術指標
├── ptt_bus.py                  # PTT 爬蟲
├── correlation_analysis.py     # 關聯性分析
├── trend_tracker.py            # 趨勢追蹤
├── daily_report.py             # 報告生成
├── daily_schedule.py           # 每日行程
├── check_status.py             # 系統檢查
├── setup_cron.sh              # Cron 設置
├── logs/                       # 日誌檔
└── reports/                    # 報告檔
```

## 📈 監控與維護

### 查看日誌
```bash
# 查看最新日誌
tail -f logs/cron.log

# 查看系統狀態
python3 check_status.py
```

### 修改排程
```bash
# 編輯 crontab
crontab -e

# 查看現有排程
crontab -l
```

## 🎯 下一步

### 短期
- [x] 擴充股票範圍到 200+ 檔
- [x] 建立完整每日行程
- [x] 設置自動化 cron
- [ ] 加入 LINE/Telegram 通知
- [ ] 建立 Web Dashboard

### 中期
- [ ] 擴充到 1700+ 檔完整股票
- [ ] 加入美國股票
- [ ] 改進情緒分析 (BERT)
- [ ] 機器學習預測

### 長期
- [ ] 自動交易系統
- [ ] 投資組合優化
- [ ] 回測引擎

---
*Last updated: 2026-03-28*
*Author: Robert Lin (@Stock_bob_bot)*
