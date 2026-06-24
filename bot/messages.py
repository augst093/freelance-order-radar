import datetime
from storage.models import Opportunity
from utils.text import summarize_text, clean_html
from scanner.scoring import calculate_score

def format_opportunity_message(opp: Opportunity, pos_kws: list[str] = None, neg_kws: list[str] = None) -> str:
    """
    Formats the notification alert message.
    Outputs HTML-formatted text for Telegram.
    """
    # Recalculate scoring reason list if keywords are provided
    reasons_str = "• Matches your service filters"
    if pos_kws and neg_kws:
        _, reasons = calculate_score(opp, pos_kws, neg_kws)
        if reasons:
            reasons_str = "\n".join([f"• {r}" for r in reasons])
            
    # Freshness emoji
    freshness_emojis = {
        "HOT": "🔥 HOT",
        "FRESH": "⚡ FRESH",
        "OK": "🟢 OK",
        "OLD": "⏳ OLD",
        "TOO_OLD": "🔴 TOO OLD"
    }
    f_bucket = freshness_emojis.get(opp.freshness_bucket, opp.freshness_bucket)
    
    # Budget check
    budget_val = opp.budget if (opp.budget and opp.budget.strip() and "none" not in opp.budget.lower()) else "Not specified"
    
    # Client Needs summary
    summary = summarize_text(opp.description, 280)
    
    text = (
        f"🔥 <b>NEW FREELANCE ORDER</b>\n\n"
        f"<b>Title:</b> {opp.title}\n"
        f"<b>Source:</b> {opp.source.upper()}\n"
        f"<b>Age:</b> {opp.age_minutes} mins ago ({f_bucket})\n"
        f"<b>Category:</b> {opp.category}\n"
        f"<b>Score:</b> {opp.score}/10\n"
        f"<b>Difficulty:</b> {opp.difficulty}\n"
        f"<b>Budget:</b> {budget_val}\n\n"
        f"<b>Why it fits:</b>\n"
        f"<i>{reasons_str}</i>\n\n"
        f"<b>Client needs:</b>\n"
        f"{summary}\n\n"
        f"<b>Suggested reply (Tap to Copy):</b>\n"
        f"<code>{opp.suggested_reply}</code>\n\n"
        f"<b>Link:</b> {opp.url}"
    )
    return text

def format_status_message(stats: dict) -> str:
    """Formats the bot's system status report."""
    scan_active_label = "🟢 Active" if stats.get("active_sources", 0) > 0 else "🔴 Paused"
    
    # Format time
    last_scan = stats.get("last_scan_time")
    if last_scan:
        try:
            dt = datetime.datetime.fromisoformat(last_scan)
            last_scan_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            last_scan_str = last_scan
    else:
        last_scan_str = "Never"

    text = (
        f"📊 <b>Freelance Order Radar - System Status</b>\n\n"
        f"🤖 <b>Scanning status:</b> {scan_active_label}\n"
        f"📡 <b>Active sources:</b> {stats.get('active_sources', 0)}\n"
        f"🕒 <b>Last scan time:</b> {last_scan_str}\n\n"
        f"📈 <b>Stats for today:</b>\n"
        f"• New opportunities parsed: {stats.get('new_today', 0)}\n"
        f"• Total saved (starred): {stats.get('saved', 0)}\n"
        f"• Total marked as applied: {stats.get('applied', 0)}\n"
        f"• Total database listings: {stats.get('total_opportunities', 0)}"
    )
    return text

def format_details_message(opp: Opportunity) -> str:
    """Formats the extended details message."""
    budget_val = opp.budget if (opp.budget and opp.budget.strip() and "none" not in opp.budget.lower()) else "Not specified"
    posted_at_str = opp.posted_at.strftime("%Y-%m-%d %H:%M:%S") if opp.posted_at else "Not available"
    
    text = (
        f"📄 <b>Project Details: {opp.title}</b>\n\n"
        f"<b>Source:</b> {opp.source.upper()} | <b>Category:</b> {opp.category}\n"
        f"<b>Client:</b> {opp.client_name or 'Unknown'} | <b>Budget:</b> {budget_val}\n"
        f"<b>Posted at:</b> {posted_at_str}\n"
        f"<b>First detected:</b> {opp.first_detected_at.strftime('%H:%M:%S') if opp.first_detected_at else 'Unknown'}\n"
        f"<b>Age:</b> {opp.age_minutes} minutes ({opp.freshness_bucket})\n"
        f"<b>Score:</b> {opp.score}/10 | <b>Difficulty:</b> {opp.difficulty}\n"
        f"<b>Current status:</b> {opp.status.upper()}\n\n"
        f"<b>Full Description:</b>\n"
        f"<i>{opp.description}</i>\n\n"
        f"<b>Link:</b> {opp.url}"
    )
    return text

def get_start_message() -> str:
    """Returns the start introduction message."""
    text = (
        f"🚀 <b>Welcome to Freelance Order Radar!</b>\n\n"
        f"I monitor freelance marketplaces, job boards, and Telegram chats every 5 minutes to find "
        f"the newest orders matching your services.\n\n"
        f"<b>My core services:</b>\n"
        f"• Landing pages & business websites\n"
        f"• AI generation (video, images, text, UGC)\n"
        f"• Telegram bots & simple automations\n"
        f"• Python scripts & frontend projects\n\n"
        f"I score all jobs (1-10) and automatically generate cover letter templates. Use the buttons below "
        f"or type /help to see what I can do!"
    )
    return text

