#!/usr/bin/env python3
"""
超快速本地 CI 檢查（<15 秒）
"""

import sys
import os
from datetime import datetime
from pathlib import Path

workspace = Path('/home/openclaw/.openclaw/workspace-stock/hello-bob')

print("="*60)
print(f"🧪 快速 CI 檢查 - {datetime.now().strftime('%H:%M:%S')}")
print("="*60)

# 1. 語法檢查
print("\n1. 語法檢查...")
files = ['app_v5.py', 'commodities_analyzer.py', 'market_dashboard.py']
for f in files:
    p = workspace / f
    if p.exists():
        try:
            compile(open(p).read(), str(p), 'exec')
            print(f"  ✓ {f}")
        except SyntaxError as e:
            print(f"  ✗ {f}: {e}")
            sys.exit(1)

# 2. 必要檔案檢查
print("\n2. 檔案完整性...")
required = ['app_v5.py', 'commodities_analyzer.py', 'market_dashboard.py', 'ptt_sentiment.py']
for f in required:
    if (workspace / f).exists():
        print(f"  ✓ {f}")
    else:
        print(f"  ✗ {f} 缺失")

# 3. 服務健康
print("\n3. 服務健康...")
try:
    import urllib.request
    with urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=3) as r:
        if r.status == 200:
            print("  ✓ Streamlit 運行正常")
        else:
            print("  ⚠️  Streamlit 回應異常")
except:
    print("  ⚠️  Streamlit 未運行")

print("\n" + "="*60)
print("✅ 快速檢查完成")
print("="*60)
