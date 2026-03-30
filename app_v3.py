#!/usr/bin/env python3
"""
Stock Analysis Dashboard V3 - 完整優化版
✅ UI/UX 全面升級
✅ 資料清洗與驗證  
✅ PTT 情緒分析
✅ 即時更新狀態
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
from ptt_sentiment import fetch_ptt_stock_posts, get_market_sentiment, generate_sentiment_report

# 頁面配置
st.set_page_config(page_title="台灣股票分析系統", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# 樣式
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 1rem; }
    .status-bar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 0.5rem; border-radius: 8px; color: white; text-align: center; margin-bottom: 1rem; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# 標題
st.markdown('<h1 class="main-header">📊 台灣股票分析系統</h1>', unsafe_allow_html=True)
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f'<div class="status-bar">🟢 系統運行中 | 最後更新：{now}</div>', unsafe_allow_html=True)
st.markdown("---")

# 側邊欄
st.sidebar.header("⚙️ 控制面板")
view_option = st.sidebar.radio("選擇視圖", ["📈 大盤趨勢", "🔍 個股分析", "🏭 產業表現", "💬 PTT 情緒", "📝 分析報告"], index=0)

# 資料載入
@st.cache_data(ttl=300)
def load_market_data():
    data = get_market_data(days=90)
    for symbol, info in data.items():
        if info['data'] is not None:
            df = info['data'].ffill().bfill().dropna(subset=['Close'])
            info['data'] = df
    return data

@st.cache_data(ttl=60)
def load_breadth():
    return calculate_market_breadth()

@st.cache_data(ttl=300)
def load_sector_performance():
    return get_sector_performance()

@st.cache_data(ttl=120)
def load_ptt_sentiment():
    posts = fetch_ptt_stock_posts()
    return get_market_sentiment(posts), posts

def fetch_stock_data(symbol, days=90):
    try:
        import yfinance as yf
        if not symbol.endswith('.TW'):
            symbol = f"{symbol}.TW"
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=f"{days}d")
        if df.empty:
            return None
        df = df.reset_index().rename(columns={'Date': 'date', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
        df = df.ffill().bfill().dropna(subset=['close'])
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA60'] = df['close'].rolling(window=60).mean()
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss.replace(0, np.nan)))
        return df
    except Exception as e:
        st.error(f"讀取失敗：{e}")
        return None

# 大盤趨勢
if view_option == "📈 大盤趨勢":
    st.header("📈 大盤趨勢分析")
    with st.spinner("🔄 載入中..."):
        market_data = load_market_data()
        breadth = load_breadth()
        sector_perf = load_sector_performance()
    
    col1, col2, col3, col4 = st.columns(4)
    if '0050.TW' in market_data:
        d = market_data['0050.TW']
        if d['latest'] is not None:
            col1.metric("台灣 50", f"{d['latest']['Close']:.2f}", f"{d['change']:+.2f}%")
    if breadth:
        col2.metric("漲跌比", f"{breadth['up']}/{breadth['down']}", f"比價:{breadth['ratio']:.2f}")
        col3.metric("漲跌差", f"{breadth['advance_decline']:+d}")
    
    st.markdown("---")
    
    if '0050.TW' in market_data:
        df = market_data['0050.TW']['data']
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.5, 0.3, 0.2], subplot_titles=('台灣 50', '成交量', '漲跌%'))
        fig.add_trace(go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='價格'), row=1, col=1)
        colors = ['red' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'green' for i in range(len(df))]
        fig.add_trace(go.Bar(x=df['Date'], y=df['Volume'], name='成交量', marker_color=colors), row=2, col=1)
        change = df['Close'].pct_change() * 100
        colors_c = ['red' if x >= 0 else 'green' for x in change]
        fig.add_trace(go.Bar(x=df.index, y=change, name='漲跌%', marker_color=colors_c), row=3, col=1)
        fig.update_layout(height=700, xaxis_rangeslider_visible=False, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("📝 市場摘要")
    st.markdown(generate_market_summary(market_data, breadth, sector_perf))
    
    if sector_perf:
        st.subheader("🏭 產業表現")
        data = [{'產業': s, '漲幅': p['avg_change'], '檔數': p['stock_count']} for s, p in sector_perf.items()]
        sdf = pd.DataFrame(data).sort_values('漲幅', ascending=False)
        fig = go.Figure(go.Bar(x=sdf['產業'], y=sdf['漲幅'], marker_color=['red' if x > 0 else 'green' for x in sdf['漲幅']]))
        fig.update_layout(title='產業漲幅', height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# 個股分析
elif view_option == "🔍 個股分析":
    st.header("🔍 個股分析")
    col1, col2 = st.columns([3, 1])
    with col1:
        stock_id = st.text_input("股票代號", "2330")
    with col2:
        days = st.slider("天數", 30, 365, 90)
    
    if st.button("🔍 查詢", type="primary"):
        df = fetch_stock_data(stock_id, days)
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else df.iloc[0]
            change = (latest['close'] - prev['close']) / prev['close'] * 100 if prev['close'] != 0 else 0
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("股價", f"{latest['close']:.2f}", f"{change:+.2f}%")
            col2.metric("最高", f"{df['high'].max():.2f}")
            col3.metric("最低", f"{df['low'].min():.2f}")
            col4.metric("均量", f"{df['volume'].mean()/1e6:.1f}萬")
            col5.metric("RSI", f"{latest.get('RSI', 50):.1f}" if 'RSI' in df.columns else "N/A")
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='股價'), row=1, col=1)
            if 'MA20' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['MA20'], name='MA20', line=dict(color='orange')), row=1, col=1)
            fig.add_trace(go.Bar(x=df['date'], y=df['volume'], name='成交量', marker_color='blue'), row=2, col=1)
            fig.update_layout(height=600, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📋 歷史資料")
            display_df = df[['date', 'open', 'high', 'low', 'close', 'volume']].copy()
            display_df['漲跌'] = display_df['close'].pct_change() * 100
            st.dataframe(display_df.sort_values('date', ascending=False).style.format({'open': '{:.2f}', 'high': '{:.2f}', 'low': '{:.2f}', 'close': '{:.2f}', 'volume': '{:.0f}', '漲跌': '{:+.2f}%'}), use_container_width=True, hide_index=True)
        else:
            st.error("查無資料")

# 產業表現
elif view_option == "🏭 產業表現":
    st.header("🏭 產業表現")
    sector_perf = load_sector_performance()
    if sector_perf:
        for sector, perf in sector_perf.items():
            with st.expander(f"🏭 {sector} ({perf['avg_change']:+.2f}%, {perf['stock_count']}檔)", expanded=True):
                if perf['stocks']:
                    sdf = pd.DataFrame(perf['stocks']).sort_values('change_pct', ascending=False)
                    st.dataframe(sdf.style.format({'change_pct': '{:+.2f}%'}), use_container_width=True, hide_index=True)

# PTT 情緒
elif view_option == "💬 PTT 情緒":
    st.header("💬 PTT 情緒分析")
    with st.spinner("🔄 抓取中..."):
        sentiment, posts = load_ptt_sentiment()
    if posts:
        col1, col2, col3 = st.columns(3)
        avg = sentiment['avg_sentiment']
        bull = sentiment['bullish_ratio']
        icon = "🟢" if avg > 0.3 else ("🔴" if avg < -0.3 else "🟡")
        text = "樂觀" if avg > 0.3 else ("悲觀" if avg < -0.3 else "中性")
        col1.metric("情緒", f"{icon} {text}", f"{avg:+.2f}")
        col2.metric("多頭", f"{bull*100:.1f}%")
        col3.metric("文章", f"{sentiment['posts_count']}篇")
        st.markdown("---")
        st.subheader("🔥 熱門文章")
        for i, p in enumerate(sorted(posts, key=lambda x: x.get('push', 0), reverse=True)[:10], 1):
            st.markdown(f"{i}. {'👍' if p.get('push',0) > 0 else '👎'} {p.get('push',0)} | {p.get('title', '')} - {p.get('author', '')}")
        st.markdown("---")
        st.markdown(generate_sentiment_report(posts, sentiment))
    else:
        st.warning("無資料")

# 分析報告
elif view_option == "📝 分析報告":
    st.header("📝 分析報告")
    try:
        with open('reports/daily_report.md', 'r', encoding='utf-8') as f:
            st.markdown(f.read())
    except Exception as e:
        st.error(f"讀取失敗：{e}")

# Footer
st.markdown("---")
st.markdown(f'<div style="text-align:center;color:gray;font-size:0.9rem;">🤖 Stock Analysis System | {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>', unsafe_allow_html=True)
