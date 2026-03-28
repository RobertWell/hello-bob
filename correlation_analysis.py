#!/usr/bin/env python3
"""
Stock Correlation Analysis

Analyzes correlations between stocks to identify:
- Highly correlated stock pairs
- Sector correlations
- Market leaders and followers

Usage:
    python correlation_analysis.py
"""

import logging
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from config import STOCK_UNIVERSE, ANALYSIS_CONFIG, DB_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_price_data(symbols: List[str] = None, days: int = None) -> pd.DataFrame:
    """
    Load price data for multiple stocks.
    
    Parameters
    ----------
    symbols : List[str], optional
        List of stock symbols
    days : int, optional
        Number of days to load
    
    Returns
    -------
    pd.DataFrame
        DataFrame with close prices for all stocks
    """
    import sqlite3
    
    if symbols is None:
        symbols = list(STOCK_UNIVERSE.keys())
    
    if days is None:
        days = ANALYSIS_CONFIG['history_days']
    
    conn = sqlite3.connect(DB_PATH)
    
    # Build query for all symbols
    placeholders = ','.join('?' * len(symbols))
    query = f'''
        SELECT symbol, date, close
        FROM stock_prices
        WHERE symbol IN ({placeholders})
        AND date >= date('now', ?)
        ORDER BY date
    '''
    
    df = pd.read_sql_query(
        query, 
        conn, 
        params=symbols + [f'-{days} days']
    )
    conn.close()
    
    if df.empty:
        logger.warning("No price data found in database")
        return df
    
    # Pivot to get close prices for each symbol
    df['date'] = pd.to_datetime(df['date'])
    price_df = df.pivot(index='date', columns='symbol', values='close')
    
    return price_df


def calculate_correlation_matrix(price_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate correlation matrix for stock returns.
    
    Parameters
    ----------
    price_df : pd.DataFrame
        DataFrame with close prices
    
    Returns
    -------
    pd.DataFrame
        Correlation matrix
    """
    # Calculate daily returns
    returns = price_df.pct_change().dropna()
    
    # Calculate correlation matrix
    corr_matrix = returns.corr()
    
    return corr_matrix


def find_highly_correlated_pairs(
    corr_matrix: pd.DataFrame, 
    threshold: float = 0.7
) -> List[Tuple[str, str, float]]:
    """
    Find stock pairs with high correlation.
    
    Parameters
    ----------
    corr_matrix : pd.DataFrame
        Correlation matrix
    threshold : float
        Minimum correlation threshold
    
    Returns
    -------
    List[Tuple[str, str, float]]
        List of (symbol1, symbol2, correlation) tuples
    """
    pairs = []
    
    # Get upper triangle of matrix
    for i in range(len(corr_matrix)):
        for j in range(i + 1, len(corr_matrix)):
            symbol1 = corr_matrix.index[i]
            symbol2 = corr_matrix.index[j]
            corr_value = corr_matrix.iloc[i, j]
            
            if abs(corr_value) >= threshold:
                pairs.append((symbol1, symbol2, corr_value))
    
    # Sort by correlation strength
    pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    
    return pairs


def identify_sector_correlations(corr_matrix: pd.DataFrame) -> Dict:
    """
    Identify correlations within and between sectors.
    
    Parameters
    ----------
    corr_matrix : pd.DataFrame
        Correlation matrix
    
    Returns
    -------
    Dict
        Sector correlation analysis
    """
    # Simple sector classification (can be enhanced)
    sector_map = {
        '2330': 'Technology',
        '2317': 'Technology',
        '2454': 'Technology',
        '2308': 'Technology',
        '2353': 'Technology',
        '2357': 'Technology',
        '2881': 'Finance',
        '2882': 'Finance',
        '2886': 'Finance',
        '1301': 'Traditional',
        '1303': 'Traditional',
        '1326': 'Traditional',
    }
    
    sectors = {}
    for symbol in corr_matrix.columns:
        sector = sector_map.get(symbol, 'Other')
        if sector not in sectors:
            sectors[sector] = []
        sectors[sector].append(symbol)
    
    # Calculate intra-sector correlations
    sector_corr = {}
    for sector, symbols in sectors.items():
        if len(symbols) > 1:
            sub_corr = corr_matrix.loc[symbols, symbols]
            avg_corr = sub_corr.where(np.triu(np.ones(sub_corr.shape), k=1) == 1).mean().mean()
            sector_corr[sector] = {
                'avg_correlation': avg_corr,
                'stocks': symbols
            }
    
    return sector_corr


def analyze_correlation_trends(price_df: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """
    Analyze how correlations change over time.
    
    Parameters
    ----------
    price_df : pd.DataFrame
        DataFrame with close prices
    window : int
        Rolling window size
    
    Returns
    -------
    pd.DataFrame
        Rolling correlation trends
    """
    returns = price_df.pct_change().dropna()
    
    # Calculate rolling correlations (example: TSMC vs market)
    if '2330' in returns.columns:
        rolling_corr = returns['2330'].rolling(window).corr(returns.mean(axis=1))
        return rolling_corr
    
    return None


def main():
    """Main analysis function."""
    logger.info("Starting correlation analysis...")
    
    # Load price data
    price_df = load_price_data()
    
    if price_df is None or price_df.empty or price_df.shape[1] < 2:
        logger.error("Insufficient data for correlation analysis")
        return
    
    logger.info(f"Loaded data for {len(price_df.columns)} stocks")
    
    # Calculate correlation matrix
    corr_matrix = calculate_correlation_matrix(price_df)
    
    logger.info("\n" + "="*60)
    logger.info("CORRELATION MATRIX")
    logger.info("="*60)
    print(corr_matrix.round(3))
    
    # Find highly correlated pairs
    high_corr_pairs = find_highly_correlated_pairs(corr_matrix, threshold=0.7)
    
    logger.info("\n" + "="*60)
    logger.info("HIGHLY CORRELATED PAIRS (>0.7)")
    logger.info("="*60)
    
    for symbol1, symbol2, corr in high_corr_pairs[:10]:  # Top 10
        name1 = STOCK_UNIVERSE.get(symbol1, symbol1)
        name2 = STOCK_UNIVERSE.get(symbol2, symbol2)
        logger.info(f"{symbol1} ({name1}) ↔ {symbol2} ({name2}): {corr:.3f}")
    
    # Sector analysis
    sector_analysis = identify_sector_correlations(corr_matrix)
    
    logger.info("\n" + "="*60)
    logger.info("SECTOR CORRELATIONS")
    logger.info("="*60)
    
    for sector, data in sector_analysis.items():
        logger.info(f"{sector}: Avg Corr = {data['avg_correlation']:.3f}")
        logger.info(f"  Stocks: {', '.join(data['stocks'])}")


if __name__ == "__main__":
    main()
