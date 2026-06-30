import requests
import re
import json
from bs4 import BeautifulSoup

r = requests.get('https://kwork.ru/projects?c=11')
soup = BeautifulSoup(r.content, 'html.parser')

script = soup.find('script', string=re.compile('window\.State'))
if script:
    print("Found window.State script!")
    
scripts = soup.find_all('script')
for s in scripts:
    if s.string and ('wants' in s.string or 'project' in s.string or 'window.' in s.string):
        print("Script length:", len(s.string))
        print(s.string[:200])

