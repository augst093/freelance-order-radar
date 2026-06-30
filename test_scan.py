import asyncio
import os
from storage.db import Database
from scanner.engine import ScannerEngine
from utils.logger import get_logger

logger = get_logger("test")

async def run():
    db = Database("freelance_radar.db")
    await db.init_db()
    engine = ScannerEngine(db)
    
    logger.info("Scanning...")
    opps = await engine.scan_now()
    logger.info(f"Scan finished. Found {len(opps)} opportunities to notify.")
    
    if not opps:
        print("No opportunities matched the threshold!")
        
    for o in opps:
        print(f"TITLE: {o.title}")
        print(f"SCORE: {o.score}")
        print(f"REPLY: {o.suggested_reply}")

if __name__ == "__main__":
    if __import__('sys').platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run())
