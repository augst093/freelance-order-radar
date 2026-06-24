# Freelance Order Radar 🤖🛰️

A production-ready Telegram Bot designed to monitor freelance marketplaces, job boards, and public Telegram channels. It fetches fresh freelance project listings, scores them based on custom relevance filters, drafts personalized cover letters in multiple languages, and alerts you within 5–30 minutes of posting.

---

## Features
- **Real-Time Monitoring:** Scans active sources every 5 minutes using asynchronous adapters.
- **Dynamic Scoring (1–10):** Ranks leads based on age, category relevance, client urgency, and budget.
- **Negative Keyword Filters:** Automatically skips scams, full-time jobs, and unpaid listings.
- **AI Suggested Reply Generator:** Instantly drafts clean, context-specific cover letters customized for different tones (Casual, Confident, Premium, etc.).
- **Interactive Buttons:** Star, skip, open link, generate demo builder prompts, or mark listings as applied directly in Telegram.
- **SQLite Database:** Deduplicates posts using MD5 hashes to prevent duplicate notifications.
- **Zero Paid APIs by Default:** Built entirely with free, open-source utilities.

---

## Project Structure
```
freelance-order-radar/
  main.py                      # Bot bootstrapping and polling loop
  config.py                    # Environment loader and default profiles
  requirements.txt             # Required python packages
  .env.example                 # Dotenv template file
  freelance_radar.db           # SQLite database (auto-generated)
  bot/
    handlers.py                # Command and inline callback logic
    keyboards.py               # Main layout and button keyboards
    messages.py                # Message layouts and formatting templates
  scanner/
    engine.py                  # Core logic orchestrator
    scheduler.py               # APScheduler background scan timer
    scoring.py                 # lead scoring logic
    freshness.py               # Time calculation and age bucketing
    reply_generator.py         # Dynamic template text writer
  sources/
    base.py                    # Abstract base scraper interface
    mock_source.py             # Realistic offline mock listing generator
    telegram_source.py         # Web preview channel scraper
    freelancehunt_source.py    # Public RSS reader
    kwork_source.py            # Kwork adapter layout
    flru_source.py             # FL.ru RSS adapter layout
    reddit_source.py           # Reddit RSS adapter layout
  utils/
    hashing.py                 # Deduplication MD5 generator
    logger.py                  # Unified console/file logging
    text.py                    # HTML cleaning and keyword parsing
    time_utils.py              # Custom date and relative age parser
```

---

## Installation & Setup

### Prerequisites
- Python 3.11+ installed.
- Git (optional).

### 1. Clone or Copy files
Download the repository files to a local folder (e.g., `C:\freelance-order-radar`).

### 2. Install dependencies
Open Command Prompt or PowerShell in the project directory and run:
```bash
pip install -r requirements.txt
```

### 3. Create a Telegram Bot
1. Search for [@BotFather](https://t.me/BotFather) on Telegram and start a chat.
2. Send the `/newbot` command.
3. Follow the instructions to name your bot and choose a username.
4. Copy the generated **HTTP API Token** (e.g., `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).

### 4. Find your Telegram User ID
1. Search for [@userinfobot](https://t.me/userinfobot) or [@raw_data_bot](https://t.me/raw_data_bot) on Telegram.
2. Send `/start`.
3. Copy your numerical **User ID** (e.g. `987654321`).

### 5. Setup Configuration
Copy the template `.env.example` file and rename it to `.env`:
```bash
copy .env.example .env
```
Open `.env` in a text editor and fill in your details:
```ini
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_USER_ID=987654321
SCAN_INTERVAL_MINUTES=5
MIN_SCORE_TO_NOTIFY=7
MAX_NOTIFICATIONS_PER_SCAN=5
FRESHNESS_MAX_MINUTES=60
DATABASE_PATH=freelance_radar.db
```

---

## Running the Bot

Start the application by running:
```bash
python main.py
```
Upon start, the bot will initialize the SQLite database file (`freelance_radar.db`) with default keywords and configuration settings. If the `TELEGRAM_USER_ID` is set correctly, you will receive a startup message from the bot in Telegram.

---

## Commands & Operations

### Navigation Commands
- `/start` - Launch the bot and view the persistent layout menu.
- `/help` - View the list of all available command structures.
- `/status` - Check active scrape sources, last execution timestamps, and today's stats.
- `/scan_now` - Trigger an immediate scrape cycle across all enabled sources.
- `/test_scan` - Generate 5 fake opportunities to test bot notifications and keyboard buttons.

### Listing Views
- `/latest` - Show the 10 most recently parsed orders in the database.
- `/hot` - Display only HOT opportunities (less than 15 minutes old).
- `/saved` - List all opportunities you starred / marked as "Save".
- `/applied` - List all orders you flagged as "Applied".

### Settings & Filters
- `/settings` - Access the inline settings menu for easy configuration.
- `/keywords` - Show active Positive (interests) and Negative (skips) keywords.
- `/add_keyword <word>` - Add an interest keyword (e.g. `website`).
- `/add_keyword -<word>` - Add a skip keyword (e.g. `-unpaid` or `-agency`).
- `/remove_keyword <word>` - Remove an existing filter keyword.
- `/sources` - Toggle source scrapers on/off.
- `/reply_style` - Change the default cover letter tone (casual, confident, premium, etc.).
- `/profile_text` - View or update the background freelancer description used in cover letters.

### AI Assistants
- `/portfolio_ideas` - Generates a mock demo idea matching the latest opportunity.
- `/generate_demo_prompt` - Generates an AntiGravity/Codex prompt to code a quick HTML/CSS demo page matching the order details.

---

## Customizing Scraping Sources

To add a new custom adapter, create a new file in the `sources/` directory that inherits from `BaseSource`:

```python
from sources.base import BaseSource
from storage.models import Opportunity

class MyNewSource(BaseSource):
    name = "mynewsource"

    async def fetch_opportunities(self) -> list[Opportunity]:
        # Implement fetching logic here (RSS, scraping, etc.)
        # Return a list of Opportunity objects
        return []
```

Register your adapter class in the `sources_classes` dictionary inside `scanner/engine.py`:
```python
from sources.mynewsource import MyNewSource
# ...
self.source_classes = {
    # ...
    "mynewsource": MyNewSource
}
```

Add your source default configuration details to the list in `config.py`.

---

## Troubleshooting

1. **Bot not responding to my messages:**
   Make sure you set the `TELEGRAM_BOT_TOKEN` correctly in `.env` and that the token is active. Also verify that the `TELEGRAM_USER_ID` is matching your Telegram profile id.
2. **Missing sqlite3 DLL or binary error:**
   Python comes with native SQLite support. Ensure you are using a standard Python interpreter, not a minimal embedded version.
3. **Connection timeouts or 403 blocks:**
   Marketplaces like Kwork and FL.ru use Cloudflare protection. If they block standard requests, the bot will log a warning and skip them, maintaining active scanning for Telegram and RSS channels without crashing.
