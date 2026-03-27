import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from infrastructure.external_api.ptt_bus import fetch_stock_posts

def main():
    print("🚀 啟動 PTT 股版情緒抓取...")
    posts = fetch_stock_posts(pages=2)
    for p in posts[:15]:
        print(f"[{p['date']}] {p['push']:>3}推 | {p['title']}")

if __name__ == "__main__":
    main()
