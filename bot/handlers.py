import asyncio
import datetime
from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandObject, BaseFilter
from aiogram.types import Message, CallbackQuery
import config
from storage.db import Database
from storage.models import Opportunity
from scanner.engine import ScannerEngine
from scanner.reply_generator import generate_reply
from bot.keyboards import (
    get_main_menu_keyboard,
    get_opportunity_keyboard,
    get_settings_keyboard,
    get_reply_style_keyboard,
    get_sources_keyboard,
    get_keywords_menu_keyboard
)
from bot.messages import (
    get_start_message,
    get_help_message,
    format_opportunity_message,
    format_status_message,
    format_details_message
)
from utils.logger import get_logger

logger = get_logger("bot_handlers")
router = Router()

# 1. Admin Filters for Security
class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if config.TELEGRAM_USER_ID == 0:
            return True # Allow during setup/first run if config is empty
        return message.from_user.id == config.TELEGRAM_USER_ID

class IsAdminCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        if config.TELEGRAM_USER_ID == 0:
            return True
        return callback.from_user.id == config.TELEGRAM_USER_ID

# Inject database and engine references
db_inst: Database = None
engine_inst: ScannerEngine = None

def init_handlers(database: Database, engine: ScannerEngine):
    global db_inst, engine_inst
    db_inst = database
    engine_inst = engine

# 2. START & HELP
@router.message(Command("start"), IsAdmin())
async def cmd_start(message: Message):
    await db_inst.init_db()  # Ensure DB is populated
    await message.answer(
        text=get_start_message(),
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("help"), IsAdmin())
@router.message(F.text == "❓ Help", IsAdmin())
async def cmd_help(message: Message):
    await message.answer(text=get_help_message(), parse_mode="HTML")

