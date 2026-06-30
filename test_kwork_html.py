import requests
from bs4 import BeautifulSoup

r = requests.get('https://kwork.ru/projects?c=11')
soup = BeautifulSoup(r.content, 'html.parser')

print(f"Status: {r.status_code}")
items = soup.select('.project-item') or soup.select('.want-card') or soup.select('.project-card') or soup.select('.card')
print(f"Found {len(items)} items using generic selectors.")
if items:
    print(f"Class of first item: {items[0].get('class')}")

import re
matches = re.findall(r'class="([^"]*item[^"]*|[^"]*card[^"]*|[^"]*project[^"]*)"', r.text)
from collections import Counter
print(Counter(matches).most_common(10))
