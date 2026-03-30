("### 📊 情緒分析報告")
        st.markdown(generate_sentiment_report(posts, market_sentiment))
    else:
        st.warning("目前無 PTT 文章資料")

# ==================== 分析報告視圖 ====================
elif view_option == "📝 分析報告":
    st.header("📝 分析報告")
    try:
        with open('reports/daily_report.md', 'r', encoding='utf-8') as f:
            report = f.read()
        st.markdown(report)
    except Exception as e:
        st.error(f"讀取報告失敗：{e}")

# ==================== Footer ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9rem;'>
    🤖 Stock Analysis System | Powered by yfinance, Streamlit, Plotly & PTT | 
    📊 資料更新：每 60 秒 | 🔄 最後更新：{}
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
