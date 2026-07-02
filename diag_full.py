import asyncio
import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from storage.db import Database
from scanner.engine import ScannerEngine
from aiogram import Bot

async def main():
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    db = Database()
    await db.init_db()
    engine = ScannerEngine(db)

    print("Running scan_now()...")
    results = await engine.scan_now()
    print(f"\n=== RESULT: {len(results)} opportunities passed ALL filters ===")

    if not results:
        print("Nothing passed. Checking DB stats...")
        recent = await db.get_latest_opportunities(limit=10, min_score=1)
        sources = {}
        for r in recent:
            sources[r.source] = sources.get(r.source, 0) + 1
        print(f"DB recent items by source: {sources}")
        return

    # Try sending first result
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    from bot.keyboards import get_opportunity_keyboard
    from bot.messages import format_opportunity_message

    keywords = await db.get_keywords()
    pos_kws = [k["keyword"] for k in keywords if k["is_negative"] == 0]
    neg_kws = [k["keyword"] for k in keywords if k["is_negative"] == 1]

    opp = results[0]
    text = format_opportunity_message(opp, pos_kws, neg_kws)
    kb = get_opportunity_keyboard(opp)
    try:
        await bot.send_message(
            chat_id=config.TELEGRAM_USER_ID,
            text=text,
            reply_markup=kb,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        await db.mark_notification_sent(opp.id)
        print(f"SENT TO TELEGRAM: {str(opp.title)[:60]}")
    except Exception as e:
        print(f"TELEGRAM SEND ERROR: {e}")
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
