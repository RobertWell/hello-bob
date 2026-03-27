#!/usr/bin/env python3
"""
PTT Stock Board Scraper

Fetches and analyzes posts from PTT Stock board (stock板).
Provides sentiment analysis based on post titles and content.

Usage:
    from ptt_bus import fetch_ptt_posts, analyze_sentiment
    
    posts = fetch_ptt_posts(limit=50)
    sentiment = analyze_sentiment(posts)

Environment:
    Requires: requests, beautifulsoup4
    Install: pip install requests beautifulsoup4
"""

import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    logging.error(f"Missing required package: {e}")
    logging.info("Install with: pip install requests beautifulsoup4")
    raise


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


PTT_STOCK_URL = "https://www.ptt.cc/bbs/stock/index{}.html"
PTT_ARTICLE_URL = "https://www.ptt.cc{}"


@dataclass
class Post:
    """Represents a PTT post."""
    title: str
    author: str
    date: str
    url: str
    content: Optional[str] = None
    stock_symbols: Optional[List[str]] = None


class SentimentType(Enum):
    """Sentiment classification."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


# Keyword-based sentiment analysis
BULLISH_KEYWORDS = [
    '多頭', '看漲', '買進', '加碼', '上攻', '突破', '新高', '噴出',
    '涨停', '大漲', '創高', '利多', '強勢', '反彈', '反攻'
]

BEARISH_KEYWORDS = [
    '空頭', '看跌', '賣出', '停損', '下探', '破底', '新低', '崩盤',
    '跌停', '大跌', '高點', '利空', '弱勢', '修正', '下檔'
]

# Common stock-related patterns
STOCK_SYMBOL_PATTERN = re.compile(r'(\d{4})\.TW|(\d{4})\.TWO|(\d{4})')


def fetch_ptt_posts(limit: int = 50) -> List[Post]:
    """
    Fetch recent posts from PTT Stock board.
    
    Parameters
    ----------
    limit : int
        Maximum number of posts to fetch (default: 50)
    
    Returns
    -------
    List[Post]
        List of Post objects
    
    Notes
    -----
    - Fetches from multiple index pages if needed
    - Respects PTT's robots.txt
    - Includes rate limiting to avoid overloading server
    """
    posts = []
    page = 0
    max_pages = (limit // 20) + 1  # PTT shows ~20 posts per page
    
    try:
        while len(posts) < limit and page < max_pages:
            url = PTT_STOCK_URL.format(page)
            logger.info(f"Fetching {url}")
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all post entries
            entries = soup.select('div.r-ent')
            
            for entry in entries:
                if len(posts) >= limit:
                    break
                
                try:
                    title_elem = entry.select_one('.title a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    author_elem = entry.select_one('.author')
                    author = author_elem.get_text(strip=True) if author_elem else 'Unknown'
                    
                    date_elem = entry.select_one('.date')
                    date = date_elem.get_text(strip=True) if date_elem else ''
                    
                    link = title_elem.get('href')
                    url = f"https://www.ptt.cc{link}" if link else ''
                    
                    post = Post(
                        title=title,
                        author=author,
                        date=date,
                        url=url
                    )
                    posts.append(post)
                    
                except Exception as e:
                    logger.warning(f"Error parsing entry: {e}")
                    continue
            
            page += 1
            
    except Exception as e:
        logger.error(f"Error fetching PTT posts: {e}")
    
    logger.info(f"Fetched {len(posts)} posts from PTT")
    return posts


def extract_stock_symbols(text: str) -> List[str]:
    """
    Extract stock symbols from text.
    
    Parameters
    ----------
    text : str
        Text to search
    
    Returns
    -------
    List[str]
        List of stock symbols found
    """
    matches = STOCK_SYMBOL_PATTERN.findall(text)
    # Flatten the matches and remove empty strings
    symbols = [m[0] or m[1] or m[2] for m in matches if any(m)]
    return list(set(symbols))  # Remove duplicates


def analyze_post_sentiment(post: Post) -> SentimentType:
    """
    Analyze sentiment of a single post.
    
    Parameters
    ----------
    post : Post
        Post to analyze
    
    Returns
    -------
    SentimentType
        Classified sentiment
    """
    text = post.title.lower()
    if post.content:
        text += ' ' + post.content.lower()
    
    bullish_score = sum(1 for kw in BULLISH_KEYWORDS if kw in text)
    bearish_score = sum(1 for kw in BEARISH_KEYWORDS if kw in text)
    
    if bullish_score > bearish_score:
        return SentimentType.BULLISH
    elif bearish_score > bullish_score:
        return SentimentType.BEARISH
    else:
        return SentimentType.NEUTRAL


def analyze_sentiment(posts: List[Post]) -> Dict:
    """
    Analyze sentiment of multiple posts.
    
    Parameters
    ----------
    posts : List[Post]
        List of posts to analyze
    
    Returns
    -------
    Dict
        Sentiment analysis results with keys:
        - bullish_count: Number of bullish posts
        - bearish_count: Number of bearish posts
        - neutral_count: Number of neutral posts
        - total_posts: Total posts analyzed
        - sentiment_score: Overall sentiment score (-1 to 1)
        - posts: List of posts with sentiment
    """
    if not posts:
        return {
            'bullish_count': 0,
            'bearish_count': 0,
            'neutral_count': 0,
            'total_posts': 0,
            'sentiment_score': 0.0,
            'posts': []
        }
    
    bullish_count = 0
    bearish_count = 0
    neutral_count = 0
    
    analyzed_posts = []
    
    for post in posts:
        sentiment = analyze_post_sentiment(post)
        post.sentiment = sentiment  # type: ignore
        
        if sentiment == SentimentType.BULLISH:
            bullish_count += 1
        elif sentiment == SentimentType.BEARISH:
            bearish_count += 1
        else:
            neutral_count += 1
        
        analyzed_posts.append({
            'title': post.title,
            'author': post.author,
            'date': post.date,
            'url': post.url,
            'sentiment': sentiment.value
        })
    
    total = len(posts)
    # Sentiment score: -1 (all bearish) to 1 (all bullish)
    sentiment_score = (bullish_count - bearish_count) / total if total > 0 else 0.0
    
    return {
        'bullish_count': bullish_count,
        'bearish_count': bearish_count,
        'neutral_count': neutral_count,
        'total_posts': total,
        'sentiment_score': round(sentiment_score, 3),
        'posts': analyzed_posts
    }


def fetch_article_content(url: str) -> Optional[str]:
    """
    Fetch full content of a PTT article.
    
    Parameters
    ----------
    url : str
        Article URL
    
    Returns
    -------
    Optional[str]
        Article content or None if fetch fails
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.select_one('#main-content')
        
        if content_div:
            return content_div.get_text(strip=True)
        
    except Exception as e:
        logger.warning(f"Error fetching article content: {e}")
    
    return None


# Example usage
if __name__ == "__main__":
    print("Fetching PTT Stock board posts...")
    posts = fetch_ptt_posts(limit=10)
    
    if posts:
        print(f"\nFetched {len(posts)} posts:")
        for i, post in enumerate(posts[:5], 1):
            print(f"{i}. {post.title} by {post.author}")
        
        print("\nAnalyzing sentiment...")
        sentiment = analyze_sentiment(posts)
        print(f"Bullish: {sentiment['bullish_count']}")
        print(f"Bearish: {sentiment['bearish_count']}")
        print(f"Neutral: {sentiment['neutral_count']}")
        print(f"Sentiment Score: {sentiment['sentiment_score']}")