def get_help_message() -> str:
    """Returns the list of commands."""
    text = (
        f"❓ <b>Freelance Order Radar Commands</b>\n\n"
        f"<b>Main Commands:</b>\n"
        f"/start - Show intro and main keyboard menu\n"
        f"/status - View system state and scan metrics\n"
        f"/scan_now - Trigger an immediate scrape cycle\n"
        f"/test_scan - Generate 5 fake opportunities to test bot notifications\n"
        f"/help - Show this guide\n\n"
        f"<b>Opportunities & Filters:</b>\n"
        f"/latest - Show the last 10 parsed listings\n"
        f"/hot - Show only HOT listings (under 15 mins old)\n"
        f"/saved - Show all starred/saved opportunities\n"
        f"/applied - Show listings you applied to\n\n"
        f"<b>Settings:</b>\n"
        f"/settings - Configure sources, style, and profile text\n"
        f"/keywords - List positive and negative filters\n"
        f"/add_keyword <code>word</code> - Add positive interest filter\n"
        f"/remove_keyword <code>word</code> - Remove filter\n"
        f"/sources - Toggle scrapers (mock, telegram, freelancehunt, etc.)\n"
        f"/reply_style - Update style (casual, confident, premium, etc.)\n"
        f"/profile_text - View current freelancer background text\n\n"
        f"<b>AI Helpers:</b>\n"
        f"/portfolio - Show your vibe coding website portfolio links\n"
        f"/portfolio_ideas - Generate a mock project idea for a listing\n"
        f"/generate_demo_prompt - Generate a system prompt to code a quick demo website for a listing"
    )
    return text

def get_portfolio_message() -> str:
    """Returns the formatted list of Vibe Coding portfolio websites."""
    text = (
        f"💼 <b>My Vibe Coding Portfolio Websites</b>\n"
        f"Tap on any URL to open it, or tap on the code block to copy it for your replies!\n\n"
        
        f"1. 🛍️ <b>Swaggin</b> (Street Fashion / Clothing Shop):\n"
        f"🔗 <a href='https://swaggin-mu.vercel.app/'>swaggin-mu.vercel.app</a>\n"
        f"<code>https://swaggin-mu.vercel.app/</code>\n\n"
        
        f"2. ✒️ <b>Nocturne Ink</b> (Tattoo Studio / Art Agency):\n"
        f"🔗 <a href='https://nocturne-ink.vercel.app'>nocturne-ink.vercel.app</a>\n"
        f"<code>https://nocturne-ink.vercel.app</code>\n\n"
        
        f"3. 💅 <b>Muse Nail Atelier</b> (Manicure & Beauty Salon):\n"
        f"🔗 <a href='https://muse-nail-atelier.vercel.app/'>muse-nail-atelier.vercel.app</a>\n"
        f"<code>https://muse-nail-atelier.vercel.app/</code>\n\n"
        
        f"4. 🧘 <b>FlowState</b> (Productivity & Mental Focus App):\n"
        f"🔗 <a href='https://flowstate-delta-navy.vercel.app/'>flowstate-delta-navy.vercel.app</a>\n"
        f"<code>https://flowstate-delta-navy.vercel.app/</code>\n\n"
        
        f"5. 🛋️ <b>The Soft Edit</b> (Interior Design & lifestyle blog):\n"
        f"🔗 <a href='https://the-soft-edit-nine.vercel.app/'>the-soft-edit-nine.vercel.app</a>\n"
        f"<code>https://the-soft-edit-nine.vercel.app/</code>\n\n"
        
        f"6. 💳 <b>PulsePay</b> (Fintech App / Payment Platform Demo):\n"
        f"🔗 <a href='https://pulsepay-phi.vercel.app/'>pulsepay-phi.vercel.app</a>\n"
        f"<code>https://pulsepay-phi.vercel.app/</code>\n\n"
        
        f"7. 🧴 <b>Lumera Skin</b> (Skincare & Cosmetics Brand store):\n"
        f"🔗 <a href='https://lumera-skin-zeta.vercel.app/'>lumera-skin-zeta.vercel.app</a>\n"
        f"<code>https://lumera-skin-zeta.vercel.app/</code>\n\n"
        
        f"8. 🏋️ <b>Forge Method</b> (Fitness & Athletic Training Portal):\n"
        f"🔗 <a href='https://forge-method.vercel.app/'>forge-method.vercel.app</a>\n"
        f"<code>https://forge-method.vercel.app/</code>\n\n"
        
        f"9. 🏡 <b>Aurelia Estates</b> (Luxury Real Estate Portal):\n"
        f"🔗 <a href='https://aurelia-estates-two.vercel.app/'>aurelia-estates-two.vercel.app</a>\n"
        f"<code>https://aurelia-estates-two.vercel.app/</code>\n\n"
        
        f"10. 📈 <b>Elias Morgan Advisory</b> (Business & Financial Consulting):\n"
        f"🔗 <a href='https://elias-morgan-advisory.vercel.app/'>elias-morgan-advisory.vercel.app</a>\n"
        f"<code>https://elias-morgan-advisory.vercel.app/</code>"
    )
    return text
