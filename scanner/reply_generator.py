import re
from storage.models import Opportunity

def is_russian(text: str) -> bool:
    """Detects if the text contains Russian Cyrillic characters."""
    if not text:
        return False
    return bool(re.search(r'[а-яА-ЯёЁ]', text))

def generate_reply(opp: Opportunity, style: str = "confident", profile_text: str = "") -> str:
    """
    Generates a personalized, professional cover letter / message draft.
    Adapts to Russian or English based on the listing language.
    Strictly follows style constraints, under 800 characters, no spammy formatting.
    """
    use_ru = is_russian(f"{opp.title} {opp.description}")
    
    # 1. Clean up problem details from the title
    problem = opp.title
    # Remove prefixes like "Need a", "Looking for", "Требуется" to get clean problem nouns
    clean_problem = re.sub(r'^(need|looking for|required|create|build|develop|хочу|нужно|требуется|сделать|разработать)\s+', '', problem, flags=re.IGNORECASE)
    
    # 2. Setup category specific hooks & approaches
    category = opp.category
    
    if use_ru:
        # Russian responses
        next_questions = {
            "Landing page": "У вас уже готовы тексты и структура, или мне стоит сделать первый набросок прототипа?",
            "Website": "Есть ли у вас дизайн-макет в Figma, или мы начнем разработку с проектирования интерфейса?",
            "Telegram bot": "Подскажите, нужно ли интегрировать бота с какими-то внешними сервисами (CRM, Google Таблицы, платежные системы)?",
            "AI video": "Материалы для генерации видео предоставите вы, или мне полностью подготовить сценарий и креативы?",
            "AI image": "В каком стиле вы планируете генерацию и есть ли примеры картинок, которые вам нравятся?",
            "Automation": "Опишите, пожалуйста, логику процесса: какие исходные данные и куда их нужно переносить?",
            "Content/SMM": "Какая тематика проекта и есть ли у вас контент-план на ближайшее время?",
            "Other": "Расскажите подробнее о деталях задачи. Когда планируете начать?"
        }
        
        greetings = {
            "casual": "Привет!",
            "confident": "Здравствуйте!",
            "short": "Приветствую!",
            "premium": "Здравствуйте! Меня зовут разработчик-партнер.",
            "aggressive but polite": "Здравствуйте! Готов приступить к работе."
        }
        
        category_reasons = {
            "Landing page": "создании продающих посадочных страниц с фокусом на конверсию, быструю скорость загрузки и удобство для мобильных устройств.",
            "Website": "разработке современных адаптивных веб-сайтов на чистом коде (HTML/CSS/JS) или фреймворках, оптимизированных для SEO.",
            "Telegram bot": "разработке функциональных Telegram ботов на Python (используя aiogram 3). Создаю надежную архитектуру с базами данных.",
            "AI video": "создании качественных видеороликов с помощью ИИ (heygen, runway). Делаю монтаж, озвучку и реалистичную синхронизацию губ.",
            "AI image": "генерации реалистичных и концептуальных изображений через Midjourney и Stable Diffusion для бизнеса и блогов.",
            "Automation": "написании эффективных Python скриптов для парсинга данных, интеграции API и автоматизации рутины.",
            "Content/SMM": "создании вовлекающего контента с ИИ-генерацией картинок/видео для соцсетей и блогов.",
            "Other": "решении технических задач и автоматизации бизнес-процессов с использованием Python и веб-технологий."
        }

        # Structure drafts based on style
        if style == "short":
            msg = f"{greetings[style]} Могу помочь вам сделать {clean_problem.lower()}.\n\nСпециализируюсь на {category_reasons[category]}\n\n{next_questions[category]}"
        elif style == "casual":
            msg = f"{greetings[style]} Прочитал описание вашей задачи по разработке {clean_problem.lower()}. Могу с этим помочь.\n\nДелаю качественно, без лишней воды. {profile_text}\n\n{next_questions[category]} Давай обсудим детали?"
        elif style == "premium":
            msg = f"{greetings[style]} Ознакомился с вашим проектом: {opp.title}. Предлагаю свои услуги по разработке.\n\nМой подход — это создание премиальных решений с высокой скоростью загрузки и чистым кодом. Специализируюсь на {category_reasons[category]}\n\nСкажите, пожалуйста, {next_questions[category].lower()}"
        elif style == "aggressive but polite":
            msg = f"{greetings[style]} Готов взять ваш заказ «{opp.title}» в работу прямо сейчас. Опыт имеется.\n\nГарантирую соблюдение сроков и чистый код. {category_reasons[category].capitalize()}\n\nДавайте спишемся в чате? {next_questions[category]}"
        else: # confident (default)
            msg = f"{greetings['confident']} Я могу помочь вам реализовать {clean_problem.lower()}.\n\nУ меня есть опыт в этой сфере. Я специализируюсь на {category_reasons[category]} Сделаю всё адаптивно и быстро.\n\n{next_questions[category]}"
            
    else:
        # English responses
        next_questions = {
            "Landing page": "Do you already have the text/images/Figma, or should I create the first draft copy myself?",
            "Website": "Do you have a Figma design ready, or should we start with UI/UX prototyping?",
            "Telegram bot": "Do we need to integrate the bot with external services like a CRM, Google Sheets, or payment gateways?",
            "AI video": "Will you provide the scripts/voiceovers, or should I handle the scriptwriting and AI generations end-to-end?",
            "AI image": "What specific style are you aiming for, and do you have any reference images you like?",
            "Automation": "Could you share the manual steps you're doing right now so I can automate them accurately?",
            "Content/SMM": "What is the niche of your project, and how often do you plan to post?",
            "Other": "Could you share a bit more details about the core requirements? Let's discuss."
        }
        
        greetings = {
            "casual": "Hey there!",
            "confident": "Hi,",
            "short": "Hello,",
            "premium": "Hello,",
            "aggressive but polite": "Hi, I can help you with this right away."
        }
        
        category_reasons = {
            "Landing page": "building high-converting landing pages focused on fast loading times, clean code, and great mobile experiences.",
            "Website": "developing responsive, modern business websites using clean HTML/CSS/JS or frameworks, fully optimized for performance.",
            "Telegram bot": "building robust Telegram bots in Python using aiogram. I design clean DB schemas and secure integrations.",
            "AI video": "generating professional video content using AI avatars, realistic voice syncing, and high-fidelity video tools.",
            "AI image": "creating premium assets using Stable Diffusion and Midjourney, customized to match brand identity.",
            "Automation": "writing clean Python scripts for scraping public pages, automating workflows, and API connections.",
            "Content/SMM": "creating engaging copy paired with unique AI-generated graphics/videos for social channels.",
            "Other": "building custom automation scripts and web tools to solve specific technical challenges."
        }

        if style == "short":
            msg = f"{greetings[style]} I can help you with {clean_problem.lower()}.\n\nI specialize in {category_reasons[category]}\n\n{next_questions[category]}"
        elif style == "casual":
            msg = f"{greetings[style]} Saw your post about needing {clean_problem.lower()}. I can get this done for you.\n\nI focus on clean work and easy communication. {profile_text}\n\n{next_questions[category]} Let me know if you want to chat."
        elif style == "premium":
            msg = f"{greetings[style]} I reviewed your project details regarding {opp.title}. I would like to offer my services.\n\nI focus on premium custom development, providing fast performance and reliable code. I have extensive experience in {category_reasons[category]}\n\n{next_questions[category]}"
        elif style == "aggressive but polite":
            msg = f"{greetings[style]} I can start working on your {clean_problem.lower()} project immediately.\n\nI have completed similar projects successfully. My focus is on speed, clean code, and solid logic. {category_reasons[category].capitalize()}\n\nLet's get started. {next_questions[category]}"
        else: # confident (default)
            msg = f"{greetings['confident']} I can help you build this {clean_problem.lower()}.\n\nI specialize in {category_reasons[category]} I'll make sure it is clean, fast, and fully functional.\n\n{next_questions[category]}"

    # Cap message size to 800 characters
    if len(msg) > 780:
        msg = msg[:780] + "..."
        
    return msg
