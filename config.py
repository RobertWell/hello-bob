"""
Stock Analysis Configuration

Defines the list of stocks to track and analysis parameters.
"""

# Taiwan Stock Exchange (TWSE) listed companies - Key sectors
# Source: https://www.twse.com.tw/zh/page/trading/exchange/STOCK_LIST.html

STOCK_UNIVERSE = {
    # ===== Technology / Semiconductors =====
    '2330': '台積電',      # TSMC
    '2317': '鴻海',        # Hon Hai/Foxconn
    '2454': '聯發科',      # MediaTek
    '2308': '台達電',      # Delta Electronics
    '2353': '宏碁',        # Acer
    '2357': '華碩',        # ASUS
    '2395': '研華',        # Advantech
    '2337': '旺宏',        # Macronix
    '2344': '華邦電',      # Winbond
    '2336': '亞太電',      # Asia Pacific Telecom
    
    # ===== Finance =====
    '2881': '富邦金',      # Fubon Financial
    '2882': '國泰金',      # Cathay Financial
    '2886': '兆豐金',      # Mega Financial
    '2891': '中信金',      # CTBC Financial
    '2892': '第一金',      # First Financial
    '2880': '開發金',      # SinoPac Financial
    
    # ===== Traditional Industry =====
    '1301': '台塑',        # Formosa Plastics
    '1303': '南亞',        # Nan Ya Plastics
    '1326': '台化',        # Formosa Chemicals
    '1101': '台泥',        # Taiwan Cement
    '1102': '亞泥',        # Asia Cement
    
    # ===== Services / Retail =====
    '2912': '統一超',      # 7-Eleven Taiwan
    '2901': '遠百',        # Far Eastern Department Stores
    '1216': '統一',        # Uni-President
    
    # ===== ETF =====
    '0050': '元大台灣50',  # Yuanta Taiwan Top 50
    '006208': '元大S&P500', # Yuanta S&P 500
    '00888': '國泰台灣5G+', # Cathay Taiwan 5G+
    
    # ===== Key International (for correlation, if available) =====
    # These would need different data sources (Yahoo Finance US market)
    # 'AAPL': 'Apple',
    # 'NVDA': 'NVIDIA',
    # 'TSM': 'TSMC ADR',
}

# Analysis parameters
ANALYSIS_CONFIG = {
    # Historical data period
    'history_days': 365,  # 1 year
    
    # Indicator parameters
    'sma_periods': [5, 10, 20, 60, 120],  # Short, medium, long term
    'ema_periods': [12, 26],
    'rsi_period': 14,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'bb_period': 20,
    'bb_std': 2.0,
    
    # Sentiment analysis
    'sentiment_window_days': 7,  # Analyze sentiment over last 7 days
    'min_posts_for_sentiment': 10,  # Minimum posts for reliable sentiment
    
    # Correlation analysis
    'correlation_window_days': 60,  # Calculate correlations over 60 days
    'min_correlation_threshold': 0.5,  # Minimum correlation to track
}

# Database settings
DB_PATH = 'stock_data.db'

# PTT settings
PTT_STOCK_URL = "https://www.ptt.cc/bbs/stock/index{}.html"
PTT_MAX_PAGES = 5  # Fetch from 5 pages of PTT
