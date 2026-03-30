#!/usr/bin/env python3
"""Stock Analysis Dashboard V5 - RWD + NaN Fix"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np
import sys
sys.path.append('/home/openclaw/.openclaw/workspace-stock/hello-bob')

from market_dashboard import get_market_data, calculate_market_breadth, get_sector_performance, generate_market_summary
from ptt_sentiment import fetch_ptt_stock_posts, get_market_sentiment
from commodities_analyzer import get_all_commodities_data, get_all_futures_data, generate_commodities_summary, generate_futures_summary

# 配置
st.set_page_config(page_title="台灣股票分析 V5", page_icon="📊", layout="wide")

# 樣式
st.markdown("""
<style>
.main-header { font-size: 2rem; font-weight: bold; text-align: center; color: #667eea; margin-bottom: 1rem; }
.status-bar { background: linear-gradient(135deg, #667eea, #764ba2); padding: 0.5rem; border-radius: 8px; color: white; text-align: center; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">📊 台灣股票分析系統 V5</h1>', unsafe_allow_html=True)
st.markdown(f'<div class="status-bar">🟢 {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>', unsafe_allow_html=True)
st.markdown("---")

# 側邊欄
with st.sidebar:
    view = st.radio("視圖", ["📈 大盤", "🔍 個股", "📦 原物料", "🌍 全球", "🏭 產業", "💬 PTT"])

# 載入數據
@st.cache_data(ttl=300)
def load_market():
    data = get_market_data(90)
    for s, i in data.items():
        if i['data'] is not None:
            i['data'] = i['data'].ffill().bfill().dropna()
    return data

@st.cache_data(ttl=60)
def load_breadth():
    b = calculate_market_breadth()
    for k in ['up','down','ratio','advance_decline']:
        if k in b and (pd.isna(b[k]) if isinstance(b[k], float) else False): b[k]=0
    return b

@st.cache_data(ttl=300)
def load_sectors(): return get_sector_performance()

@st.cache_data(ttl=120)
def load_ptt():
    posts = fetch_ptt_stock_posts()
    return get_market_sentiment(posts), posts

@st.cache_data(ttl=300)
def load_comm(): return get_all_commodities_data(90)

@st.cache_data(ttl=300)
def load_fut(): return get_all_futures_data(90)

def fetch_stock(sym, days=90):
    try:
        import yfinance as yf
        if not sym.endswith('.TW'): sym += '.TW'
        df = yf.Ticker(sym).history(period=f"{days}d")
        if df.empty: return None
        df = df.reset_index().rename(columns={'Date':'date','Open':'open','High':'high','Low':'low','Close':'close','Volume':'volume'})
        df = df.ffill().bfill().dropna(subset=['close'])
        df['MA20'] = df['close'].rolling(20).mean()
        df['MA60'] = df['close'].rolling(60).mean()
        delta = df['close'].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rs = gain/loss.replace(0,np.nan)
        df['RSI'] = 100-(100/(1+rs))
        return df.ffill().bfill()
    except: return None

# 大盤
if view == "📈 大盤":
    st.header("📈 大盤趨勢")
    with st.spinner("載入中..."):
        mkt = load_market()
        breadth = load_breadth()
        sectors = load_sectors()
    
    c1,c2,c3,c4 = st.columns(4)
    if '0050.TW' in mkt:
        d = mkt['0050.TW']
        if d['latest']:
            p = float(d['latest']) if not isinstance(d['latest'],(list,tuple)) else d['latest'][0]
            c1.metric("台灣 50", f"{p:.2f}", f"{float(d['change']):+.2f}%")
    if breadth:
        c2.metric("漲跌比", f"{breadth.get('up',0)}/{breadth.get('down',0)}", f"比:{breadth.get('ratio',0):.2f}")
        c3.metric("漲跌差", f"{breadth.get('advance_decline',0):+d}")
    
    st.markdown("---")
    if '0050.TW' in mkt:
        df = mkt['0050.TW']['data']
        if not df.empty:
            fig = make_subplots(3,1,shared_xaxes=True,row_heights=[0.5,0.3,0.2])
            fig.add_trace(go.Candlestick(x=df['Date'],open=df['Open'],high=df['High'],low=df['Low'],close=df['Close']),1,1)
            cols = ['red' if df['Close'].iloc[i]>=df['Open'].iloc[i] else 'green' for i in range(len(df))]
            fig.add_trace(go.Bar(x=df['Date'],y=df['Volume'],marker_color=cols),2,1)
            chg = df['Close'].pct_change().fillna(0)
            cols_c = ['red' if x>=0 else 'green' for x in chg]
            fig.add_trace(go.Bar(x=df.index,y=chg,marker_color=cols_c),3,1)
            fig.update_layout(height=600,xaxis_rangeslider_visible=False)
            st.plotly_chart(fig,use_container_width=True)
    
    st.subheader("📝 摘要")
    txt = generate_market_summary(mkt,breadth,sectors).replace('nan','N/A').replace('NaN','N/A')
    st.markdown(txt)

# 個股
elif view == "🔍 個股":
    st.header("🔍 個股分析")
    c1,c2 = st.columns([3,1])
    with c1: sym = st.text_input("代號","2330",label_visibility="collapsed")
    with c2: days = st.slider("天",30,365,90)
    if st.button("查詢",type="primary",use_container_width=True):
        df = fetch_stock(sym,days)
        if df is not None and not df.empty:
            l,p = df.iloc[-1], df.iloc[-2] if len(df)>1 else df.iloc[0]
            chg = (l['close']-p['close'])/p['close']*100 if p['close']!=0 else 0
            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("股價",f"{l['close']:.2f}",f"{chg:+.2f}%")
            c2.metric("高",f"{df['high'].max():.2f}")
            c3.metric("低",f"{df['low'].min():.2f}")
            c4.metric("量",f"{df['volume'].mean()/1e6:.1f}萬")
            rsi = l.get('RSI',50)
            if pd.isna(rsi): rsi=50
            c5.metric("RSI",f"{rsi:.1f}")
            fig = make_subplots(2,1,shared_xaxes=True,row_heights=[0.7,0.3])
            fig.add_trace(go.Candlestick(x=df['date'],open=df['open'],high=df['high'],low=df['low'],close=df['close']),1,1)
            if 'MA20' in df: fig.add_trace(go.Scatter(x=df['date'],y=df['MA20'],name='MA20'),1,1)
            fig.add_trace(go.Bar(x=df['date'],y=df['volume']),2,1)
            fig.update_layout(height=500)
            st.plotly_chart(fig,use_container_width=True)
        else: st.error("查無資料")

# 原物料
elif view == "📦 原物料":
    st.header("📦 原物料期貨")
    with st.spinner("載入中..."): comm = load_comm()
    if comm:
        cols = st.columns(min(4,len(comm)))
        for i,(n,inf) in enumerate(comm.items()):
            if i<4:
                p = inf['latest']
                if pd.isna(p): p=0
                try: cols[i].metric(n,f"{p:.2f}",f"{inf['change']:+.2f}%")
                except: cols[i].metric(n,str(round(p,2)),f"{inf['change']:+.2f}%")
        st.markdown("---")
        fig = go.Figure()
        for n,inf in comm.items():
            df = inf['data']
            if df is not None and not df.empty:
                norm = df['close']/df['close'].iloc[0]*100
                fig.add_trace(go.Scatter(x=df['date'],y=norm,name=n))
        fig.update_layout(title='走勢',height=400)
        st.plotly_chart(fig,use_container_width=True)
        st.markdown(generate_commodities_summary(comm))
    else: st.warning("無資料")

# 全球
elif view == "🌍 全球":
    st.header("🌍 全球期貨")
    with st.spinner("載入中..."): fut = load_fut()
    if fut:
        cols = st.columns(min(4,len(fut)))
        for i,(n,inf) in enumerate(fut.items()):
            if i<4:
                p = inf['latest']
                if pd.isna(p): p=0
                try: cols[i].metric(n,f"{p:.2f}",f"{inf['change']:+.2f}%")
                except: cols[i].metric(n,str(round(p,2)),f"{inf['change']:+.2f}%")
        st.markdown("---")
        fig = go.Figure()
        for n,inf in fut.items():
            df = inf['data']
            if df is not None and not df.empty:
                norm = df['close']/df['close'].iloc[0]*100
                fig.add_trace(go.Scatter(x=df['date'],y=norm,name=n))
        fig.update_layout(title='走勢',height=400)
        st.plotly_chart(fig,use_container_width=True)
        st.markdown(generate_futures_summary(fut))
    else: st.warning("無資料")

# 產業
elif view == "🏭 產業":
    st.header("🏭 產業表現")
    sec = load_sectors()
    if sec:
        for s,p in sec.items():
            with st.expander(f"{s} ({p.get('avg_change',0):+.2f}%)"):
                if p.get('stocks'):
                    sdf = pd.DataFrame(p['stocks']).sort_values('change_pct',ascending=False)
                    st.dataframe(sdf,use_container_width=True,hide_index=True)

# PTT
elif view == "💬 PTT":
    st.header("💬 PTT 情緒")
    with st.spinner("載入中..."):
        sent, posts = load_ptt()
    if posts:
        c1,c2,c3 = st.columns(3)
        avg = sent.get('avg_sentiment',0) or 0
        bull = sent.get('bullish_ratio',0) or 0
        icon = "🟢" if avg>0.3 else ("🔴" if avg<-0.3 else "🟡")
        t = "樂觀" if avg>0.3 else ("悲觀" if avg<-0.3 else "中性")
        c1.metric("情緒",f"{icon} {t}",f"{avg:+.2f}")
        c2.metric("多頭",f"{bull*100:.1f}%")
        c3.metric("文章",f"{sent.get('posts_count',0)}")
        st.markdown("---")
        for i,p in enumerate(sorted(posts,key=lambda x:x.get('push',0),reverse=True)[:10],1):
            st.markdown(f"{i}. {'👍' if p.get('push',0)>0 else '👎'} {p.get('push',0)} | {p.get('title','')}")
    else: st.warning("無資料")

st.markdown("---")
st.markdown(f"<div style='text-align:center;color:gray;font-size:0.9rem;'>V5 | {datetime.now().strftime('%Y-%m-%d')}</div>",unsafe_allow_html=True)
