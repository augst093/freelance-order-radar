import sqlite3

conn = sqlite3.connect('freelance_radar.db')
c = conn.cursor()
c.execute("UPDATE opportunities SET status='skipped' WHERE status='new'")
conn.commit()
conn.close()
print("Cleaned up old messages.")
