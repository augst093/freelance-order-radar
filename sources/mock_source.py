import datetime
import random
from sources.base import BaseSource
from storage.models import Opportunity
from utils.hashing import generate_opportunity_hash

class MockSource(BaseSource):
    name = "mock"

    async def fetch_opportunities(self) -> list[Opportunity]:
        self.logger.info("Generating mock freelance opportunities...")
        current_time = datetime.datetime.now()
        
        # A list of templates to generate realistic jobs
        templates = [
            # HOT & FRESH - Landing Page
            {
                "title": "Need a Landing Page for a Gym",
                "description": "Hi, I need a simple but elegant landing page for a local gym. It must have a hero section, testimonials, pricing plans, and a signup form. Please use HTML/CSS or React. Fast load time is important. No agency, freelancers only.",
                "url": "https://kwork.ru/projects/gym-landing-page",
                "client_name": "Alexander Fitness",
                "budget": "$150",
                "time_offset_min": 3,
                "category": "Landing page"
            },
            # HOT & FRESH - Telegram Bot
            {
                "title": "Create a Telegram Bot in Python",
                "description": "We need a python telegram bot for our delivery shop. The bot should show a product catalog, handle shopping cart, and send order notifications to our manager. Using aiogram 3 is highly preferred. SQLite for storing product items.",
                "url": "https://freelance.ru/projects/telegram-delivery-bot",
                "client_name": "PizzaGo",
                "budget": "$250",
                "time_offset_min": 7,
                "category": "Telegram bot"
            },
            # HOT & FRESH - AI Video
            {
                "title": "AI Video creator for TikTok and Reels",
                "description": "Looking for an expert to create 10 AI UGC videos for my e-commerce shop. You will need to generate AI videos of actors presenting a beauty product using tools like HeyGen, Runway or similar. Confident speaker avatar and good voice sync.",
                "url": "https://weblancer.net/projects/ai-video-reels",
                "client_name": "BeautyBrand",
                "budget": "$400",
                "time_offset_min": 12,
                "category": "AI video"
            },
            # HOT & FRESH - Automation
            {
                "title": "Python script for Google Sheets automation",
                "description": "I need a simple automation script written in Python to parse real estate listings from a public site and insert them daily into my Google Sheets spreadsheet. Should run on a cron job. Budget is tight, simple job.",
                "url": "https://freelancehunt.com/project/python-sheets-parser",
                "client_name": "John D.",
                "budget": "$80",
                "time_offset_min": 14,
                "category": "Automation"
            },
            # OK (30-60 mins old) - Website
            {
                "title": "Need a multi-page Business website",
                "description": "Looking for a web developer to build a business website for a law firm. 5 pages total (Home, Services, About, Blog, Contact). Must look professional and premium. HTML, CSS, JavaScript, responsive design. Contact form integrated.",
                "url": "https://kwork.ru/projects/law-firm-website",
                "client_name": "Justice Law Partners",
                "budget": "$600",
                "time_offset_min": 35,
                "category": "Website"
            },
            # OK - AI Image
            {
                "title": "Generate AI images of futuristic cars",
                "description": "Need 50 high-quality AI generated images of futuristic concept cars. You can use Midjourney, Stable Diffusion, or DALL-E. I need them in high resolution. Will use them for a website banner and social media.",
                "url": "https://freelancehunt.com/project/midjourney-car-images",
                "client_name": "FutureDrive LLC",
                "budget": "$100",
                "time_offset_min": 45,
                "category": "AI image"
            },
            # OLD (60-180 mins old) - Content / SMM
            {
                "title": "Create social media content for AI tech blog",
                "description": "Need content creator to write 15 short posts about AI tools and news. Create engaging copy and generate simple matching AI images. The content is for a Telegram tech channel.",
                "url": "https://kwork.ru/projects/smm-ai-blog",
                "client_name": "AI Trend Hunter",
                "budget": "$75",
                "time_offset_min": 90,
                "category": "Content/SMM"
            },
            # Negative keyword test - Full-time job (Should get low score / skipped)
            {
                "title": "Senior Python Full-time Developer in Munich",
                "description": "We are hiring a senior full-time Python backend developer for our office in Munich. Relocation assistance provided. Must have 5 years experience in Django and microservices. No freelance or remote contract.",
                "url": "https://reddit.com/r/freelance/senior-python-fulltime",
                "client_name": "Big Tech Corp",
                "budget": "$100k/year",
                "time_offset_min": 5,
                "category": "Website"
            },
            # Negative keyword test - Unpaid / Free (Should get low score / skipped)
            {
                "title": "Need a website built for free or za otzyv",
                "description": "Hi, I am starting a non-profit dog shelter and need a website built. I have no money, need free help. Can provide good feedback and rating in exchange (работа за отзыв, бесплатно, без оплаты).",
                "url": "https://fl.ru/projects/free-dog-shelter-site",
                "client_name": "Animal Lover",
                "budget": "None (free)",
                "time_offset_min": 10,
                "category": "Website"
            },
            # Dynamic pool for generating more realistic jobs (30 in total)
            {
                "title": "Сделать сайт-визитку для фотографа",
                "description": "Нужно сделать красивый и быстрый сайт-портфолио для фотографа. Слайдер с работами, отзывы, контакты. Желательно чистый HTML, CSS и JS для максимальной скорости. Нужен адаптивный дизайн.",
                "url": "https://freelance.ru/projects/photographer-portfolio",
                "client_name": "Дмитрий",
                "budget": "5000 руб",
                "time_offset_min": 8,
                "category": "Website"
            },
            {
                "title": "Telegram bot for tracking crypto prices",
                "description": "Need a simple python telegram bot that sends notifications when bitcoin price changes. Should fetch price from Binance public API. Database can be simple SQLite. Confident code.",
                "url": "https://weblancer.net/projects/crypto-price-bot",
                "client_name": "CryptoTrader",
                "budget": "$120",
                "time_offset_min": 18,
                "category": "Telegram bot"
            },
            {
                "title": "AI generated UGC product reviews",
                "description": "Looking for video creator who can generate AI UGC videos for an online shop. Use AI avatar tools or film yourself using capcut / AI features. Simple task, need 5 short videos.",
                "url": "https://kwork.ru/projects/ai-ugc-videos",
                "client_name": "ShopifySeller",
                "budget": "$150",
                "time_offset_min": 25,
                "category": "AI video"
            },
            {
                "title": "Сделать лендинг для продажи курса по AI",
                "description": "Требуется создать посадочную страницу под ключ (landing page) для онлайн-курса по нейросетям. Структура: первый экран, программа, спикеры, тарифы, форма заказа. Нужен современный дизайн, анимация при скролле.",
                "url": "https://fl.ru/projects/ai-course-landing",
                "client_name": "Елена",
                "budget": "15000 руб",
                "time_offset_min": 2,
                "category": "Landing page"
            },
            {
                "title": "Python script for parsing real estate site",
                "description": "Need a parser for a property site. The python script should extract title, price, location and phone numbers (if visible). Save results to CSV. Only clean code, async requests preferred.",
                "url": "https://freelancehunt.com/project/python-estate-parser",
                "client_name": "RealEstateAgent",
                "budget": "$90",
                "time_offset_min": 11,
                "category": "Automation"
            },
            {
                "title": "AI Generated Model Images for Fashion",
                "description": "We need an AI image specialist to generate 20 fashion model catalog photos wearing generic white shirts in outdoor locations. Please show portfolio of similar generation using Stable Diffusion / Midjourney.",
                "url": "https://kwork.ru/projects/sd-fashion-models",
                "client_name": "TrendWear",
                "budget": "$180",
                "time_offset_min": 22,
                "category": "AI image"
            },
            {
                "title": "Automated posting bot for Telegram channels",
                "description": "I need a telegram bot in python that will automatically fetch posts from reddit RSS feeds and post them to my telegram channel with formatting and source link. Simple setup.",
                "url": "https://kwork.ru/projects/tg-autoposting-bot",
                "client_name": "Admin101",
                "budget": "$100",
                "time_offset_min": 28,
                "category": "Telegram bot"
            },
            {
                "title": "Website frontend redesign - HTML/CSS/JS",
                "description": "We have an existing website and need the homepage redesigned to be modern and conversion-focused. You will receive Figma designs and need to write clean HTML, CSS and Javascript. Mobile responsiveness is critical.",
                "url": "https://freelancehunt.com/project/frontend-redesign-figma",
                "client_name": "SaaS Starter",
                "budget": "$350",
                "time_offset_min": 52,
                "category": "Website"
            },
            {
                "title": "Need 5 product presentation slides in AI",
                "description": "Create 5 beautiful slides explaining our AI product. Design should be futuristic, using custom generated AI images. Fast turnaround. urgent!",
                "url": "https://kwork.ru/projects/ai-slides-presentation",
                "client_name": "TechVentures",
                "budget": "$50",
                "time_offset_min": 5,
                "category": "Content/SMM"
            },
            {
                "title": "Crypto Scam / Casino Web builder - URGENT",
                "description": "Need a website clone for an online gambling casino slot machine. High budget but must be done quickly. No questions asked. (Should trigger negative keyword: casino/gambling)",
                "url": "https://fl.ru/projects/casino-clone",
                "client_name": "ShadowOp",
                "budget": "$3000",
                "time_offset_min": 1,
                "category": "Website"
            },
            {
                "title": "Simple portfolio website for illustrator",
                "description": "I need a website to show my drawings. Simple, minimalist design. A gallery grid that opens images in a modal, an about page, and contact info. HTML and CSS, easy to deploy.",
                "url": "https://weblancer.net/projects/artist-portfolio",
                "client_name": "Anna Art",
                "budget": "$120",
                "time_offset_min": 16,
                "category": "Website"
            }
        ]
        
        # Add another 10 variations to make sure we have 30+ items and randomize some of them
        for i in range(15):
            categories = ["Landing page", "Website", "Telegram bot", "AI video", "AI image", "Automation", "Content/SMM", "Other"]
            cat = random.choice(categories)
            title = f"Urgent: {cat} project needed"
            desc = f"Looking for a freelancer to assist with a {cat.lower()} task. We need this completed quickly. Technologies: Python, HTML, CSS, AI tools. Budget is negotiable, please message with your price and experience."
            
            templates.append({
                "title": title,
                "description": desc,
                "url": f"https://freelancehunt.com/project/random-job-{i}",
                "client_name": f"Client_{random.randint(100, 999)}",
                "budget": f"${random.randint(50, 500)}",
                "time_offset_min": random.randint(1, 150),
                "category": cat
            })

        opportunities = []
        for temp in templates:
            posted = current_time - datetime.timedelta(minutes=temp["time_offset_min"])
            hash_id = generate_opportunity_hash(temp["title"], self.name, temp["url"], temp["description"])
            
            opp = Opportunity(
                hash_id=hash_id,
                source=self.name,
                title=temp["title"],
                description=temp["description"],
                url=temp["url"],
                client_name=temp["client_name"],
                budget=temp["budget"],
                posted_at=posted,
                detected_at=current_time,
                first_detected_at=posted,
                category=temp["category"],
                status="new",
                raw_data_json=None
            )
            opportunities.append(opp)
            
        return opportunities
