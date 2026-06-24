import asyncio
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import config
from storage.db import Database
from scanner.engine import ScannerEngine
from scanner.scheduler import ScanScheduler
from bot.handlers import router, init_handlers
from utils.logger import get_logger

logger = get_logger("main")

async def main():
    logger.info("Initializing Freelance Order Radar...")
    
    # 1. Validation Checks
    if not config.TELEGRAM_BOT_TOKEN or config.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("TELEGRAM_BOT_TOKEN is not configured in .env! Please set it before running the bot.")
        sys.exit(1)
        
    if config.TELEGRAM_USER_ID == 0:
        logger.warning("TELEGRAM_USER_ID is set to 0. The bot will respond to all users initially. Set it in .env for security.")

    # 2. Storage & Database Setup
    db = Database(config.DATABASE_PATH)
    try:
        await db.init_db()
        logger.info("Database loaded and defaults verified.")
    except Exception as e:
        logger.critical(f"Failed to initialize SQLite Database: {e}")
        sys.exit(1)

    # 3. Engine Setup
    engine = ScannerEngine(db)

    # 4. Telegram Bot Initialization
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    # Using memory storage for Finite State Machine (if extended later)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Inject references into handlers
    init_handlers(db, engine)
    dp.include_router(router)

    # 5. Background Scheduler Setup
    scheduler = ScanScheduler(bot, db, engine)
    
    # Define Startup Hook
    async def on_startup():
        logger.info("Bot started polling...")
        scheduler.start()
        # Notify the admin on start if ID is set
        if config.TELEGRAM_USER_ID != 0:
            try:
                await bot.send_message(
                    chat_id=config.TELEGRAM_USER_ID,
                    text="🤖 <b>Freelance Order Radar is online!</b>\nBackground scan active. Use /help to list commands.",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Could not send startup notification to User ID {config.TELEGRAM_USER_ID}: {e}")

    # Define Shutdown Hook
    async def on_shutdown():
        logger.info("Shutting down Freelance Order Radar...")
        scheduler.stop()
        await bot.session.close()
        logger.info("Bot shutdown completed.")

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Define a small web health check server for Render free tier
    app = web.Application()
    async def handle_health(request):
        return web.json_response({"status": "ok"})
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check server started on port {port}")

    # 6. Run Polling
    try:
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Interrupted. Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error running bot: {e}")

if __name__ == "__main__":
    # Ensure correct event loop policy on Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process terminated by user.")
