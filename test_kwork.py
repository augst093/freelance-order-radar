import asyncio
from storage.db import Database
from sources.kwork_source import KworkSource
from utils.logger import setup_logger

setup_logger()

async def test_kwork():
    kwork = KworkSource()
    opps = await kwork.fetch_opportunities()
    print(f"Fetched {len(opps)} opportunities from Kwork")
    for opp in opps:
        print(f"- {opp.title} ({opp.budget})")

if __name__ == "__main__":
    if __import__('sys').platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_kwork())
