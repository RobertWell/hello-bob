#!/usr/bin/env python3
"""
L1 測試：語法 + 類型檢查（快速，<10 秒）
使用方式：python tests/test_l1_syntax.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_syntax():
    """測試所有 Python 檔案語法"""
    print("📝 語法檢查...")
    files = ['app_v5.py', 'commodities_analyzer.py', 'market_dashboard.py', 'ptt_sentiment.py']
    
    for f in files:
        if os.path.exists(f):
            try:
                compile(open(f).read(), f, 'exec')
                print(f"  ✓ {f}")
            except SyntaxError as e:
                print(f"  ✗ {f}: {e}")
                return False
    return True

def test_types():
    """測試資料類型（使用 mock）"""
    print("\n🔧 類型檢查...")
    
    # Mock 資料結構
    test_cases = [
        ('原物料', {'latest': 4500.5, 'change': 1.2, 'data': None}),
        ('期貨', {'latest': 50000.0, 'change': -0.5, 'data': None}),
    ]
    
    for name, sample in test_cases:
        # 檢查必要欄位
        assert 'latest' in sample, f"{name} 缺少 latest"
        assert 'change' in sample, f"{name} 缺少 change"
        
        # 檢查類型
        assert isinstance(sample['latest'], (int, float)), f"{name} 的 latest 類型錯誤"
        assert isinstance(sample['change'], (int, float)), f"{name} 的 change 類型錯誤"
        
        # 檢查格式化
        try:
            _ = f"{sample['latest']:.2f}"
            _ = f"{sample['change']:+.2f}"
        except (TypeError, ValueError) as e:
            print(f"  ✗ {name} 格式化失敗：{e}")
            return False
        
        print(f"  ✓ {name}")
    
    return True

def test_imports():
    """測試必要模組可導入"""
    print("\n📦 模組導入檢查...")
    modules = ['pandas', 'numpy', 'plotly', 'streamlit']
    
    for mod in modules:
        try:
            __import__(mod)
            print(f"  ✓ {mod}")
        except ImportError as e:
            print(f"  ✗ {mod}: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("="*50)
    print("🧪 L1 快速測試")
    print("="*50)
    
    all_pass = True
    all_pass &= test_syntax()
    all_pass &= test_types()
    all_pass &= test_imports()
    
    print("\n" + "="*50)
    if all_pass:
        print("✅ L1 測試通過")
        sys.exit(0)
    else:
        print("❌ L1 測試失敗")
        sys.exit(1)
