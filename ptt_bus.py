import requests
from bs4 import BeautifulSoup
import time

def fetch_stock_posts(pages=3):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    base_url = 'https://www.ptt.cc'
    url = f'{base_url}/bbs/Stock/index.html'
    articles = []
    
    for _ in range(pages):
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')
            
            for d in soup.find_all('div', class_='r-ent'):
                a_tag = d.find('a')
                if a_tag:
                    articles.append({
                        'date': d.find('div', class_='date').text.strip(),
                        'push': d.find('div', class_='nrec').text.strip() or '0',
                        'title': a_tag.text,
                        'href': base_url + a_tag['href']
                    })
            
            prev_link = soup.find('div', class_='btn-group btn-group-paging').find_all('a')[1]['href']
            url = base_url + prev_link
            time.sleep(0.5)
        except Exception as e:
            print(f"Error fetching PTT: {e}")
            break
    return articles
