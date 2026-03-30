#!/usr/bin/env python3
"""快速測試套件 - 只測試關鍵問題"""

import sys
import pandas as pd
sys.path.append('/home/openclaw/.openclaw/workspace-stock/hello-bob')

from commodities_analyzer import get_all_commodities_data, get_all_futures_data

print("="*50)
print("🧪 快速測試")
print("="*50)

# Test 1: 原物料
print("\n1. 測試原物料資料...")
try:
    comm = get_all_commodities_data(days=5)
    for name, info in list(comm.items())[:3]:  # 只測前 3 個
        assert isinstance(info['latest'], (int, float)), f"{name} 類型錯誤"
        assert not pd.isna(info['latest']), f"{name} 是 NaN"
        _ = f"{info['latest']:.2f}"  # 測試格式化
        print(f"  ✓ {name}: {info['latest']:.2f} ({info['change']:+.2f}%)")
    print("  ✅ 原物料測試通過")
except Exception as e:
    print(f"  ❌ 失敗：{e}")
    sys.exit(1)

# Test 2: 全球期貨
print("\n2. 測試全球期貨...")
try:
    fut = get_all_futures_data(days=5)
    for name, info in list(fut.items())[:3]:  # 只測前 3 個
        assert isinstance(info['latest'], (int, float)), f"{name} 類型錯誤"
        assert not pd.isna(info['latest']), f"{name} 是 NaN"
        _ = f"{info['latest']:.2f}"
        print(f"  ✓ {name}: {info['latest']:.2f} ({info['change']:+.2f}%)")
    print("  ✅ 全球期貨測試通過")
except Exception as e:
    print(f"  ❌ 失敗：{e}")
    sys.exit(1)

print("\n" + "="*50)
print("✅ 所有測試通過！")
print("="*50)
