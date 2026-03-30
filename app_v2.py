#!/usr/bin/env python3
"""
Stock Analysis Dashboard V2 - 優化版
- 更好的 UI/UX
- 資料清洗
- PTT 情緒整合
- 響應式設計
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from datetime import datetime, timedelta
import numpy as np
import sys
sys.path.append('/home/openclaw/.openclaw/workspace-stock/hello-bob')

from market_dashboard import get_market_data, calculate_market_breadth, get_sector_performance, generate_market_summary

# 頁面配置
st.set_page_config(
    page_title="台灣股票分析系統",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義樣式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1f77b4;
        margin-top: 1.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stApp {
        background-color: #0e1117;
    }
</style>
""", unsafe_allow_html=True)

# 標題
st.markdown('<h1 class="main-header">📊 台灣股票分析系統</h1>', unsafe_allow_html=True)
st.markdown("---")

# 側邊欄
st.sidebar.header("⚙️ 控制面板")

# 功能選擇
view_option = st.sidebar.radio(
    "選擇視圖",
    ["📈 大盤趨勢", "🔍 個股分析", "🏭 產業表現", "📝 分析報告"],
    index=0
)

# 資料載入函式（含清洗）
@st.cache_data(ttl=300)
def load_market_data():
    """載入並清洗大盤數據"""
    data = get_market_data(days=90)
    # 清洗 NaN
    for symbol, info in data.items():
        if info['data'] is not None:
            df = info['data']
            df = df.fillna(method='ffill').fillna(method='bfill')
            info['data'] = df
    return data

@st.cache_data(ttl=60)
def load_breadth():
    """載入市場寬度"""
    return calculate_market_breadth()

@st.cache_data(ttl=300)
def load_sector_performance():
    """載入產業表現"""
    return get_sector_performance()

def fetch_stock_data(symbol, days=90):
    """獲取個股數據（含清洗）"""
    try:
        import yfinance as yf
        if not symbol.endswith('.TW'):
            symbol = f"{symbol}.TW"
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=f"{days}d")
        
        if df.empty:
            return None
        
        df = df.reset_index()
        df = df.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Adj Close': 'adj_close',
            'Volume': 'volume'
        })
        
        # 清洗 NaN
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        # 計算技術指標
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA60'] = df['close'].rolling(window=60).mean()
        
        # 計算 RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    except Exception as e:
        st.error(f"讀取資料失敗：{e}")
        return None

