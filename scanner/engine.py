import datetime
import traceback
from storage.db import Database
from storage.models import Opportunity
from utils.logger import get_logger
from utils.time_utils import get_current_time
from scanner.freshness import update_freshness
from scanner.scoring import detect_category, estimate_difficulty, calculate_score
from scanner.reply_generator import generate_reply
from scanner.ai_filter import is_opportunity_relevant
import config

# Import sources dynamically or statically
from sources.mock_source import MockSource
from sources.telegram_source import TelegramSource
from sources.freelancehunt_source import FreelancehuntSource
from sources.kwork_source import KworkSource
from sources.flru_source import FLRuSource
from sources.reddit_source import RedditSource

logger = get_logger("scanner_engine")

class ScannerEngine:
    def __init__(self, db: Database):
        self.db = db
        # Mapping names to classes
        self.source_classes = {
            "mock": MockSource,
            "telegram": TelegramSource,
            "freelancehunt": FreelancehuntSource,
            "kwork": KworkSource,
            "flru": FLRuSource,
            "reddit": RedditSource
        }

    async def scan_now(self) -> list[Opportunity]:
        """
        Runs the full scan cycle:
        1. Fetch enabled sources
        2. Deduplicate, calculate freshness, score
        3. Generate replies
        4. Save to DB
        5. Return list of new high-scoring (score >= min_score) opportunities
        """
        logger.info("Starting new scan cycle...")
        
        # 1. Fetch enabled sources from DB
        sources_list = await self.db.get_sources()
        enabled_sources = [s["name"] for s in sources_list if s["enabled"] == 1]
        
        if not enabled_sources:
            logger.warning("No scraping sources are enabled. Skipping scan.")
            return []
            
        logger.info(f"Enabled sources to scan: {enabled_sources}")
        
        # 2. Gather all listings from enabled sources (handle errors gracefully per source)
        raw_opportunities = []
        for src_name in enabled_sources:
            if src_name not in self.source_classes:
                logger.warning(f"Source adapter '{src_name}' not found. Skipping.")
                continue
                
            try:
                adapter = self.source_classes[src_name]()
                logger.info(f"Running source: {src_name}")
                items = await adapter.fetch_opportunities()
                raw_opportunities.extend(items)
                # Update last scan time in DB
                await self.db.update_source_scan_time(src_name)
            except Exception as e:
                logger.error(f"Error executing source adapter '{src_name}': {e}")
                logger.error(traceback.format_exc())
                # Continue scanning other sources
                continue

        logger.info(f"Total raw opportunities scraped: {len(raw_opportunities)}")
        
        # 3. Fetch current keywords & settings for scoring and reply generation
        keywords = await self.db.get_keywords()
        pos_kws = [k["keyword"] for k in keywords if k["is_negative"] == 0]
        neg_kws = [k["keyword"] for k in keywords if k["is_negative"] == 1]
        
        reply_style = await self.db.get_setting("reply_style", "confident")
        profile_text = await self.db.get_setting("profile_text", "")
        min_score = int(await self.db.get_setting("min_score_to_notify", "7"))
        max_notifications = int(await self.db.get_setting("max_notifications_per_scan", "5"))
        
        qualified_opportunities = []
        current_time = get_current_time()
        
        # 4. Process each opportunity
        for opp in raw_opportunities:
            # Check for duplicate in DB
            existing = await self.db.get_opportunity_by_hash(opp.hash_id)
            
            if existing:
                # Restore fields from DB record
                opp.first_detected_at = existing.first_detected_at
                opp.detected_at = existing.detected_at
                opp.id = existing.id
                opp.status = existing.status
                opp.category = existing.category or detect_category(opp.title, opp.description)
                opp.difficulty = existing.difficulty or estimate_difficulty(opp.title, opp.description)
                update_freshness(opp)

                # Always recalculate score (fixes cases where score was saved as 0 due to earlier bug)
                score, _ = calculate_score(opp, pos_kws, neg_kws)
                opp.score = score

                # Update in DB with fresh score + freshness
                await self.db.save_opportunity(opp)

                # If we've already notified or processed this, skip notification
                if existing.status != "new" or await self.db.is_notification_sent(existing.id):
                    continue
            else:
                # New listing detected!
                opp.first_detected_at = current_time
                opp.detected_at = current_time
                update_freshness(opp)
                
                # Categorization & difficulty estimation
                opp.category = detect_category(opp.title, opp.description)
                opp.difficulty = estimate_difficulty(opp.title, opp.description)
                
                # Lead scoring
                score, reasons = calculate_score(opp, pos_kws, neg_kws)
                opp.score = score
                
                # Save to database to generate an autoincrement ID
                saved_opp = await self.db.save_opportunity(opp)
                opp.id = saved_opp.id
                
            # 5. Filter for notifications
            # Rules:
            # - Status must be 'new'
            # - Score must be >= min_score
            # - Must not have been notified before
            # NOTE: We intentionally DO NOT filter by freshness_bucket here.
            # Telegram posts can be hours old by the time the bot first sees them,
            # and filtering by HOT/FRESH was silently dropping 99% of Telegram leads.
            # The deduplication (is_notification_sent) prevents us from spamming the same post twice.
            is_sent = await self.db.is_notification_sent(opp.id)
            if (
                opp.status == "new" and 
                opp.score >= min_score and 
                not is_sent
            ):
                # Final check: AI Filter
                # Wait 12s between calls to stay within Gemini free tier (5 req/min)
                await asyncio.sleep(12)
                is_relevant = await is_opportunity_relevant(opp.title, opp.description, config.GEMINI_API_KEY)
                if is_relevant:
                    # Generate suggested reply ONLY for relevant and high-score items
                    opp.suggested_reply = await generate_reply(opp, reply_style, profile_text)
                    await self.db.save_opportunity(opp)
                    qualified_opportunities.append(opp)
                else:
                    # Update status to rejected so we don't scan it again
                    opp.status = "rejected_by_ai"
                    await self.db.save_opportunity(opp)
                
        # Sort qualified items by score descending, then by age (newest first)
        qualified_opportunities.sort(key=lambda x: (x.score, -x.age_minutes), reverse=True)
        
        # Cap notifications to max limit
        final_notifications = qualified_opportunities[:max_notifications]
        logger.info(f"Qualified opportunities matching notify rules: {len(qualified_opportunities)}. Notifying about: {len(final_notifications)} (Cap: {max_notifications})")
        
        return final_notifications
