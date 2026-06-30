import asyncio
import os
import config
from storage.db import Database
from scanner.reply_generator import generate_reply
from sources.mock_source import MockSource
import datetime

async def test_cmd():
    db = Database()
    await db.init_db()
    
    mock = MockSource()
    raw_opps = await mock.fetch_opportunities()
    opp = raw_opps[0]
    
    reply_style = await db.get_setting("reply_style", "confident")
    profile_text = await db.get_setting("profile_text", "")
    
    print("Testing generate_reply...")
    try:
        reply = await generate_reply(opp, reply_style, profile_text)
        print("REPLY GENERATED:", reply)
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_cmd())
