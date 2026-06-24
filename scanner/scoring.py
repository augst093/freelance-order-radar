import re
from storage.models import Opportunity
from utils.text import contains_keyword, count_keyword_matches

def detect_category(title: str, description: str) -> str:
    """
    Classifies the project into one of the core categories:
    Landing page, Website, Telegram bot, AI video, AI image, Automation, Content/SMM, Other.
    """
    text = f"{title} {description}".lower()
    
    # Priority checks
    if contains_keyword(text, ["landing", "лендинг", "посадочная", "одностраничник", "product page"]):
        return "Landing page"
    elif contains_keyword(text, ["telegram bot", "телеграм бот", "тг бот", "tg bot", "бот"]):
        return "Telegram bot"
    elif contains_keyword(text, ["ai video", "heygen", "runway", "sora", "reels", "shorts", "tiktok", "ugc", "video generation", "генерация видео"]):
        return "AI video"
    elif contains_keyword(text, ["ai image", "midjourney", "stable diffusion", "dall-e", "dalle", "нейросеть рисует", "генерация изображений"]):
        return "AI image"
    elif contains_keyword(text, ["automation", "автоматизация", "script", "скрипт", "parser", "парсер", "scraping", "скрапинг"]):
        return "Automation"
    elif contains_keyword(text, ["smm", "content", "копирайт", "посты", "social media", "контент"]):
        return "Content/SMM"
    elif contains_keyword(text, ["website", "сайт", "web design", "html", "css", "js", "frontend", "верстка", "портфолио", "portfolio"]):
        return "Website"
        
    return "Other"

def estimate_difficulty(title: str, description: str) -> str:
    """
    Estimates project difficulty:
    - EASY: Can be done in 1-3 hours (scripts, clean-up, basic edits)
    - HARD: More than 1 day or complex (porting, large applications, teams)
    - MEDIUM: Standard website, typical bot (default)
    """
    text = f"{title} {description}".lower()
    
    easy_keywords = ["simple", "easy", "script", "minor", "fix", "простой", "скрипт", "правка", "небольшой", "быстро"]
    hard_keywords = ["complex", "senior", "system", "fullstack", "mobile app", "full-stack", "team", "сложный", "система", "крупный"]
    
    if contains_keyword(text, hard_keywords):
        return "HARD"
    elif contains_keyword(text, easy_keywords):
        return "EASY"
    return "MEDIUM"

def calculate_score(
    opp: Opportunity, 
    positive_keywords: list[str], 
    negative_keywords: list[str]
) -> tuple[int, list[str]]:
    """
    Scores an opportunity from 1 to 10.
    Returns the final score and a list of matched reasons why it fits/doesn't fit.
    """
    score = 5  # Base score
    reasons = []
    text = f"{opp.title} {opp.description}".lower()
    
    # 1. Freshness Score Modifiers
    if opp.freshness_bucket == "HOT":
        score += 3
        reasons.append("🔥 Hot off the press (0-15 min)")
    elif opp.freshness_bucket == "FRESH":
        score += 2
        reasons.append("⚡ Very fresh (15-30 min)")
    elif opp.freshness_bucket in ("OLD", "TOO_OLD"):
        score -= 2
        reasons.append("⏳ Listing is older than 60 minutes")
    
    # 2. Positive Keyword matching (Matches services)
    matches_count = count_keyword_matches(text, positive_keywords)
    if matches_count > 0:
        score += 2
        reasons.append(f"✅ Matches your services ({matches_count} keywords matched)")
        
    # 3. Simple / Easy task check
    diff = estimate_difficulty(opp.title, opp.description)
    if diff == "EASY":
        score += 2
        reasons.append("👌 Looks simple and fast to complete")
    elif diff == "HARD":
        score -= 1
        reasons.append("🧠 Complex project, may take time")
        
    # 4. Budget Mentioned
    if opp.budget and opp.budget.strip() and "none" not in opp.budget.lower():
        score += 1
        reasons.append(f"💰 Budget specified: {opp.budget}")
        
    # 5. Client urgency
    urgent_keywords = ["urgent", "fast", "asap", "срочно", "быстро", "сегодня"]
    if contains_keyword(text, urgent_keywords):
        score += 1
        reasons.append("🚨 Client indicates urgency")
        
    # 6. High demand categories
    if opp.category in ("Landing page", "Website", "Telegram bot", "AI video", "AI image"):
        score += 1
        reasons.append(f"🎯 Category: {opp.category}")
        
    # 7. Unpaid check
    unpaid_keywords = ["unpaid", "free", "бесплатно", "за отзыв", "без оплаты"]
    if contains_keyword(text, unpaid_keywords):
        score -= 3
        reasons.append("❌ Likely unpaid work or reviews-based")
        
    # 8. Full-time work checks
    ft_keywords = ["full-time", "senior", "office", "relocation", "штат", "офис"]
    if contains_keyword(text, ft_keywords):
        score -= 3
        reasons.append("💼 Looks like long-term full-time employment")
        
    # 9. Advanced experience / Video call check
    video_keywords = ["video call", "camera", "созвон", "камера", "zoom call", "meet"]
    if contains_keyword(text, video_keywords):
        score -= 2
        reasons.append("📹 Requires video call/camera verification")
        
    # 10. Negative keywords penalty
    neg_matches = count_keyword_matches(text, negative_keywords)
    if neg_matches > 0:
        score -= 6
        reasons.append(f"⚠️ Contains negative filters ({neg_matches} negative keywords matched)")
        
    # Clamp score to 1-10 range
    final_score = max(1, min(10, score))
    return final_score, reasons
