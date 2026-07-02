"""
Full diagnostic: показывает почему Telegram лиды не доходят
"""
import asyncio, os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from storage.db import Database

async def main():
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    db = Database()
    await db.init_db()

    import aiosqlite
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row

        # Общая статистика по источникам
        cur = await conn.execute("""
            SELECT source, status, COUNT(*) as cnt
            FROM opportunities
            GROUP BY source, status
            ORDER BY source, status
        """)
        rows = await cur.fetchall()
        print("=== DB STATUS BY SOURCE ===")
        for r in rows:
            print(f"  source={r['source']} | status={r['status']} | count={r['cnt']}")

        # Сколько telegram постов с score >= 7 но rejected
        cur = await conn.execute("""
            SELECT COUNT(*) FROM opportunities 
            WHERE source='telegram' AND status='rejected_by_ai' AND score >= 7
        """)
        cnt = (await cur.fetchone())[0]
        print(f"\nTelegram posts: rejected_by_ai BUT score>=7: {cnt}")

        # Сколько telegram постов никогда не было уведомлено
        cur = await conn.execute("""
            SELECT COUNT(*) FROM opportunities 
            WHERE source='telegram' AND status='new'
        """)
        cnt2 = (await cur.fetchone())[0]
        print(f"Telegram posts: status=new (not yet processed): {cnt2}")

        cur = await conn.execute("""
            SELECT COUNT(*) FROM opportunities WHERE source='telegram'
        """)
        total = (await cur.fetchone())[0]
        print(f"Telegram posts: TOTAL in DB: {total}")

        # Сколько notification_sent для telegram
        cur = await conn.execute("""
            SELECT COUNT(*) FROM notifications_sent ns
            JOIN opportunities o ON ns.opportunity_id = o.id
            WHERE o.source = 'telegram'
        """)
        sent = (await cur.fetchone())[0]
        print(f"Telegram posts: notification_sent: {sent}")

if __name__ == "__main__":
    asyncio.run(main())
