import asyncio
import os
import config
from storage.db import Database
from scanner.engine import ScannerEngine

async def main():
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    db = Database()
    await db.init_db()
    
    engine = ScannerEngine(db)
    res = await engine.scan_now()
    print('SCAN RESULT:', len(res))

if __name__ == '__main__':
    asyncio.run(main())