# 3. SCAN NOW
@router.message(Command("scan_now"), IsAdmin())
@router.message(Command("scan"), IsAdmin())
@router.message(F.text == "🔍 Scan Now", IsAdmin())
async def cmd_scan_now(message: Message):
    status_msg = await message.answer("🔄 Scanning all sources (Telegram, Kwork, Freelancehunt)...")
    try:
        new_opps = await engine_inst.scan_now()
        
        await message.bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
        
        if not new_opps:
            await message.answer(
                "✅ Scan done. No new leads passed the filters right now.\n"
                "If you expect Telegram leads, run /reset_scan first, then /scan again."
            )
            return
            
        await message.answer(f"📈 Found {len(new_opps)} new matching opportunities:")
        
        keywords = await db_inst.get_keywords()
        pos_kws = [k["keyword"] for k in keywords if k["is_negative"] == 0]
        neg_kws = [k["keyword"] for k in keywords if k["is_negative"] == 1]
        
        for opp in new_opps:
            text = format_opportunity_message(opp, pos_kws, neg_kws)
            kb = get_opportunity_keyboard(opp)
            await message.answer(
                text=text,
                reply_markup=kb,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            await db_inst.mark_notification_sent(opp.id)
            await asyncio.sleep(1.0)
            
    except Exception as e:
        logger.error(f"Error manually running scan: {e}")
        await message.answer(f"❌ Error occurred during scan: {e}")

# 3b. RESET REJECTED — сбросить rejected_by_ai обратно в new
@router.message(Command("reset_scan"), IsAdmin())
async def cmd_reset_scan(message: Message):
    await message.answer("♻️ Resetting all rejected posts back to 'new' for re-evaluation...")
    count = await db_inst.reset_rejected_opportunities()
    await message.answer(
        f"✅ Done! <b>{count}</b> rejected posts reset to 'new'.\n\n"
        f"Now use /scan to run a fresh scan — Telegram leads will be re-evaluated and sent.",
        parse_mode="HTML"
    )

# 3c. DEBUG — показывает состояние базы данных прямо в чате
@router.message(Command("debug"), IsAdmin())
async def cmd_debug(message: Message):
    import aiosqlite
    await message.answer("🔍 Checking database state on this server...")
    try:
        async with aiosqlite.connect(db_inst.db_path) as conn:
            conn.row_factory = aiosqlite.Row

            # By source + status
            cur = await conn.execute("""
                SELECT source, status, COUNT(*) as cnt
                FROM opportunities GROUP BY source, status ORDER BY source
            """)
            rows = await cur.fetchall()
            lines = ["<b>📊 DB State by source:</b>"]
            for r in rows:
                lines.append(f"  {r['source']} | {r['status']} | {r['cnt']}")

            # Sent notifications
            cur = await conn.execute("SELECT COUNT(*) FROM sent_notifications")
            sent_total = (await cur.fetchone())[0]
            lines.append(f"\n<b>📬 Total notifications sent:</b> {sent_total}")

            # min_score setting
            cur = await conn.execute("SELECT value FROM settings WHERE key='min_score_to_notify'")
            row = await cur.fetchone()
            min_score = row[0] if row else "?"
            lines.append(f"<b>🎯 min_score_to_notify:</b> {min_score}")

            # Keywords count
            cur = await conn.execute("SELECT COUNT(*) FROM keywords WHERE is_negative=0")
            pos = (await cur.fetchone())[0]
            cur = await conn.execute("SELECT COUNT(*) FROM keywords WHERE is_negative=1")
            neg = (await cur.fetchone())[0]
            lines.append(f"<b>🔑 Keywords:</b> {pos} positive / {neg} negative")

            await message.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Debug error: {e}")

# 4. TEST SCAN
@router.message(Command("test_scan"), IsAdmin())
async def cmd_test_scan(message: Message):
    await message.answer("🧪 Generating 5 fake opportunities to test UI notification layout...")
    
    # We will trigger the mock source adapter directly
    from sources.mock_source import MockSource
    mock = MockSource()
    raw_opps = await mock.fetch_opportunities()
    
    keywords = await db_inst.get_keywords()
    pos_kws = [k["keyword"] for k in keywords if k["is_negative"] == 0]
    neg_kws = [k["keyword"] for k in keywords if k["is_negative"] == 1]
    
    reply_style = await db_inst.get_setting("reply_style", "confident")
    profile_text = await db_inst.get_setting("profile_text", "")
    
    # Take 5 items
    test_items = raw_opps[:5]
    for i, opp in enumerate(test_items):
        # Force them to be HOT (0-15 mins old)
        opp.posted_at = datetime.datetime.now() - datetime.timedelta(minutes=3 * (i + 1))
        opp.first_detected_at = opp.posted_at
        opp.detected_at = datetime.datetime.now()
        
        from scanner.freshness import update_freshness
        from scanner.scoring import detect_category, estimate_difficulty, calculate_score
        
        update_freshness(opp)
        opp.category = detect_category(opp.title, opp.description)
        opp.difficulty = estimate_difficulty(opp.title, opp.description)
        opp.score, _ = calculate_score(opp, pos_kws, neg_kws)
        opp.suggested_reply = await generate_reply(opp, reply_style, profile_text)
        
        # Save to SQLite DB
        saved_opp = await db_inst.save_opportunity(opp)
        
        text = format_opportunity_message(saved_opp, pos_kws, neg_kws)
        kb = get_opportunity_keyboard(saved_opp)
        
        await message.answer(
            text=text,
            reply_markup=kb,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        await db_inst.mark_notification_sent(saved_opp.id)
        await asyncio.sleep(1.0)

# 5. STATUS
@router.message(Command("status"), IsAdmin())
@router.message(F.text == "📊 Status", IsAdmin())
async def cmd_status(message: Message):
    stats = await db_inst.get_stats()
    text = format_status_message(stats)
    await message.answer(text=text, parse_mode="HTML")

# 6. OPPORTUNITY VIEWS
@router.message(Command("latest"), IsAdmin())
@router.message(F.text == "📑 Latest", IsAdmin())
async def cmd_latest(message: Message):
    opps = await db_inst.get_latest_opportunities(limit=10)
    if not opps:
        await message.answer("No opportunities in the database yet. Try running /scan_now.")
        return
        
    for opp in opps:
        kb = get_opportunity_keyboard(opp)
        await message.answer(
            text=format_opportunity_message(opp),
            reply_markup=kb,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        await asyncio.sleep(0.5)

@router.message(Command("hot"), IsAdmin())
@router.message(F.text == "🔥 Hot Offers", IsAdmin())
async def cmd_hot(message: Message):
    opps = await db_inst.get_hot_opportunities(limit=10)
    if not opps:
        await message.answer("No HOT opportunities found (0-15 minutes old). Check back later!")
        return
        
    for opp in opps:
        kb = get_opportunity_keyboard(opp)
        await message.answer(
            text=format_opportunity_message(opp),
            reply_markup=kb,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        await asyncio.sleep(0.5)

@router.message(Command("portfolio"), IsAdmin())
@router.message(F.text == "💼 Portfolio", IsAdmin())
async def cmd_portfolio(message: Message):
    from bot.messages import get_portfolio_message
    await message.answer(text=get_portfolio_message(), parse_mode="HTML", disable_web_page_preview=True)

@router.message(Command("saved"), IsAdmin())
@router.message(F.text == "⭐ Saved", IsAdmin())
async def cmd_saved(message: Message):
    opps = await db_inst.get_saved_opportunities()
    if not opps:
        await message.answer("You haven't saved any opportunities yet. Star them using the inline buttons.")
        return
        
    await message.answer(f"⭐️ <b>Saved Opportunities ({len(opps)}):</b>", parse_mode="HTML")
    for opp in opps:
        kb = get_opportunity_keyboard(opp)
        await message.answer(
            text=format_opportunity_message(opp),
            reply_markup=kb,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        await asyncio.sleep(0.5)

@router.message(Command("applied"), IsAdmin())
@router.message(F.text == "✅ Applied", IsAdmin())
async def cmd_applied(message: Message):
    opps = await db_inst.get_applied_opportunities()
    if not opps:
        await message.answer("No opportunities marked as applied yet.")
        return
        
    await message.answer(f"✅ <b>Applied Opportunities ({len(opps)}):</b>", parse_mode="HTML")
    for opp in opps:
        kb = get_opportunity_keyboard(opp)
        await message.answer(
            text=format_opportunity_message(opp),
            reply_markup=kb,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        await asyncio.sleep(0.5)

# 7. SETTINGS COMMANDS
@router.message(Command("settings"), IsAdmin())
@router.message(F.text == "⚙️ Settings", IsAdmin())
async def cmd_settings(message: Message):
    await message.answer(
        "⚙️ <b>Control Center Settings</b>\nConfigure active scraper adapters, reply template styles, and freelancer parameters.",
        reply_markup=get_settings_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("keywords"), IsAdmin())
async def cmd_keywords(message: Message):
    kws = await db_inst.get_keywords()
    pos = [k["keyword"] for k in kws if k["is_negative"] == 0]
    neg = [k["keyword"] for k in kws if k["is_negative"] == 1]
    
    text = (
        f"📋 <b>Active Keywords Filters</b>\n\n"
        f"🟢 <b>High Priority ({len(pos)}):</b>\n"
        f"<code>{', '.join(pos)}</code>\n\n"
        f"🔴 <b>Negative / Skip ({len(neg)}):</b>\n"
        f"<code>{', '.join(neg)}</code>"
    )
    await message.answer(text=text, parse_mode="HTML")

@router.message(Command("add_keyword"), IsAdmin())
async def cmd_add_keyword(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("Usage: <code>/add_keyword keyword_text</code>\nFor negative keyword: <code>/add_keyword -keyword_text</code>", parse_mode="HTML")
        return
        
    arg = command.args.strip()
    is_neg = arg.startswith("-")
    kw = arg[1:].strip() if is_neg else arg
    
    success = await db_inst.add_keyword(kw, is_neg)
    if success:
        label = "Negative" if is_neg else "High-Priority"
        await message.answer(f"✅ Added {label} keyword: <code>{kw}</code>", parse_mode="HTML")
    else:
        await message.answer("❌ Failed to add keyword (already exists or DB error).")

@router.message(Command("remove_keyword"), IsAdmin())
async def cmd_remove_keyword(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("Usage: <code>/remove_keyword keyword_text</code>", parse_mode="HTML")
        return
        
    kw = command.args.strip()
    success = await db_inst.remove_keyword(kw)
    if success:
        await message.answer(f"✅ Removed keyword: <code>{kw}</code>", parse_mode="HTML")
    else:
        await message.answer(f"❌ Keyword <code>{kw}</code> not found in list.", parse_mode="HTML")

@router.message(Command("sources"), IsAdmin())
async def cmd_sources(message: Message):
    sources = await db_inst.get_sources()
    await message.answer("📡 <b>Source Adapters Configuration</b>", reply_markup=get_sources_keyboard(sources), parse_mode="HTML")

@router.message(Command("reply_style"), IsAdmin())
async def cmd_reply_style(message: Message, command: CommandObject):
    current = await db_inst.get_setting("reply_style", "confident")
    if not command.args:
        await message.answer(
            text=f"Current style: <b>{current}</b>\nChoose style using inline settings or: <code>/reply_style [confident/casual/short/premium/aggressive]</code>",
            reply_markup=get_reply_style_keyboard(current),
            parse_mode="HTML"
        )
        return
        
    new_style = command.args.strip().lower()
    valid = ["confident", "casual", "short", "premium", "aggressive but polite", "aggressive"]
    if new_style == "aggressive":
        new_style = "aggressive but polite"
        
    if new_style not in valid:
        await message.answer(f"Invalid style. Choose from: {', '.join(valid)}")
        return
        
    await db_inst.set_setting("reply_style", new_style)
    await message.answer(f"✅ Reply style updated to: <b>{new_style}</b>", parse_mode="HTML")

@router.message(Command("profile_text"), IsAdmin())
async def cmd_profile_text(message: Message, command: CommandObject):
    current = await db_inst.get_setting("profile_text", "")
    if not command.args:
        await message.answer(
            text=f"👤 <b>Your Freelancer Profile Text:</b>\n\n<code>{current}</code>\n\nTo update, run:\n<code>/profile_text I am an expert web developer specializing in...</code>",
            parse_mode="HTML"
        )
        return
        
    new_profile = command.args.strip()
    await db_inst.set_setting("profile_text", new_profile)
    await message.answer("✅ Freelancer profile text updated successfully.")

# 8. AI ASSISTANTS (Portfolio Ideas & Codex Prompts)
@router.message(Command("portfolio_ideas"), IsAdmin())
async def cmd_portfolio_ideas(message: Message, command: CommandObject):
    opp_id = None
    if command.args:
        try:
            opp_id = int(command.args.strip())
        except ValueError:
            pass
            
    if opp_id:
        opp = await db_inst.get_opportunity(opp_id)
    else:
        # Get latest opportunity
        opps = await db_inst.get_latest_opportunities(limit=1)
        opp = opps[0] if opps else None
        
    if not opp:
        await message.answer("No opportunities found to generate ideas for.")
        return
        
    ideas = {
        "Landing page": (
            "💡 <b>Portfolio Demo Idea:</b>\n"
            "Create a modern Gym/Fitness landing page using React and Tailwind. "
            "Implement a sleek dark mode theme with neon green highlights, an interactive membership pricing card, "
            "a booking form, and dynamic scroll animations (using Framer Motion or AOS)."
        ),
        "Website": (
            "💡 <b>Portfolio Demo Idea:</b>\n"
            "Build a premium Law Firm business website (multipage) using HTML, CSS (variables, grid/flexbox), and JS. "
            "Include a consultation appointment scheduler, testimonials slider, team slider, "
            "and an animated contact modal."
        ),
        "Telegram bot": (
            "💡 <b>Portfolio Demo Idea:</b>\n"
            "Create a clean Pizza Delivery bot in python using aiogram 3. "
            "Implement SQLite storage for the catalog. Include a Telegram WebApp shopping cart, "
            "custom InlineKeyboardMarkup keyboards, and automated invoice checkout features."
        ),
        "AI video": (
            "💡 <b>Portfolio Demo Idea:</b>\n"
            "Generate a professional AI UGC product video using HeyGen/Runway. "
            "Create a virtual presenter speaking with perfect lip-sync, write an engaging 30-second script for an e-commerce brand, "
            "add background music, and render in TikTok/Reels vertical layout with dynamic subtitles."
        ),
        "AI image": (
            "💡 <b>Portfolio Demo Idea:</b>\n"
            "Generate a series of concept art cars using Midjourney. "
            "Upscale and edit them in Photoshop, add typographic UI overlays, and package them as high-quality "
            "website banners representing futuristic transportation."
        ),
        "Automation": (
            "💡 <b>Portfolio Demo Idea:</b>\n"
            "Write a Python script using httpx and BeautifulSoup4 to scrape rental listings. "
            "Automate CSV generation, format coordinates, and integrate with a Google Sheets API "
            "to update data columns daily."
        ),
        "Content/SMM": (
            "💡 <b>Portfolio Demo Idea:</b>\n"
            "Write 5 high-quality tech blog posts about AI trends. "
            "Include generated matching marketing graphics, custom hashtags, and call-to-actions, "
            "tailored for LinkedIn and Telegram channels."
        ),
        "Other": (
            "💡 <b>Portfolio Demo Idea:</b>\n"
            "Develop a lightweight Python script that integrates an API to run cron checks and "
            "sends custom notifications via Email or Telegram Webhooks."
        )
    }
    
    text = (
        f"🎯 <b>Mock Project Idea for:</b> {opp.title}\n\n"
        f"{ideas.get(opp.category, ideas['Other'])}"
    )
    await message.answer(text=text, parse_mode="HTML")

@router.message(Command("generate_demo_prompt"), IsAdmin())
async def cmd_generate_demo_prompt(message: Message, command: CommandObject):
    opp_id = None
    if command.args:
        try:
            opp_id = int(command.args.strip())
        except ValueError:
            pass
            
    if opp_id:
        opp = await db_inst.get_opportunity(opp_id)
    else:
        opps = await db_inst.get_latest_opportunities(limit=1)
        opp = opps[0] if opps else None
        
    if not opp:
        await message.answer("No opportunities found to generate prompt for.")
        return
        
    desc_summary = opp.description.replace("\n", " ")[:200]
    prompt = (
        f"You are Codex / AntiGravity AI. Build a quick demo page representing this client's freelance request:\n"
        f"Title: {opp.title}\n"
        f"Needs: {desc_summary}...\n\n"
        f"Requirements:\n"
        f"- Write a single index.html file with beautiful embedded CSS and clean Javascript.\n"
        f"- Use a modern, responsive layout (grid/flex), premium dark mode aesthetics (glassmorphism/gradients), and Outfit/Inter fonts.\n"
        f"- Add simulated interactive widgets (e.g. calculator, simulator, API fetch preview) matching the requirements.\n"
        f"- Use high-quality placeholders for images from Unsplash."
    )
    
    await message.answer(
        text=f"🔑 <b>AntiGravity Demo Builder Prompt (Tap to Copy):</b>\n\n<code>{prompt}</code>",
        parse_mode="HTML"
    )

# 9. BUTTON CALLBACK HANDLERS
@router.callback_query(F.data.startswith("copy_"), IsAdminCallback())
async def handle_copy_reply(callback: CallbackQuery):
    opp_id = int(callback.data.split("_")[1])
    opp = await db_inst.get_opportunity(opp_id)
    
    if opp and opp.suggested_reply:
        # Send a separate copyable monospace message
        await callback.message.answer(
            text=f"📋 <b>Suggested Reply (Copyable):</b>\n\n<code>{opp.suggested_reply}</code>",
            parse_mode="HTML"
        )
        await callback.answer("Reply sent below!")
    else:
        await callback.answer("Suggested reply not found.", show_alert=True)

@router.callback_query(F.data.startswith("save_"), IsAdminCallback())
async def handle_save_opp(callback: CallbackQuery):
    opp_id = int(callback.data.split("_")[1])
    await db_inst.update_opportunity_status(opp_id, "saved")
    opp = await db_inst.get_opportunity(opp_id)
    
    # Refresh keyboard
    await callback.message.edit_reply_markup(reply_markup=get_opportunity_keyboard(opp))
    await callback.answer("⭐️ Opportunity saved!")

@router.callback_query(F.data.startswith("skip_"), IsAdminCallback())
async def handle_skip_opp(callback: CallbackQuery):
    opp_id = int(callback.data.split("_")[1])
    await db_inst.update_opportunity_status(opp_id, "skipped")
    opp = await db_inst.get_opportunity(opp_id)
    
    # Refresh keyboard
    await callback.message.edit_reply_markup(reply_markup=get_opportunity_keyboard(opp))
    await callback.answer("❌ Opportunity skipped.")

@router.callback_query(F.data.startswith("apply_"), IsAdminCallback())
async def handle_apply_opp(callback: CallbackQuery):
    opp_id = int(callback.data.split("_")[1])
    await db_inst.update_opportunity_status(opp_id, "applied")
    opp = await db_inst.get_opportunity(opp_id)
    
    # Refresh keyboard
    await callback.message.edit_reply_markup(reply_markup=get_opportunity_keyboard(opp))
    await callback.answer("✅ Marked as applied!")

@router.callback_query(F.data.startswith("regen_"), IsAdminCallback())
async def handle_regen_reply(callback: CallbackQuery):
    opp_id = int(callback.data.split("_")[1])
    opp = await db_inst.get_opportunity(opp_id)
    
    if not opp:
        await callback.answer("Opportunity not found.", show_alert=True)
        return
        
    style = await db_inst.get_setting("reply_style", "confident")
    profile = await db_inst.get_setting("profile_text", "")
    
    # We can rotate styles or regenerate with a prompt. Let's toggle style to create a fresh copy
    styles = ["confident", "casual", "short", "premium", "aggressive but polite"]
    current_idx = styles.index(style) if style in styles else 0
    next_style = styles[(current_idx + 1) % len(styles)]
    
    new_reply = await generate_reply(opp, next_style, profile)
    await db_inst.update_opportunity_reply(opp_id, new_reply)
    opp.suggested_reply = new_reply
    
    # Update the parent message text
    keywords = await db_inst.get_keywords()
    pos_kws = [k["keyword"] for k in keywords if k["is_negative"] == 0]
    neg_kws = [k["keyword"] for k in keywords if k["is_negative"] == 1]
    
    new_text = format_opportunity_message(opp, pos_kws, neg_kws)
    await callback.message.edit_text(text=new_text, reply_markup=get_opportunity_keyboard(opp), parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer(f"✍️ Regenerated reply using '{next_style}' style!")

@router.callback_query(F.data.startswith("details_"), IsAdminCallback())
async def handle_details_opp(callback: CallbackQuery):
    opp_id = int(callback.data.split("_")[1])
    opp = await db_inst.get_opportunity(opp_id)
    
    if opp:
        text = format_details_message(opp)
        await callback.message.answer(text=text, parse_mode="HTML", disable_web_page_preview=True)
        await callback.answer()
    else:
        await callback.answer("Details not found.", show_alert=True)

# 10. SETTINGS CALLBACK HANDLERS
@router.callback_query(F.data == "back_to_settings", IsAdminCallback())
async def handle_back_to_settings(callback: CallbackQuery):
    await callback.message.edit_text(
        text="⚙️ <b>Control Center Settings</b>\nConfigure active scraper adapters, reply template styles, and freelancer parameters.",
        reply_markup=get_settings_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "set_sources", IsAdminCallback())
async def handle_set_sources(callback: CallbackQuery):
    sources = await db_inst.get_sources()
    await callback.message.edit_text(
        text="📡 <b>Active Scrapers:</b>\nToggle individual source monitoring channels on and off.",
        reply_markup=get_sources_keyboard(sources),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_src_"), IsAdminCallback())
async def handle_toggle_source(callback: CallbackQuery):
    src_name = callback.data.replace("toggle_src_", "").strip()
    sources = await db_inst.get_sources()
    current_state = next((s["enabled"] for s in sources if s["name"] == src_name), 0)
    
    new_state = current_state == 0
    await db_inst.set_source_enabled(src_name, new_state)
    
    # Reload sources
    updated_sources = await db_inst.get_sources()
    await callback.message.edit_reply_markup(reply_markup=get_sources_keyboard(updated_sources))
    await callback.answer(f"Source {src_name.upper()} is now {'enabled' if new_state else 'disabled'}.")

@router.callback_query(F.data == "set_reply_style", IsAdminCallback())
async def handle_set_reply_style(callback: CallbackQuery):
    current = await db_inst.get_setting("reply_style", "confident")
    await callback.message.edit_text(
        text=f"✍️ <b>Choose suggested reply tone style:</b>",
        reply_markup=get_reply_style_keyboard(current),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("style_"), IsAdminCallback())
async def handle_change_style(callback: CallbackQuery):
    new_style = callback.data.replace("style_", "").strip()
    await db_inst.set_setting("reply_style", new_style)
    
    # Re-render keyboard
    await callback.message.edit_reply_markup(reply_markup=get_reply_style_keyboard(new_style))
    await callback.answer(f"Reply style updated to {new_style.upper()}!")

@router.callback_query(F.data == "set_profile", IsAdminCallback())
async def handle_set_profile(callback: CallbackQuery):
    current = await db_inst.get_setting("profile_text", "")
    await callback.message.answer(
        text=f"👤 <b>Your profile background details:</b>\n\n<code>{current}</code>\n\nTo change, send a message starting with <code>/profile_text [new details]</code>.",
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "set_keywords", IsAdminCallback())
async def handle_set_keywords_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        text="🔑 <b>Keywords filter settings:</b>\nManage interest keywords (high-priority) and negative skips.\nTo edit, run:\n• <code>/add_keyword word</code>\n• <code>/add_keyword -skipword</code>\n• <code>/remove_keyword word</code>",
        reply_markup=get_keywords_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "show_keywords_list", IsAdminCallback())
async def handle_show_kws_list(callback: CallbackQuery):
    kws = await db_inst.get_keywords()
    pos = [k["keyword"] for k in kws if k["is_negative"] == 0]
    neg = [k["keyword"] for k in kws if k["is_negative"] == 1]
    
    text = (
        f"📋 <b>Active Keywords Filters</b>\n\n"
        f"🟢 <b>High Priority ({len(pos)}):</b>\n"
        f"<code>{', '.join(pos)}</code>\n\n"
        f"🔴 <b>Negative / Skip ({len(neg)}):</b>\n"
        f"<code>{', '.join(neg)}</code>"
    )
    await callback.message.answer(text=text, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "set_rules", IsAdminCallback())
async def handle_set_rules(callback: CallbackQuery):
    min_score = await db_inst.get_setting("min_score_to_notify", "7")
    max_notif = await db_inst.get_setting("max_notifications_per_scan", "5")
    
    text = (
        f"📊 <b>Notification Rules</b>\n\n"
        f"• Minimum Score threshold: <b>{min_score}/10</b>\n"
        f"• Max notifications per scan: <b>{max_notif} items</b>\n\n"
        f"Settings can be configured directly inside your <code>.env</code> file configuration variables."
    )
    await callback.message.answer(text=text, parse_mode="HTML")
    await callback.answer()
