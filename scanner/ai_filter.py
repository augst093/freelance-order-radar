import asyncio
import httpx
from utils.logger import get_logger

logger = get_logger("ai_filter")

async def is_opportunity_relevant(title: str, description: str, api_key: str) -> bool:
    """
    Uses Gemini to determine if an opportunity is highly relevant to a vibe coding freelancer.
    Returns True if relevant, False if it's junk, a resume, or irrelevant.
    """
    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
        logger.warning("Gemini API key is missing. AI filter disabled (returning False for safety).")
        return False # Fail closed if no AI key configured

    prompt = f"""
    You are an expert AI recruiter filtering freelance job boards.
    Your goal is to find web development, landing page, telegram bot, automation script, and AI integration gigs for a 'Vibe Coder' freelancer.

    Task: Analyze the following post and determine if it is a VALID freelance job offer that fits the criteria.
    Criteria for REJECTION (Return "NO"):
    - It is a resume/CV (someone looking for work, e.g., "Ищу работу", "Junior Developer looking for projects").
    - It is a full-time, office-based, or corporate employment offer (not freelance).
    - It is an irrelevant category (SMM, Marketing, Video Editing, Copywriting, HR, Sales, Call Center, Card Design, Gambling).
    - It is a complex enterprise project (Senior Java, C++, Kubernetes, DevOps, etc.).
    
    Criteria for ACCEPTANCE (Return "YES"):
    - It is a clear freelance project or part-time gig.
    - It involves creating/fixing a website, landing page, telegram bot, python script, MVP, frontend, etc.
    
    Post Title: {title}
    Post Description: {description}

    Output format: You MUST output ONLY the word "YES" or "NO". No other text or explanation.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 5
        }
    }
    
    max_retries = 5
    base_delay = 15.0  # Start with 15s delay to respect 5 req/min limit
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(url, json=payload)
                
            if r.status_code == 200:
                data = r.json()
                text = data['candidates'][0]['content']['parts'][0]['text'].strip().upper()
                if "YES" in text:
                    logger.info(f"AI Filter: ACCEPTED '{title}'")
                    return True
                else:
                    logger.info(f"AI Filter: REJECTED '{title}' (Reason: AI determined irrelevant)")
                    return False
            elif r.status_code == 429:
                logger.warning(f"AI Filter: Rate limited (429). Attempt {attempt + 1}/{max_retries}. Retrying in {base_delay}s...")
                await asyncio.sleep(base_delay)
                base_delay *= 2  # Exponential backoff
            else:
                logger.error(f"AI Filter error: Status {r.status_code} - {r.text}")
                # Fail-open: don't block lead on API errors
                return True
        except Exception as e:
            logger.error(f"AI Filter exception: {e}")
            # Fail-open: don't block lead on exceptions
            return True
            
    logger.warning("AI Filter: Rate limit exhausted after retries. Failing OPEN to not block leads.")
    return True  # Fail-open: better to send a lead than miss it
