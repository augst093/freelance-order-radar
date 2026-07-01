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
from utils.time_utils import get_current_time

async def main():
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    db = Database()
    await db.init_db()

    keywords = await db.get_keywords()
    pos_kws = [k["keyword"] for k in keywords if k["is_negative"] == 0]
    neg_kws = [k["keyword"] for k in keywords if k["is_negative"] == 1]
    min_score = int(await db.get_setting("min_score_to_notify", "7"))

    print(f"\n=== DIAGNOSTIC: min_score={min_score}, pos_kws={len(pos_kws)}, neg_kws={len(neg_kws)} ===\n")

    src = TelegramSource()
    raw = await src.fetch_opportunities()
    print(f"TOTAL RAW from Telegram: {len(raw)}\n")

    stats = {"hot_fresh": 0, "old": 0, "no_keywords": 0, "neg_keywords": 0, "score_too_low": 0, "passed": 0}
    passed_examples = []
    failed_examples = []

    for opp in raw:
        update_freshness(opp)
        opp.category = detect_category(opp.title, opp.description)
        opp.difficulty = estimate_difficulty(opp.title, opp.description)
        score, reasons = calculate_score(opp, pos_kws, neg_kws)
        opp.score = score

        if opp.freshness_bucket not in ("HOT", "FRESH"):
            stats["old"] += 1
            continue

        text = f"{opp.title} {opp.description}".lower()
        has_pos = any(kw.lower() in text for kw in pos_kws)
        has_neg = any(kw.lower() in text for kw in neg_kws)

        if not has_pos:
            stats["no_keywords"] += 1
            if len(failed_examples) < 5:
                failed_examples.append(f"  [NO_KEYWORDS] Score={score} | {opp.title[:60]}")
            continue

        if has_neg:
            stats["neg_keywords"] += 1
            if len(failed_examples) < 5:
                failed_examples.append(f"  [NEG_KEYWORD] Score={score} | {opp.title[:60]}")
            continue

        stats["hot_fresh"] += 1
        if score < min_score:
            stats["score_too_low"] += 1
            if len(failed_examples) < 5:
                failed_examples.append(f"  [LOW_SCORE={score}] | {opp.title[:60]}")
            continue

        stats["passed"] += 1
        passed_examples.append(f"  [PASS score={score}] {opp.title[:60]}")

    print("=== FILTER FUNNEL ===")
    print(f"  Dropped (too old):        {stats['old']}")
    print(f"  Dropped (no keywords):    {stats['no_keywords']}")
    print(f"  Dropped (neg keywords):   {stats['neg_keywords']}")
    print(f"  HOT/FRESH total:          {stats['hot_fresh']}")
    print(f"  Dropped (score < {min_score}):      {stats['score_too_low']}")
    print(f"  PASSED ALL FILTERS:       {stats['passed']}")
    print()
    if passed_examples:
        print("=== PASSED ===")
        for e in passed_examples:
            print(e)
    else:
        print("=== NO POSTS PASSED ===")
        print("Failed examples:")
        for e in failed_examples:
            print(e)

if __name__ == "__main__":
    asyncio.run(main())
