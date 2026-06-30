import sqlite3
from utils.text import count_keyword_matches

conn = sqlite3.connect('freelance_radar.db')
keywords = conn.execute("SELECT keyword FROM keywords WHERE is_negative=0").fetchall()
pos_kws = [k[0] for k in keywords]

text = "Менеджер по исходящим звонкам/оператор колл-центра (удаленно, B2B) от 55 000 ₽ ООО 'АКСЕЛЬ' • Без опыта"

matches_count = count_keyword_matches(text, pos_kws)
print(f"Matches count: {matches_count}")
for kw in pos_kws:
    if kw.lower() in text.lower():
        print(f"Matched directly: {kw}")
    else:
        import re
        kw_lower = kw.lower()
        if len(kw_lower) <= 3:
            pattern = r'\b' + re.escape(kw_lower) + r'\b'
            if re.search(pattern, text.lower()):
                print(f"Matched boundary: {kw}")

