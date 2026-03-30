#!/usr/bin/env python3
"""
測試套件 - 確保程式碼品質
- 資料載入測試
- NaN 檢查
- API 回應測試
- 整合測試
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append('/home/openclaw/.openclaw/workspace-stock/hello-bob')

from commodities_analyzer import get_all_commodities_data, get_all_futures_data, COMMODITIES, GLOBAL_FUTURES
from market_dashboard import get_market_data, calculate_market_breadth, get_sector_performance
from ptt_sentiment import fetch_ptt_stock_posts, get_market_sentiment

def test_commodities_data():
    """測試原物料資料載入"""
    print("📦 測試原物料資料...")
    try:
        data = get_all_commodities_data(days=5)  # 減少天數加速
        assert len(data) > 0, "原物料資料為空"
        
        for name, info in data.items():
            # 檢查必要的鍵
            assert 'latest' in info, f"{name} 缺少 'latest'"
            assert 'change' in info, f"{name} 缺少 'change'"
            assert 'data' in info, f"{name} 缺少 'data'"
            
            # 檢查資料類型
            assert isinstance(info['latest'], (int, float)), f"{name} 的 latest 不是數值：{type(info['latest'])}"
            assert isinstance(info['change'], (int, float)), f"{name} 的 change 不是數值"
            
            # 檢查 NaN
            assert not pd.isna(info['latest']), f"{name} 的 latest 是 NaN"
            assert not pd.isna(info['change']), f"{name} 的 change 是 NaN"
            
            # 檢查數據框
            if info['data'] is not None:
                assert not info['data'].empty, f"{name} 的數據為空"
                assert 'close' in info['data'].columns, f"{name} 缺少 'close' 欄位"
        
        print(f"  ✓ 通過 ({len(data)} 項商品)")
        return True
    except Exception as e:
        print(f"  ✗ 失敗：{e}")
        return False

def test_futures_data():
    """測試期貨資料載入"""
    print("🌍 測試全球期貨資料...")
    try:
        data = get_all_futures_data(days=5)  # 減少天數加速
        assert len(data) > 0, "期貨資料為空"
        
        for name, info in data.items():
            assert 'latest' in info, f"{name} 缺少 'latest'"
            assert 'change' in info, f"{name} 缺少 'change'"
            assert 'data' in info, f"{name} 缺少 'data'"
            
            assert isinstance(info['latest'], (int, float)), f"{name} 的 latest 不是數值：{type(info['latest'])}"
            assert isinstance(info['change'], (int, float)), f"{name} 的 change 不是數值"
            
            assert not pd.isna(info['latest']), f"{name} 的 latest 是 NaN"
            assert not pd.isna(info['change']), f"{name} 的 change 是 NaN"
        
        print(f"  ✓ 通過 ({len(data)} 項期貨)")
        return True
    except Exception as e:
        print(f"  ✗ 失敗：{e}")
        return False

def test_market_data():
    """測試大盤資料"""
    print("📈 測試大盤資料...")
    try:
        data = get_market_data(days=10)  # 減少天數加速
        assert len(data) > 0, "大盤資料為空"
        
        if '0050.TW' in data:
            d = data['0050.TW']
            if d['data'] is not None and not d['data'].empty:
                assert 'Close' in d['data'].columns, "缺少 'Close' 欄位"
                assert not d['data'].isna().all().all(), "數據全部是 NaN"
        
        print(f"  ✓ 通過 ({len(data)} 個標的)")
        return True
    except Exception as e:
        print(f"  ✗ 失敗：{e}")
        return False

def test_breadth():
    """測試漲跌比"""
    print("📊 測試漲跌比...")
    try:
        breadth = calculate_market_breadth()
        assert breadth is not None, "漲跌比為空"
        
        required_keys = ['up', 'down', 'ratio', 'advance_decline']
        for key in required_keys:
            assert key in breadth, f"缺少 '{key}'"
            if isinstance(breadth[key], float):
                assert not pd.isna(breadth[key]), f"{key} 是 NaN"
        
        print(f"  ✓ 通過 (漲跌比：{breadth['up']}/{breadth['down']})")
        return True
    except Exception as e:
        print(f"  ✗ 失敗：{e}")
        return False

def test_ptt():
    """測試 PTT 情緒"""
    print("💬 測試 PTT 情緒...")
    try:
        posts = fetch_ptt_stock_posts()
        assert posts is not None, "PTT 文章為空"
        
        sentiment = get_market_sentiment(posts)
        assert 'avg_sentiment' in sentiment, "缺少 'avg_sentiment'"
        assert 'bullish_ratio' in sentiment, "缺少 'bullish_ratio'"
        
        print(f"  ✓ 通過 ({len(posts)} 篇文章)")
        return True
    except Exception as e:
        print(f"  ✗ 失敗：{e}")
        return False

def test_formatting():
    """測試格式化（避免 TypeError）"""
    print("🔧 測試格式化...")
    try:
        # 測試原物料格式化
        data = get_all_commodities_data(days=5)
        for name, info in data.items():
            try:
                _ = f"{info['latest']:.2f}"
                _ = f"{info['change']:+.2f}"
            except (TypeError, ValueError) as e:
                raise AssertionError(f"{name} 格式化失敗：{e}")
        
        # 測試期貨格式化
        data = get_all_futures_data(days=5)
        for name, info in data.items():
            try:
                _ = f"{info['latest']:.2f}"
                _ = f"{info['change']:+.2f}"
            except (TypeError, ValueError) as e:
                raise AssertionError(f"{name} 格式化失敗：{e}")
        
        print("  ✓ 通過")
        return True
    except Exception as e:
        print(f"  ✗ 失敗：{e}")
        return False

def run_all_tests():
    """執行所有測試"""
    print("="*60)
    print(f"🧪 測試執行 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 快速測試組合（減少天數）
    tests = [
        ("格式化", test_formatting),  # 最快
        ("原物料資料", test_commodities_data),
        ("大盤資料", test_market_data),
        ("漲跌比", test_breadth),
        # ("全球期貨", test_futures_data),  # 跳過（慢）
        # ("PTT 情緒", test_ptt),  # 跳過（慢）
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ {name} 異常：{e}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("📊 測試結果摘要")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {status} - {name}")
    
    print(f"\n總計：{passed}/{total} 通過")
    print("="*60)
    
    if passed == total:
        print("🎉 所有測試通過！")
        return 0
    else:
        print("⚠️  有測試失敗，請檢查！")
        return 1

if __name__ == "__main__":
    exit(run_all_tests())
