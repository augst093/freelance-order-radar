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
            wantsListData = state.get('wantsListData', {})
            print(f"wantsListData is type {type(wantsListData)}")
            if isinstance(wantsListData, dict):
                print(list(wantsListData.keys())[:5])
                first_key = list(wantsListData.keys())[0]
                print(wantsListData[first_key])
            elif isinstance(wantsListData, list):
                print("It is a list!")
                print(wantsListData[0])
