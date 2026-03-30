#!/usr/bin/env python3
"""
Stock Analysis Dashboard with Market Overview
- 大盤趨勢分析
- 個股監控
- 技術指標
- 市場情緒
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from datetime import datetime, timedelta
import sys
sys.path.append('/home/openclaw/.openclaw/workspace-stock/hello-bob')

from market_dashboard import get_market_data, calculate_market_breadth, get_sector_performance, generate_market_summary
from data_collector import fetch_historical_data, store_data

# 頁面配置
st.set_page_config(
    page_title="台灣股票分析系統",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 樣式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
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
    ["📈 大盤趨勢", "🔍 個股分析", "📊 產業表現", "📝 分析報告"]
)

# 大盤數據緩存
@st.cache_data(ttl=300)
def load_market_data():
    """載入大盤數據"""
    return get_market_data(days=90)

@st.cache_data(ttl=60)
def load_breadth():
    """載入市場寬度"""
    return calculate_market_breadth()

@st.cache_data(ttl=300)
def load_sector_performance():
    """載入產業表現"""
    return get_sector_performance()

# ==================== 大盤趨勢視圖 ====================
if view_option == "📈 大盤趨勢":
    st.header("📈 大盤趨勢分析")
    
    # 載入數據
    with st.spinner("載入大盤數據中..."):
        market_data = load_market_data()
        breadth = load_breadth()
        sector_perf = load_sector_performance()
    
    # 主要指標列
    col1, col2, col3, col4 = st.columns(4)
    
    # 台灣 50 數據
    if '0050.TW' in market_data:
        data_0050 = market_data['0050.TW']
        latest_0050 = data_0050['latest']
        if latest_0050 is not None:
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
            f"{vol/1e9:.2f}億",
            "台灣 50"
        )
    
    st.markdown("---")
    
    # 大盤走勢圖
    st.subheader("📊 大盤走勢")
    
    if '0050.TW' in market_data:
        df = market_data['0050.TW']['data']
        
        # 建立 K 線圖
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=('台灣 50 走勢', '成交量')
        )
        
        # K 線
        fig.add_trace(
            go.Candlestick(
                x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='0050.TW'
            ),
            row=1, col=1
        )
        
        # 成交量
        colors = ['red' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'green' 
                 for i in range(len(df))]
        fig.add_trace(
            go.Bar(
                x=df['Date'],
                y=df['Volume'],
                name='成交量',
                marker_color=colors
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=600,
            xaxis_rangeslider_visible=False,
            showlegend=False,
            hovermode='x unified'
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
            marker_color=['red' if x > 0 else 'green' for x in sector_df['漲幅']]
        ))
        fig.update_layout(
            title='各產業漲跌表現',
            xaxis_title='產業',
            yaxis_title='漲幅 (%)',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

# ==================== 個股分析視圖 ====================
elif view_option == "🔍 個股分析":
    st.header("🔍 個股分析")
    
    # 輸入股票代號
    col1, col2 = st.columns([3, 1])
    with col1:
        stock_id = st.text_input("股票代號", "2330", help="例如：2330 (台積電), 2317 (鴻海)")
    with col2:
        days = st.number_input("天數", min_value=30, max_value=365, value=90)
    
    if st.button("🔍 查詢", type="primary"):
        # 載入數據
        df = fetch_historical_data(stock_id, days)
        
        if df is not None and not df.empty:
            # 顯示基本資料
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else df.iloc[0]
            change = (latest['close'] - prev['close']) / prev['close'] * 100
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("目前股價", f"{latest['close']:.2f}", f"{change:+.2f}%")
            col2.metric("最高價", f"{df['high'].max():.2f}")
            col3.metric("最低價", f"{df['low'].min():.2f}")
            col4.metric("成交量", f"{latest['volume']/1e6:.1f}萬張")
            
            # 走勢圖
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='股價'
            ))
            fig.update_layout(
                title=f'{stock_id} 股價走勢',
                xaxis_title='日期',
                yaxis_title='價格',
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df.sort_values('date', ascending=False), use_container_width=True)
        else:
            st.error("查無資料，請確認股票代號是否正確")

# ==================== 產業表現視圖 ====================
elif view_option == "📊 產業表現":
    st.header("📊 產業表現分析")
    
    sector_perf = load_sector_performance()
    
    if sector_perf:
        for sector, perf in sector_perf.items():
            st.subheader(f"🏭 {sector}")
            col1, col2 = st.columns(2)
            col1.metric("平均漲幅", f"{perf['avg_change']:+.2f}%")
            col2.metric("檔數", f"{perf['stock_count']}檔")
            
            # 產業內個股表現
            if perf['stocks']:
                stock_df = pd.DataFrame(perf['stocks'])
                stock_df = stock_df.sort_values('change_pct', ascending=False)
                st.dataframe(stock_df, use_container_width=True)

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
<div style='text-align: center; color: gray;'>
    <small>🤖 Stock Analysis System | Powered by yfinance & Streamlit</small>
</div>
""", unsafe_allow_html=True)
