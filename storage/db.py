import datetime
import json
import sqlite3
import aiosqlite
import config
from storage.models import Opportunity
from utils.logger import get_logger

logger = get_logger("db")

class Database:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Initializes database schema and populates default values if tables are empty."""
        logger.info(f"Initializing database at {self.db_path}")
        async with aiosqlite.connect(self.db_path) as db:
            # Create opportunities table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash_id TEXT UNIQUE,
                    source TEXT,
                    title TEXT,
                    description TEXT,
                    url TEXT,
                    client_name TEXT,
                    budget TEXT,
                    posted_at TEXT,
                    detected_at TEXT,
                    first_detected_at TEXT,
                    age_minutes INTEGER,
                    freshness_bucket TEXT,
                    category TEXT,
                    score INTEGER,
                    difficulty TEXT,
                    status TEXT,
                    suggested_reply TEXT,
                    raw_data_json TEXT
                )
            """)

            # Create sources table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    name TEXT PRIMARY KEY,
                    enabled INTEGER DEFAULT 1,
                    last_scanned_at TEXT
                )
            """)

            # Create keywords table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT UNIQUE,
                    is_negative INTEGER DEFAULT 0
                )
            """)

            # Create settings table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # Create sent_notifications table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sent_notifications (
                    opportunity_id INTEGER PRIMARY KEY,
                    sent_at TEXT
                )
            """)

            await db.commit()
            
            # Populate defaults if tables are empty
            await self._populate_defaults(db)

    async def _populate_defaults(self, db: aiosqlite.Connection):
        # Default sources
        cursor = await db.execute("SELECT COUNT(*) FROM sources")
        if (await cursor.fetchone())[0] == 0:
            logger.info("Populating default sources...")
            for src in config.DEFAULT_SOURCES:
                await db.execute(
                    "INSERT INTO sources (name, enabled) VALUES (?, ?)",
                    (src["name"], src["enabled"])
                )
            await db.commit()

        # Default keywords
        cursor = await db.execute("SELECT COUNT(*) FROM keywords")
        if (await cursor.fetchone())[0] == 0:
            logger.info("Populating default keywords...")
            for kw in config.DEFAULT_HIGH_PRIORITY_KEYWORDS:
                await db.execute(
                    "INSERT OR IGNORE INTO keywords (keyword, is_negative) VALUES (?, 0)",
                    (kw,)
                )
            for kw in config.DEFAULT_NEGATIVE_KEYWORDS:
                await db.execute(
                    "INSERT OR IGNORE INTO keywords (keyword, is_negative) VALUES (?, 1)",
                    (kw,)
                )
            await db.commit()

        # Default settings
        cursor = await db.execute("SELECT COUNT(*) FROM settings")
        if (await cursor.fetchone())[0] == 0:
            logger.info("Populating default settings...")
            defaults = {
                "reply_style": "confident",
                "profile_text": (
                    "I am a software engineer and AI content creator. I specialize in building landing pages, "
                    "business websites, Telegram bots, python scripts, integrations, and AI generation (video/images)."
                ),
                "scanning_active": "1"
            }
            for k, v in defaults.items():
                await db.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?)",
                    (k, v)
                )
            await db.commit()

    # OPPORTUNITIES CRUD
    async def get_opportunity_by_hash(self, hash_id: str) -> Opportunity | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM opportunities WHERE hash_id = ?", (hash_id,))
            row = await cursor.fetchone()
            if row:
                return self._row_to_opportunity(row)
        return None

    async def save_opportunity(self, opp: Opportunity) -> Opportunity:
        """Saves a new opportunity or updates an existing one."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Check if exists
            cursor = await db.execute("SELECT * FROM opportunities WHERE hash_id = ?", (opp.hash_id,))
            existing = await cursor.fetchone()
            
            posted_at_str = opp.posted_at.isoformat() if opp.posted_at else None
            detected_at_str = opp.detected_at.isoformat() if opp.detected_at else datetime.datetime.now().isoformat()
            
            if existing:
                # If first_detected_at isn't set, use existing or current
                first_detected = existing["first_detected_at"] or detected_at_str
                opp.first_detected_at = datetime.datetime.fromisoformat(first_detected) if first_detected else None
                opp.id = existing["id"]
                
                await db.execute("""
                    UPDATE opportunities SET 
                        title = ?, description = ?, url = ?, client_name = ?, budget = ?, 
                        posted_at = ?, age_minutes = ?, freshness_bucket = ?, category = ?, 
                        score = ?, difficulty = ?, status = ?, suggested_reply = ?, raw_data_json = ?
                    WHERE id = ?
                """, (
                    opp.title, opp.description, opp.url, opp.client_name, opp.budget,
                    posted_at_str, opp.age_minutes, opp.freshness_bucket, opp.category,
                    opp.score, opp.difficulty, opp.status, opp.suggested_reply, opp.raw_data_json,
                    opp.id
                ))
            else:
                first_detected_str = opp.first_detected_at.isoformat() if opp.first_detected_at else detected_at_str
                opp.first_detected_at = datetime.datetime.fromisoformat(first_detected_str)
                
                cursor = await db.execute("""
                    INSERT INTO opportunities (
                        hash_id, source, title, description, url, client_name, budget,
                        posted_at, detected_at, first_detected_at, age_minutes, freshness_bucket,
                        category, score, difficulty, status, suggested_reply, raw_data_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    opp.hash_id, opp.source, opp.title, opp.description, opp.url, opp.client_name, opp.budget,
                    posted_at_str, detected_at_str, first_detected_str, opp.age_minutes, opp.freshness_bucket,
                    opp.category, opp.score, opp.difficulty, opp.status, opp.suggested_reply, opp.raw_data_json
                ))
                opp.id = cursor.lastrowid
                
            await db.commit()
            return opp

    async def update_opportunity_status(self, opp_id: int, status: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE opportunities SET status = ? WHERE id = ?", (status, opp_id))
            await db.commit()

    async def update_opportunity_reply(self, opp_id: int, reply: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE opportunities SET suggested_reply = ? WHERE id = ?", (reply, opp_id))
            await db.commit()

    async def get_opportunity(self, opp_id: int) -> Opportunity | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,))
            row = await cursor.fetchone()
            if row:
                return self._row_to_opportunity(row)
        return None

    async def get_latest_opportunities(self, limit: int = 10, min_score: int = 0) -> list[Opportunity]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM opportunities WHERE score >= ? ORDER BY detected_at DESC LIMIT ?", 
                (min_score, limit)
            )
            rows = await cursor.fetchall()
            return [self._row_to_opportunity(row) for row in rows]

    async def get_hot_opportunities(self, limit: int = 20) -> list[Opportunity]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM opportunities WHERE freshness_bucket = 'HOT' ORDER BY detected_at DESC LIMIT ?", 
                (limit,)
            )
            rows = await cursor.fetchall()
            return [self._row_to_opportunity(row) for row in rows]

    async def get_saved_opportunities(self, limit: int = 30) -> list[Opportunity]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM opportunities WHERE status = 'saved' ORDER BY detected_at DESC LIMIT ?", 
                (limit,)
            )
            rows = await cursor.fetchall()
            return [self._row_to_opportunity(row) for row in rows]

    async def get_applied_opportunities(self, limit: int = 30) -> list[Opportunity]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM opportunities WHERE status = 'applied' ORDER BY detected_at DESC LIMIT ?", 
                (limit,)
            )
            rows = await cursor.fetchall()
            return [self._row_to_opportunity(row) for row in rows]

    def _row_to_opportunity(self, row: aiosqlite.Row) -> Opportunity:
        posted_at = datetime.datetime.fromisoformat(row["posted_at"]) if row["posted_at"] else None
        detected_at = datetime.datetime.fromisoformat(row["detected_at"]) if row["detected_at"] else datetime.datetime.now()
        first_detected_at = datetime.datetime.fromisoformat(row["first_detected_at"]) if row["first_detected_at"] else None
        
        return Opportunity(
            id=row["id"],
            hash_id=row["hash_id"],
            source=row["source"],
            title=row["title"],
            description=row["description"],
            url=row["url"],
            client_name=row["client_name"],
            budget=row["budget"],
            posted_at=posted_at,
            detected_at=detected_at,
            first_detected_at=first_detected_at,
            age_minutes=row["age_minutes"],
            freshness_bucket=row["freshness_bucket"],
            category=row["category"],
            score=row["score"],
            difficulty=row["difficulty"],
            status=row["status"],
            suggested_reply=row["suggested_reply"],
            raw_data_json=row["raw_data_json"]
        )

    # SETTINGS
    async def get_setting(self, key: str, default: str = "") -> str:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = await cursor.fetchone()
            if row:
                return row[0]
        return default

    async def set_setting(self, key: str, value: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
            await db.commit()

    # NOTIFICATIONS
    async def is_notification_sent(self, opp_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT 1 FROM sent_notifications WHERE opportunity_id = ?", (opp_id,))
            row = await cursor.fetchone()
            return row is not None

    async def mark_notification_sent(self, opp_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            sent_at = datetime.datetime.now().isoformat()
            await db.execute("INSERT OR IGNORE INTO sent_notifications (opportunity_id, sent_at) VALUES (?, ?)", (opp_id, sent_at))
            await db.commit()

    # SOURCES
    async def get_sources(self) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM sources")
            rows = await cursor.fetchall()
            return [{"name": r["name"], "enabled": r["enabled"], "last_scanned_at": r["last_scanned_at"]} for r in rows]

    async def set_source_enabled(self, name: str, enabled: bool):
        async with aiosqlite.connect(self.db_path) as db:
            val = 1 if enabled else 0
            await db.execute("UPDATE sources SET enabled = ? WHERE name = ?", (val, name))
            await db.commit()

    async def update_source_scan_time(self, name: str):
        async with aiosqlite.connect(self.db_path) as db:
            now_str = datetime.datetime.now().isoformat()
            await db.execute("UPDATE sources SET last_scanned_at = ? WHERE name = ?", (now_str, name))
            await db.commit()

    # KEYWORDS
    async def get_keywords(self) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM keywords ORDER BY is_negative, keyword")
            rows = await cursor.fetchall()
            return [{"id": r["id"], "keyword": r["keyword"], "is_negative": r["is_negative"]} for r in rows]

    async def add_keyword(self, keyword: str, is_negative: bool = False) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                neg_val = 1 if is_negative else 0
                await db.execute("INSERT OR IGNORE INTO keywords (keyword, is_negative) VALUES (?, ?)", (keyword.strip(), neg_val))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error adding keyword: {e}")
                return False

    async def remove_keyword(self, keyword: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM keywords WHERE keyword = ?", (keyword.strip(),))
            rowcount = cursor.rowcount
            await db.commit()
            return rowcount > 0

    # STATS
    async def get_stats(self) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Total opportunities
            cursor = await db.execute("SELECT COUNT(*) FROM opportunities")
            stats["total_opportunities"] = (await cursor.fetchone())[0]
            
            # New today
            today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            cursor = await db.execute("SELECT COUNT(*) FROM opportunities WHERE detected_at >= ?", (today_start,))
            stats["new_today"] = (await cursor.fetchone())[0]

            # Saved opportunities
            cursor = await db.execute("SELECT COUNT(*) FROM opportunities WHERE status = 'saved'")
            stats["saved"] = (await cursor.fetchone())[0]

            # Applied opportunities
            cursor = await db.execute("SELECT COUNT(*) FROM opportunities WHERE status = 'applied'")
            stats["applied"] = (await cursor.fetchone())[0]
            
            # Total sources
            cursor = await db.execute("SELECT COUNT(*) FROM sources WHERE enabled = 1")
            stats["active_sources"] = (await cursor.fetchone())[0]
            
            # Last scan time (maximum last_scanned_at)
            cursor = await db.execute("SELECT MAX(last_scanned_at) FROM sources")
            stats["last_scan_time"] = (await cursor.fetchone())[0]

            return stats

    async def reset_rejected_opportunities(self) -> int:
        """Resets all 'rejected_by_ai' opportunities back to 'new' so they get re-evaluated."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "UPDATE opportunities SET status = 'new' WHERE status = 'rejected_by_ai'"
            )
            await db.commit()
            return cursor.rowcount
