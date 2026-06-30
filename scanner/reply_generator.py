import os
import re
import httpx
from storage.models import Opportunity
from utils.logger import get_logger

logger = get_logger("reply_generator")

def is_russian(text: str) -> bool:
    """Detects if the text contains Russian Cyrillic characters."""
    if not text:
        return False
    return bool(re.search(r'[а-яА-ЯёЁ]', text))

async def generate_reply_via_gemini(opp: Opportunity, style: str, profile_text: str, api_key: str) -> str | None:
    """Queries Gemini 2.0 Flash to generate a custom context-aware cover letter asynchronously."""
    use_ru = is_russian(f"{opp.title} {opp.description}")
    language_instr = "Respond in Russian" if use_ru else "Respond in English"
    
    vibe_coding_context = """Я разработчик новой волны (Vibe Coder). Я не пишу код неделями, я использую ИИ (Cursor, Lovable, v0, Windsurf) чтобы собирать идеальные проекты (лендинги, боты, веб-приложения) за считанные часы. 
У меня огромная насмотренность, чистый код и фокус на бизнес-результат, а не на техническую духоту."""
    
    expertise = profile_text if profile_text and len(profile_text) > 20 else vibe_coding_context
    
    prompt = f"""
    You are an expert vibe coder / AI-assisted developer looking for freelance gigs.
    Your profile: {expertise}
    
    Write a short, punchy, human-like cover letter to this project:
    Title: {opp.title}
    Description: {opp.description}

    RULES:
    1. {language_instr}.
    2. Analyze the project description. If it's a website/landing, mention fast delivery with Next.js/React or Tilda/Webflow. If it's a bot, mention robust Python/aiogram architectures. If it's automation, mention clean Python scripts.
    3. DON'T BE ROBOTIC. Sound like a confident, modern developer. Do NOT use generic openings like "Здравствуйте, я могу помочь вам реализовать...".
    4. Start immediately with a hook related to their specific problem. Example: "Вижу, что нужен лендинг для юриста..." or "Могу собрать этого бота за пару дней...".
    5. Highlight that you use modern AI tools to deliver 10x faster and cleaner than standard developers.
    6. End with ONE specific, smart technical question about their project to start the dialogue.
    7. Tone: {style} (confident, sharp, no-bullshit).
    8. KEEP IT UNDER 600 CHARACTERS. Short and punchy wins.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1000
        }
    }
    
    max_retries = 3
    base_delay = 5.0
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(url, json=payload)
            if r.status_code == 200:
                data = r.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text.strip()
            elif r.status_code == 429:
                logger.warning(f"Reply generator: Rate limited (429). Attempt {attempt + 1}/{max_retries}. Retrying in {base_delay}s...")
                await asyncio.sleep(base_delay)
                base_delay *= 2
            else:
                logger.error(f"Reply generator Gemini error: {r.status_code} - {r.text}")
                break
        except Exception as e:
            logger.error(f"Reply generator exception: {e}")
            break
            
    return None

async def generate_reply(opp: Opportunity, style: str = "confident", profile_text: str = "") -> str:
    """
    Generates a personalized cover letter asynchronously.
    ONLY uses Gemini. No robotic templates allowed.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key and api_key != "YOUR_GEMINI_API_KEY_HERE":
        gemini_reply = await generate_reply_via_gemini(opp, style, profile_text, api_key)
        if gemini_reply:
            return gemini_reply

    # IF AI FAILS (e.g. rate limit), return a simple warning string instead of a dumb template.
    return "⚠️ ИИ не смог сгенерировать ответ из-за лимитов API. Напишите отклик самостоятельно."

