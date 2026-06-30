import asyncio
import os
from storage.db import Database
from scanner.engine import ScannerEngine
from utils.logger import get_logger

logger = get_logger("test")

async def run():
    db = Database("freelance_radar.db")
    await db.init_db()
    
    # Just mock it by querying DB for newest opportunities and recalculating their scores
    opps = await db.execute("SELECT id, hash_id, title, description, url, budget, freshness_bucket, status, score FROM opportunities ORDER BY id DESC LIMIT 500")
    
    print(f"Total in db: {len(opps)}")
    if not opps:
        return
        
    for opp in opps[:20]:
        print(f"SCORE: {opp['score']} | TITLE: {opp['title']} | STATUS: {opp['status']} | BUCKET: {opp['freshness_bucket']}")
        
if __name__ == "__main__":
    if __import__('sys').platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run())
