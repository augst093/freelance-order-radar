import asyncio
import traceback
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from config import TELEGRAM_USER_ID, SCAN_INTERVAL_MINUTES
from storage.db import Database
from scanner.engine import ScannerEngine
from utils.logger import get_logger
from bot.keyboards import get_opportunity_keyboard
from bot.messages import format_opportunity_message

logger = get_logger("scheduler")

class ScanScheduler:
    def __init__(self, bot: Bot, db: Database, engine: ScannerEngine):
        self.bot = bot
        self.db = db
        self.engine = engine
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    def start(self):
        """Starts the background scanning scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running.")
            return

        interval = SCAN_INTERVAL_MINUTES
        logger.info(f"Starting scheduler with interval of {interval} minutes.")
        
        # Add interval job
        self.scheduler.add_job(
            self.run_scan_job,
            "interval",
            minutes=interval,
            id="scan_job",
            replace_existing=True
        )
        self.scheduler.start()
        self.is_running = True
        logger.info("Scheduler started successfully.")

    def stop(self):
        """Stops the background scheduler."""
        if not self.is_running:
            return
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Scheduler stopped.")

    async def run_scan_job(self):
        """Job triggered by APScheduler every N minutes."""
        logger.info("Scheduler triggered scan job...")
        
        # Double check if scanning is enabled in database settings
        active_str = await self.db.get_setting("scanning_active", "1")
        if active_str != "1":
            logger.info("Scanning is paused in settings. Skipping run.")
            return

        try:
            # Run scan
            new_opportunities = await self.engine.scan_now()
            
            if not new_opportunities:
                logger.info("No new matching opportunities found in this scan.")
                return

            logger.info(f"Sending notifications for {len(new_opportunities)} opportunities...")
            
            # Send notification for each qualified opportunity
            for opp in new_opportunities:
                if not TELEGRAM_USER_ID:
                    logger.warning("TELEGRAM_USER_ID is not configured. Cannot send notification.")
                    break
                    
                # Format notification message
                # We fetch positive keywords and negative keywords for reasons explanation
                keywords = await self.db.get_keywords()
                pos_kws = [k["keyword"] for k in keywords if k["is_negative"] == 0]
                neg_kws = [k["keyword"] for k in keywords if k["is_negative"] == 1]
                
                text = format_opportunity_message(opp, pos_kws, neg_kws)
                kb = get_opportunity_keyboard(opp)
                
                try:
                    await self.bot.send_message(
                        chat_id=TELEGRAM_USER_ID,
                        text=text,
                        reply_markup=kb,
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
                    # Mark notification as sent
                    await self.db.mark_notification_sent(opp.id)
                except Exception as e:
                    logger.error(f"Error sending message for opportunity {opp.id} to user {TELEGRAM_USER_ID}: {e}")
                
                # 1-second delay between telegram messages to prevent rate limits
                await asyncio.sleep(1.0)
                
        except Exception as e:
            logger.error(f"Error running scan job: {e}")
            logger.error(traceback.format_exc())
