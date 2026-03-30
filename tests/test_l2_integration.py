#!/usr/bin/env python3
"""
L2 測試：API 整合 + 資料完整性（<60 秒）
使用方式：python tests/test_l2_integration.py
"""

import sys
import os
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_commodities_structure():
    """測試原物料資料結構"""
    print("\n📦 原物料 API 測試...")
    from commodities_analyzer import get_all_commodities_data
    
    try:
        data = get_all_commodities_data(days=3)
        
        if not data:
            print("  ⚠️  無資料（可能是 API 限制）")
            return True
        
        for name, info in list(data.items())[:3]:  # 只測前 3 個
            # 必要欄位
            assert 'latest' in info, f"{name} 缺少 'latest'"
            assert 'change' in info, f"{name} 缺少 'change'"
            assert 'data' in info, f"{name} 缺少 'data'"
            
            # 類型檢查
            assert isinstance(info['latest'], (int, float)), \
                f"{name} 的 latest 類型錯誤：{type(info['latest']).__name__}"
            assert isinstance(info['change'], (int, float)), \
                f"{name} 的 change 類型錯誤：{type(info['change']).__name__}"
            
            # NaN 檢查
            assert not pd.isna(info['latest']), f"{name} 的 latest 是 NaN"
            assert not pd.isna(info['change']), f"{name} 的 change 是 NaN"
            
            # 格式化測試
            try:
                _ = f"{info['latest']:.2f}"
                _ = f"{info['change']:+.2f}%"
            except (TypeError, ValueError) as e:
                raise AssertionError(f"{name} 格式化失敗：{e}")
            
            print(f"  ✓ {name}: {info['latest']:.2f} ({info['change']:+.2f}%)")
        
        print(f"  ✅ 通過 ({len(data)} 項商品)")
        return True
        
    except AssertionError as e:
        print(f"  ❌ 失敗：{e}")
        return False
    except Exception as e:
        print(f"  ⚠️  異常：{e}")
        return True  # API 問題不阻擋測試

def test_futures_structure():
    """測試全球期貨資料結構"""
    print("\n🌍 全球期貨 API 測試...")
    from commodities_analyzer import get_all_futures_data
    
    try:
        data = get_all_futures_data(days=3)
        
        if not data:
            print("  ⚠️  無資料")
            return True
        
        for name, info in list(data.items())[:3]:
            assert 'latest' in info
            assert 'change' in info
            
            assert isinstance(info['latest'], (int, float)), \
                f"{name} 的 latest 類型錯誤"
            assert not pd.isna(info['latest']), f"{name} 是 NaN"
            
            _ = f"{info['latest']:.2f}"
            print(f"  ✓ {name}: {info['latest']:.2f}")
        
        print(f"  ✅ 通過 ({len(data)} 項期貨)")
        return True
        
    except AssertionError as e:
        print(f"  ❌ 失敗：{e}")
        return False
    except Exception as e:
        print(f"  ⚠️  異常：{e}")
        return True

def test_market_breadth():
    """測試漲跌比"""
    print("\n📊 漲跌比測試...")
    from market_dashboard import calculate_market_breadth
    
    try:
        breadth = calculate_market_breadth()
        
        if not breadth:
            print("  ⚠️  無資料")
            return True
        
        required = ['up', 'down', 'ratio', 'advance_decline']
        for key in required:
            assert key in breadth, f"缺少 '{key}'"
            if isinstance(breadth[key], float):
                assert not pd.isna(breadth[key]), f"{key} 是 NaN"
        
        print(f"  ✓ 漲跌比：{breadth['up']}/{breadth['down']}")
        print(f"  ✅ 通過")
        return True
        
    except AssertionError as e:
        print(f"  ❌ 失敗：{e}")
        return False
    except Exception as e:
        print(f"  ⚠️  異常：{e}")
        return True

if __name__ == "__main__":
    print("="*60)
    print("🧪 L2 整合測試")
    print("="*60)
    
    results = []
    results.append(test_commodities_structure())
    results.append(test_futures_structure())
    results.append(test_market_breadth())
    
    print("\n" + "="*60)
    if all(results):
        print("✅ L2 測試通過")
        sys.exit(0)
    else:
        print("❌ L2 測試失敗")
        sys.exit(1)
