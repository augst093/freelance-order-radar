import requests
import re
import json
from bs4 import BeautifulSoup

r = requests.get('https://kwork.ru/projects?c=11')
soup = BeautifulSoup(r.content.decode('utf-8', 'ignore'), 'html.parser')

scripts = soup.find_all('script')
for s in scripts:
    if s.string and len(s.string) > 100000:
        match = re.search(r'window\.stateData\s*=\s*(.*?);window', s.string)
        if match:
            state_str = match.group(1)
            state = json.loads(state_str)
            wants = state.get('wantsListData', [])
            if not wants:
                wants = state.get('wants', [])
                if isinstance(wants, dict):
                    wants = wants.get('data', [])
            
            print(f"Found {len(wants)} wants")
            for w in wants[:3]:
                print(f"- {w.get('name')} | Budget: {w.get('priceLimit')}")
                print(f"  URL: https://kwork.ru/projects/{w.get('id')}/view")
                print(f"  Desc: {w.get('description', '')[:50]}...")
