import datetime
import httpx
from bs4 import BeautifulSoup
from sources.base import BaseSource
from storage.models import Opportunity
from utils.hashing import generate_opportunity_hash
from utils.text import clean_html, summarize_text
from utils.time_utils import get_current_time

class TelegramSource(BaseSource):
    name = "telegram"

    # Default list of public telegram channel usernames to parse
    DEFAULT_CHANNELS = [
        # --- Оригинальные каналы ---
        "freelanceshop",
        "freelancehunt_projects",
        "workzilla_tasks",
        "zakazy_web",
        "tgwork",
        "theyseeku",
        "normrabota",
        "job4designer",
        "ishudesignera",
        "design_hunters",
        "mobiledevjobs",
        "Frilanser_100",
        "freelancers_pub",
        "itjob_freelance",
        "design_freelance",
        "rabota_designers",
        "pythonjobs_feed",
        "frontendjobs",
        "tlg_freelance",
        "it_freelancers",
        "web_dev_jobs",
        "copywriter_jobs",
        "smm_vacancies",
        "remote_job_it",
        "freelance_orders",
        "freelancedise",
        "freelance_rabota_rf",
        "it_vakansii_jobs",
        "devs_jobs",
        "frontend_job_offers",
        "backend_job_offers",
        # --- Новые каналы (добавлены пользователем) ---
        "mari_vakansii",
        "mari_vakansiii",
        "mirkreatorovjob",
        "ggfreelancechat",
        "proffreelancee_baraholca",
        "freelancetaverna",
        "profiwork",
        "rueventjob",
        "talentedpeoples",
        "talentedp",
        "rabota_freelancee",
        "FrWork3",
        "digitaltender",
        "FreelanceBay",
        "zakaz_design",
        "designwork_vacansii",
        "workfordesigner",
        "designizer",
        "designerworkchat",
        "jun_hi_vacancies",
        "design_careers",
        "jobaem",
        "jobdsg",
        "vacancysmm",
        "search_smm",
        "digital_jobster",
        "rabota_360",
        "udafrii",
        "rabota_udalennaya_vakansii_tg",
        "freegolup",
        "freetasks",
        "frilans",
        "frilanss",
        "freelancce",
        "freelancekp",
        "rabota_na_domu",
        "itfreelancers",
        "rabotafrontend",
        "javascript_jobs_feed",
        "javascript_jobs",
        "job_react",
        "forfrontend",
        "frontend_jobs_channel",
        "StorkLife",
        "it_remote",
        "Getitrussia",
        "UzDev_Jobs",
        "devkz_jobs",
        "cc_vakansii",
    ]

    async def fetch_opportunities(self) -> list[Opportunity]:
        opportunities = []
        current_time = get_current_time()
        
        async with httpx.AsyncClient(headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }, timeout=15.0) as client:
            for channel in self.DEFAULT_CHANNELS:
                url = f"https://t.me/s/{channel}"
                self.logger.info(f"Scanning Telegram channel preview: {url}")
                try:
                    response = await client.get(url)
                    if response.status_code != 200:
                        self.logger.warning(f"Failed to fetch Telegram preview for {channel}: Status {response.status_code}")
                        continue
                        
                    soup = BeautifulSoup(response.text, "html.parser")
                    # Telegram message wraps
                    message_wraps = soup.find_all("div", class_="tgme_widget_message_wrap")
                    
                    self.logger.info(f"Found {len(message_wraps)} messages in {channel}")
                    
                    for wrap in message_wraps:
                        # Extract post link
                        link_tag = wrap.find("a", class_="tgme_widget_message_date")
                        if not link_tag or not link_tag.get("href"):
                            continue
                        post_url = link_tag.get("href")
                        
                        # Extract text
                        text_tag = wrap.find("div", class_="tgme_widget_message_text")
                        if not text_tag:
                            continue
                        
                        full_text = text_tag.get_text(separator="\n").strip()
                        if not full_text:
                            continue
                            
                        # Extract title (first line)
                        lines = [line.strip() for line in full_text.split("\n") if line.strip()]
                        if not lines:
                            continue
                        
                        title = lines[0]
                        if len(title) > 80:
                            title = title[:80] + "..."
                            
                        description = full_text
                        
                        # Try to extract time
                        posted_at = None
                        time_tag = wrap.find("time")
                        if time_tag and time_tag.get("datetime"):
                            try:
                                # Example: 2026-06-15T12:00:00+00:00
                                iso_str = time_tag.get("datetime")
                                # Parse ISO
                                posted_at = datetime.datetime.fromisoformat(iso_str)
                                # Convert to naive local
                                posted_at = posted_at.astimezone().replace(tzinfo=None)
                            except Exception:
                                pass
                                
                        # Deduplicate using hash
                        hash_id = generate_opportunity_hash(title, self.name, post_url, description)
                        
                        opp = Opportunity(
                            hash_id=hash_id,
                            source=self.name,
                            title=title,
                            description=description,
                            url=post_url,
                            client_name=channel,
                            budget=None, # Budget can be parsed from description inside scanner
                            posted_at=posted_at,
                            detected_at=current_time,
                            first_detected_at=posted_at or current_time,
                            raw_data_json=None
                        )
                        opportunities.append(opp)
                        
                except Exception as e:
                    self.logger.error(f"Error fetching channel {channel}: {e}")
                    
        return opportunities