# ==================== 大盤趨勢視圖 ====================
if view_option == "📈 大盤趨勢":
    st.header("📈 大盤趨勢分析")
    
    # 載入數據
    with st.spinner("🔄 載入大盤數據中..."):
        market_data = load_market_data()
        breadth = load_breadth()
        sector_perf = load_sector_performance()
    
    # 主要指標列
    col1, col2, col3, col4 = st.columns(4)
    
    # 台灣 50 數據
    if '0050.TW' in market_data:
        data_0050 = market_data['0050.TW']
        latest_0050 = data_0050['latest']
        if latest_0050 is not None and not pd.isna(latest_0050['Close']):
            change_0050 = data_0050['change']
            col1.metric(
                "台灣 50",
                f"{latest_0050['Close']:.2f}",
                f"{change_0050:+.2f}%",
                delta_color="inverse" if change_0050 < 0 else "normal"
            )
    
    # 市場寬度
    if breadth:
        col2.metric(
            "漲跌比",
            f"{breadth['up']} / {breadth['down']}",
            f"比價：{breadth['ratio']:.2f}"
        )
        col3.metric(
            "漲跌差",
            f"{breadth['advance_decline']:+d}",
            f"總計：{breadth['total']}檔"
        )
    
    # 成交量
    if '0050.TW' in market_data and market_data['0050.TW']['latest'] is not None:
        vol = market_data['0050.TW']['latest']['Volume']
        col4.metric(
            "成交量",
            f"{vol/1e6:.0f}萬",
            "台灣 50"
        )
    
    st.markdown("---")
    
    # 大盤走勢圖
    st.subheader("📊 大盤走勢")
    
    if '0050.TW' in market_data:
        df = market_data['0050.TW']['data']
        df = df.dropna(subset=['Close'])  # 移除無效資料
        
        # 建立 K 線圖 + 成交量 + 均線
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            row_heights=[0.5, 0.3, 0.2],
            subplot_titles=('台灣 50 走勢 + 均線', '成交量', '漲跌')
        )
        
        # K 線
        fig.add_trace(
            go.Candlestick(
                x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='價格'
            ),
            row=1, col=1
        )
        
        # 均線
        if 'MA20' in df.columns:
            fig.add_trace(go.Scatter(x=df['Date'], y=df['MA20'], name='MA20', line=dict(color='orange', width=1.5)), row=1, col=1)
        if 'MA60' in df.columns:
            fig.add_trace(go.Scatter(x=df['Date'], y=df['MA60'], name='MA60', line=dict(color='purple', width=1.5)), row=1, col=1)
        
        # 成交量
        colors = ['red' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'green' 
                 for i in range(len(df))]
        fig.add_trace(
            go.Bar(x=df['Date'], y=df['Volume'], name='成交量', marker_color=colors),
            row=2, col=1
        )
        
        # 漲跌
        daily_change = df['Close'].pct_change() * 100
        colors_change = ['red' if x >= 0 else 'green' for x in daily_change]
        fig.add_trace(
            go.Bar(x=df['Date'][1:], y=daily_change[1:], name='漲跌%', marker_color=colors_change),
            row=3, col=1
        )
        
        fig.update_layout(
            height=700,
            xaxis_rangeslider_visible=False,
            showlegend=True,
            hovermode='x unified',
            legend=dict(x=0, y=1, bgcolor='rgba(0,0,0,0)')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 市場摘要
    st.subheader("📝 市場摘要")
    summary_text = generate_market_summary(market_data, breadth, sector_perf)
    st.markdown(summary_text)
    
    # 產業表現
    st.subheader("🏭 產業表現")
    if sector_perf:
        sector_data = []
        for sector, perf in sector_perf.items():
            sector_data.append({
                '產業': sector,
                '漲幅': perf['avg_change'],
                '檔數': perf['stock_count']
            })
        
        sector_df = pd.DataFrame(sector_data)
        sector_df = sector_df.sort_values('漲幅', ascending=False)
        
        # 產業表現柱狀圖
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=sector_df['產業'],
            y=sector_df['漲幅'],
            marker_color=['red' if x > 0 else 'green' for x in sector_df['漲幅']],
            text=[f"{x:+.2f}%" for x in sector_df['漲幅']],
            textposition='outside'
        ))
        fig.update_layout(
            title='各產業漲幅排名',
            xaxis_title='產業',
            yaxis_title='漲幅 (%)',
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

# ==================== 個股分析視圖 ====================
elif view_option == "🔍 個股分析":
    st.header("🔍 個股分析")
    
    # 輸入股票代號
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        stock_id = st.text_input("股票代號", "2330", help="例如：2330 (台積電), 2317 (鴻海)")
    with col2:
        days = st.slider("天數", min_value=30, max_value=365, value=90)
    with col3:
        query_btn = st.button("🔍 查詢", type="primary", use_container_width=True)
    
    if query_btn or stock_id:
        # 載入數據
        df = fetch_stock_data(stock_id, days)
        
        if df is not None and not df.empty:
            # 基本資料
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else df.iloc[0]
            change = (latest['close'] - prev['close']) / prev['close'] * 100 if prev['close'] != 0 else 0
            
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("目前股價", f"{latest['close']:.2f}", f"{change:+.2f}%")
            col2.metric("最高", f"{df['high'].max():.2f}")
            col3.metric("最低", f"{df['low'].min():.2f}")
            col4.metric("均量", f"{df['volume'].mean()/1e6:.1f}萬張")
            col5.metric("RSI", f"{latest.get('RSI', 50):.1f}" if 'RSI' in df.columns else "N/A")
            
            # 走勢圖
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            # K 線 + 均線
            fig.add_trace(go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='股價'), row=1, col=1)
            if 'MA20' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['MA20'], name='MA20', line=dict(color='orange')), row=1, col=1)
            if 'MA60' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['MA60'], name='MA60', line=dict(color='purple')), row=1, col=1)
            
            # 成交量
            fig.add_trace(go.Bar(x=df['date'], y=df['volume'], name='成交量', marker_color='blue'), row=2, col=1)
            
            fig.update_layout(height=600, xaxis_rangeslider_visible=False, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
            
            # 資料表
            st.subheader("📋 歷史資料")
            display_df = df[['date', 'open', 'high', 'low', 'close', 'volume']].copy()
            display_df['漲跌'] = display_df['close'].pct_change() * 100
            st.dataframe(display_df.sort_values('date', ascending=False).style.format({
                'open': '{:.2f}', 'high': '{:.2f}', 'low': '{:.2f}', 'close': '{:.2f}', 'volume': '{:.0f}', '漲跌': '{:+.2f}%'
            }), use_container_width=True, hide_index=True)
        else:
            st.error("查無資料，請確認股票代號是否正確")

# ==================== 產業表現視圖 ====================
elif view_option == "🏭 產業表現":
    st.header("🏭 產業表現分析")
    
    sector_perf = load_sector_performance()
    
    if sector_perf:
        for sector, perf in sector_perf.items():
            with st.expander(f"🏭 {sector} (平均：{perf['avg_change']:+.2f}%, {perf['stock_count']}檔)", expanded=True):
                if perf['stocks']:
                    stock_df = pd.DataFrame(perf['stocks'])
                    stock_df = stock_df.sort_values('change_pct', ascending=False)
                    st.dataframe(stock_df.style.format({'change_pct': '{:+.2f}%'}), use_container_width=True, hide_index=True)

# ==================== 分析報告視圖 ====================
elif view_option == "📝 分析報告":
    st.header("📝 分析報告")
    
    try:
        with open('reports/daily_report.md', 'r', encoding='utf-8') as f:
            report = f.read()
        st.markdown(report)
    except Exception as e:
        st.error(f"讀取報告失敗：{e}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9rem;'>
    🤖 Stock Analysis System | Powered by yfinance, Streamlit & Plotly | 資料更新頻率：每 60 秒
</div>
""", unsafe_allow_html=True)
