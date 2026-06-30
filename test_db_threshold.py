import asyncio
import os
from storage.db import Database
from scanner.engine import ScannerEngine
from utils.logger import get_logger
from scanner.scoring import calculate_score

async def run():
    db = Database("freelance_radar.db")
    await db.init_db()
    
    # Just mock it by querying DB for newest opportunities and recalculating their scores
    opps = await db.execute("SELECT * FROM opportunities ORDER BY id DESC")
    
    keywords = await db.get_keywords()
    pos_kws = [k["keyword"] for k in keywords if k["is_negative"] == 0]
    neg_kws = [k["keyword"] for k in keywords if k["is_negative"] == 1]
    
    match_count = 0
    from storage.models import Opportunity
    import datetime
    
    for row in opps:
        o = Opportunity(**row)
        score, reasons = calculate_score(o, pos_kws, neg_kws)
        if score >= 7:
            match_count += 1
            print(f"[{score}] {o.title} | {reasons}")
    
    print(f"Total over threshold: {match_count}")
        
if __name__ == "__main__":
    if __import__('sys').platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run())
