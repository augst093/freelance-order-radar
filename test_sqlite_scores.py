import sqlite3
import json
import datetime
from storage.models import Opportunity
from scanner.scoring import calculate_score

def run():
    conn = sqlite3.connect("freelance_radar.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT keyword, is_negative FROM keywords")
    keywords = c.fetchall()
    pos_kws = [k["keyword"] for k in keywords if k["is_negative"] == 0]
    neg_kws = [k["keyword"] for k in keywords if k["is_negative"] == 1]
    
    c.execute("SELECT * FROM opportunities")
    opps = c.fetchall()
    
    match_count = 0
    for row in opps:
        d = dict(row)
        if d.get("posted_at"):
            try:
                d["posted_at"] = datetime.datetime.fromisoformat(d["posted_at"])
            except:
                d["posted_at"] = None
        if d.get("detected_at"):
            try:
                d["detected_at"] = datetime.datetime.fromisoformat(d["detected_at"])
            except:
                d["detected_at"] = None
        if d.get("first_detected_at"):
            try:
                d["first_detected_at"] = datetime.datetime.fromisoformat(d["first_detected_at"])
            except:
                d["first_detected_at"] = None
                
        o = Opportunity(**d)
        score, reasons = calculate_score(o, pos_kws, neg_kws)
        if score >= 7:
            match_count += 1
            print(f"[{score}] {o.title}")
            
    print(f"Total over threshold: {match_count} out of {len(opps)}")

if __name__ == "__main__":
    run()
