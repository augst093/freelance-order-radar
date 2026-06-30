import requests
from bs4 import BeautifulSoup
import re

r = requests.get('https://kwork.ru/projects?c=11')
soup = BeautifulSoup(r.content.decode("utf-8"), 'html.parser')

items = soup.find_all('div')
classes = set()
for item in items:
    if item.get('class'):
        classes.update(item.get('class'))

for c in sorted(classes):
    if 'want' in c or 'project' in c or 'card' in c or 'item' in c:
        print(c)
