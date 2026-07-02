import asyncio
import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from storage.db import Database
from sources.telegram_source import TelegramSource
from scanner.freshness import update_freshness
from scanner.scoring import calculate_score, detect_category, estimate_difficulty

async def main():
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    db = Database()
    await db.init_db()

    keywords = await db.get_keywords()
    pos_kws = [k["keyword"] for k in keywords if k["is_negative"] == 0]
    neg_kws = [k["keyword"] for k in keywords if k["is_negative"] == 1]
    min_score = int(await db.get_setting("min_score_to_notify", "7"))

    src = TelegramSource()
    raw = await src.fetch_opportunities()
    print(f"RAW: {len(raw)}")

    passed = []
    for opp in raw:
        update_freshness(opp)
        opp.category = detect_category(opp.title, opp.description)
        opp.difficulty = estimate_difficulty(opp.title, opp.description)
        score, reasons = calculate_score(opp, pos_kws, neg_kws)
        opp.score = score
        # NEW logic: no freshness filter
        if opp.score >= min_score:
            passed.append(opp)

    print(f"PASSED (score >= {min_score}): {len(passed)}")
    for p in passed[:10]:
        print(f"  score={p.score} | {p.title[:70]}")

if __name__ == "__main__":
    asyncio.run(main())
