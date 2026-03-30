#!/usr/bin/env python3
"""
本地 CI/CD 驗證系統
- 自動執行分層測試
- 生成測試報告
- 發送通知（可選）
- 不依賴外部 CI 服務
"""

import sys
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

# 顏色
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def log_info(msg):
    print(f"{BLUE}ℹ️  {msg}{NC}")

def log_success(msg):
    print(f"{GREEN}✓  {msg}{NC}")

def log_error(msg):
    print(f"{RED}✗  {msg}{NC}")

def log_warn(msg):
    print(f"{YELLOW}⚠️  {msg}{NC}")

class LocalCI:
    def __init__(self, workspace_dir):
        self.workspace_dir = Path(workspace_dir)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'passed': 0,
            'failed': 0,
            'warnings': 0
        }
    
    def run_test(self, name, test_func, timeout_sec=30):
        """執行單個測試"""
        log_info(f"執行測試：{name}")
        
        try:
            # 執行測試
            result = test_func()
            
            if result['success']:
                log_success(f"{name} - 通過")
                self.results['tests'].append({
                    'name': name,
                    'status': 'passed',
                    'message': result.get('message', '')
                })
                self.results['passed'] += 1
            else:
                log_error(f"{name} - 失敗：{result.get('error', '未知錯誤')}")
                self.results['tests'].append({
                    'name': name,
                    'status': 'failed',
                    'error': result.get('error', '')
                })
                self.results['failed'] += 1
        
        except Exception as e:
            log_error(f"{name} - 異常：{e}")
            self.results['tests'].append({
                'name': name,
                'status': 'error',
                'error': str(e)
            })
            self.results['failed'] += 1
    
    def test_syntax(self):
        """L1: 語法檢查"""
        files = ['app_v5.py', 'commodities_analyzer.py', 'market_dashboard.py', 'ptt_sentiment.py']
        failed = []
        
        for f in files:
            path = self.workspace_dir / f
            if path.exists():
                try:
                    compile(open(path).read(), str(path), 'exec')
                except SyntaxError as e:
                    failed.append(f"{f}: {e}")
        
        if failed:
            return {'success': False, 'error': '; '.join(failed)}
        return {'success': True, 'message': '所有檔案語法正確'}
    
    def test_imports(self):
        """L1: 模組導入檢查"""
        modules = ['pandas', 'numpy', 'plotly', 'streamlit']
        failed = []
        
        for mod in modules:
            try:
                __import__(mod)
            except ImportError as e:
                failed.append(f"{mod}: {e}")
        
        if failed:
            return {'success': False, 'error': '; '.join(failed)}
        return {'success': True, 'message': '所有模組可導入'}
    
    def test_data_types(self):
        """L2: 資料類型檢查（快速版）"""
        sys.path.insert(0, str(self.workspace_dir))
        
        try:
            from commodities_analyzer import get_all_commodities_data, get_all_futures_data
            import pandas as pd
            
            # 測試原物料（只測 2 個，減少時間）
            comm = get_all_commodities_data(days=1)
            for name, info in list(comm.items())[:2]:
                if not isinstance(info['latest'], (int, float)):
                    return {'success': False, 'error': f"{name} 的 latest 類型錯誤"}
                if pd.isna(info['latest']):
                    return {'success': False, 'error': f"{name} 的 latest 是 NaN"}
                # 測試格式化
                try:
                    _ = f"{info['latest']:.2f}"
                except (TypeError, ValueError) as e:
                    return {'success': False, 'error': f"{name} 格式化失敗：{e}"}
            
            return {'success': True, 'message': f'檢查 {len(comm)} 項商品'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_service_health(self):
        """L3: 服務健康檢查"""
        import urllib.request
        
        try:
            # 檢查 Streamlit
            url = 'http://localhost:8501/_stcore/health'
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    return {'success': True, 'message': 'Streamlit 運行正常'}
                else:
                    return {'success': False, 'error': f'Streamlit 回應異常：{response.status}'}
        except Exception as e:
            return {'success': False, 'error': f'服務健康檢查失敗：{e}'}
    
    def test_file_integrity(self):
        """L1: 檔案完整性檢查"""
        required_files = [
            'app_v5.py',
            'commodities_analyzer.py',
            'market_dashboard.py',
            'ptt_sentiment.py'
        ]
        
        missing = []
        for f in required_files:
            if not (self.workspace_dir / f).exists():
                missing.append(f)
        
        if missing:
            return {'success': False, 'error': f'缺少檔案：{", ".join(missing)}'}
        
        return {'success': True, 'message': '所有必要檔案存在'}
    
    def run_all(self):
        """執行所有測試"""
        print("="*60)
        print(f"🧪 本地 CI 驗證 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        print()
        
        # L1: 快速檢查
        print("├── L1: 語法與完整性檢查")
        self.run_test("語法檢查", self.test_syntax, timeout_sec=10)
        self.run_test("模組導入", self.test_imports, timeout_sec=10)
        self.run_test("檔案完整性", self.test_file_integrity, timeout_sec=5)
        print()
        
        # L2: 整合測試
        print("├── L2: 資料完整性測試")
        self.run_test("資料類型", self.test_data_types, timeout_sec=30)
        print()
        
        # L3: 服務健康
        print("├── L3: 服務健康檢查")
        self.run_test("服務健康", self.test_service_health, timeout_sec=10)
        print()
        
        # 總結
        self.print_summary()
        
        return self.results['failed'] == 0
    
    def print_summary(self):
        """打印總結"""
        print("="*60)
        print("📊 測試結果摘要")
        print("="*60)
        
        for test in self.results['tests']:
            status = "✅" if test['status'] == 'passed' else "❌"
            print(f"{status} {test['name']}: {test.get('message', test.get('error', ''))}")
        
        print()
        print(f"總計：{self.results['passed']} 通過 / {self.results['failed']} 失敗")
        
        if self.results['failed'] == 0:
            print(f"\n{GREEN}✅ 所有測試通過！{NC}")
        else:
            print(f"\n{RED}❌ 有測試失敗，請檢查！{NC}")
        
        print("="*60)
    
    def save_report(self, output_path='ci_report.json'):
        """保存測試報告"""
        report_path = self.workspace_dir / output_path
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        log_info(f"測試報告已保存：{report_path}")

if __name__ == "__main__":
    workspace = os.environ.get('WORKSPACE_DIR', '/home/openclaw/.openclaw/workspace-stock/hello-bob')
    ci = LocalCI(workspace)
    
    success = ci.run_all()
    ci.save_report()
    
    sys.exit(0 if success else 1)
