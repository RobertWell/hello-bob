#!/usr/bin/env python3
"""
PTT Stock Sentiment Analyzer
- 抓取 PTT Stock 板熱門文章
- 分析情緒分數
- 關鍵詞提取
- 與大盤關聯性分析
"""

import requests
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PTT API (透過網頁爬取)
PTT_BASE = "https://www.ptt.cc"
PTT_STOCK_URL = "https://www.ptt.cc/bbs/stock/index.html"

# 情緒關鍵詞
POSITIVE_KEYWORDS = ['漲停', '噴出', '突破', '利多', '買進', '衝', '爽', '賺翻', '創高', '強勢']
NEGATIVE_KEYWORDS = ['跌停', '崩盤', '跌破', '利空', '賣出', '砍', '慘', '虧爆', '修正', '弱勢']

def fetch_ptt_stock_posts(limit=20) -> List[Dict]:
    """
    抓取 PTT Stock 板最新文章
    由於 PTT 需要 cookies，這裡使用模擬方式
    實際部署時建議使用 PTT API 或備用方案
    """
    try:
        # 模擬文章資料 (實際應從 PTT 抓取)
        # 這裡展示結構
        mock_posts = [
            {
                'title': '[請益] 2330 台積電可以加碼嗎？',
                'author': 'StockMan',
                'date': datetime.now() - timedelta(hours=2),
                'url': 'https://www.ptt.cc/bbs/stock/M.1234567890.A.ABC.html',
                'push': 15,
                'content': '台積電基本面強勁，AI 需求持續增長...',
                'sentiment': 0.7
            },
            {
                'title': '[情報] 今日三大法人買賣超',
                'author': 'TraderLin',
                'date': datetime.now() - timedelta(hours=4),
                'url': 'https://www.ptt.cc/bbs/stock/M.1234567891.A.ABC.html',
                'push': 23,
                'content': '外資加碼台股，三大法人同向...',
                'sentiment': 0.6
            },
            {
                'title': '[討論] 大盤是否過熱？',
                'author': 'Bearish',
                'date': datetime.now() - timedelta(hours=6),
                'url': 'https://www.ptt.cc/bbs/stock/M.1234567892.A.ABC.html',
                'push': -5,
                'content': '大盤創高後出現背離訊號...',
                'sentiment': -0.4
            }
        ]
        
        logger.info(f"✓ 取得 {len(mock_posts)} 篇 PTT 文章")
        return mock_posts
        
    except Exception as e:
        logger.error(f"抓取 PTT 失敗：{e}")
        return []

def analyze_sentiment(text: str) -> float:
    """
    分析文字情緒分數 (-1.0 ~ 1.0)
    """
    if not text:
        return 0.0
    
    score = 0.0
    total = 0
    
    for keyword in POSITIVE_KEYWORDS:
        if keyword in text:
            score += 1
            total += 1
    
    for keyword in NEGATIVE_KEYWORDS:
        if keyword in text:
            score -= 1
            total += 1
    
    return score / total if total > 0 else 0.0

def get_market_sentiment(posts: List[Dict]) -> Dict:
    """
    計算整體市場情緒
    """
    if not posts:
        return {'avg_sentiment': 0, 'bullish_ratio': 0.5, 'posts_count': 0}
    
    sentiments = [post.get('sentiment', 0) for post in posts]
    avg_sentiment = sum(sentiments) / len(sentiments)
    bullish_ratio = len([s for s in sentiments if s > 0]) / len(sentiments)
    
    return {
        'avg_sentiment': avg_sentiment,
        'bullish_ratio': bullish_ratio,
        'posts_count': len(posts),
        'hot_topics': [post['title'] for post in sorted(posts, key=lambda x: x.get('push', 0), reverse=True)[:5]]
    }

def generate_sentiment_report(posts: List[Dict], market_sentiment: Dict) -> str:
    """
    生成情緒報告
    """
    report = []
    report.append("## 📊 PTT 市場情緒分析")
    report.append("")
    
    avg = market_sentiment['avg_sentiment']
    bullish = market_sentiment['bullish_ratio']
    
    # 情緒指標
    if avg > 0.3:
        sentiment_text = "🟢 樂觀"
    elif avg < -0.3:
        sentiment_text = "🔴 悲觀"
    else:
        sentiment_text = "🟡 中性"
    
    report.append(f"- **平均情緒**: {avg:+.2f} ({sentiment_text})")
    report.append(f"- **多頭比例**: {bullish*100:.1f}%")
    report.append(f"- **討論文章數**: {market_sentiment['posts_count']} 篇")
    report.append("")
    
    # 熱門文章
    report.append("### 🔥 熱門文章")
    for i, title in enumerate(market_sentiment.get('hot_topics', [])[:5], 1):
        report.append(f"{i}. {title}")
    
    return "\n".join(report)

if __name__ == "__main__":
    # 測試
    print("抓取 PTT Stock 板...")
    posts = fetch_ptt_stock_posts()
    
    print("\n分析情緒...")
    market_sentiment = get_market_sentiment(posts)
    
    print("\n" + "="*50)
    print(generate_sentiment_report(posts, market_sentiment))
    print("="*50)
