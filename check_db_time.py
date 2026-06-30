import sqlite3
import datetime

conn = sqlite3.connect('freelance_radar.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute('SELECT title, score, first_detected_at, category FROM opportunities ORDER BY first_detected_at DESC LIMIT 20')
print(f"Current time: {datetime.datetime.now()}")
for r in c.fetchall():
    print(f"{r['title'][:60]} | Score: {r['score']} | Time: {r['first_detected_at']} | Cat: {r['category']}")
