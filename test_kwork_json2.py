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
            try:
                state = json.loads(state_str)
                wants = state.get('wants', {}).get('data', [])
                if not wants and 'wantsData' in state:
                    wants = state['wantsData']
                print(f"Parsed JSON! Found {len(wants)} wants")
                for w in wants[:3]:
                    print("-", w.get('name'), w.get('priceLimit'))
            except Exception as e:
                print("JSON parsing failed:", e)
        else:
            print("Could not find window.stateData inside the giant script.")
            # Let's see what window. variables are defined
            vars = re.findall(r'window\.([a-zA-Z0-9_]+)\s*=', s.string)
            print("Found variables:", set(vars))
            
            # Print the first 500 chars after window.stateData
            idx = s.string.find('window.stateData')
            if idx != -1:
                print("stateData found at index:", idx)
                print(s.string[idx:idx+500])
