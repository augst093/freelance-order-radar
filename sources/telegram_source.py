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
        "freelancedise",
        "freelance_rabota_rf",
        "it_vakansii_jobs",
        "devs_jobs",
        "frontend_job_offers",
        "backend_job_offers",
        "UzDev_Jobs",
        "devkz_jobs",
        "jun_hi_vacancies",
        "vacancysmm",
        "search_smm",
        "digital_jobster",
        # --- Каналы добавлены пользователем ---
        "freelansim_ru",
        "FreeVacanciesIT",
        "freelancetaverna",
        "digitaltender",
        "digitaltalks",
        "FreelanceBay",
        "Koteyka_Freelancer",
        "webfrl",
        "job_webdev",
        "front_end_dev",
        "javascript_jobs",
        "javascript_jobs_feed",
        "nodejs_jobs",
        "nodejs_jobs_feed",
        "react_js",
        "angular_ru",
        "angular_jobs_feed",
        "js_ru",
        "forwebdev",
        "forfrontend",
        "front_end_jobs",
        "runello_rus_frontend",
        "job_react",
        "frontend_job_geeklink",
        "easy_frontend_jobs",
        "frontend_jobs_channel",
        "rabotafrontend",
        "itfreelancers",
        "habr_career",
        "Getitrussia",
        "ru_pythonjobs",
        "job_python",
        "python_jobs",
        "python_jobs_feed",
        "django_jobs",
        "php_jobs",
        "php_jobs_feed",
        "laravel_jobs",
        "vuejs_jobs",
        "vue_jobs",
        "typescript_jobs",
        "html_css_jobs",
        "it_remote",
        "remoteit",
        "itjobs_ru",
        "dev_jobs",
        "dev_jobs_ru",
        "mobile_jobs",
        "mobile_jobs_feed",
        "FreeWorkFeed",
        "FrWork3",
        "freegolup",
        "workzavr",
        "ipomogator",
        "kadrof_work",
        "rabotka_zdes",
        "workk_on",
        "freelancers_kwork",
        "Happy_Freelancer",
        "TeIeWWork",
        "frilans",
        "frilanss",
        "freelancce",
        "FRILANSb",
        "frilanc",
        "freelancekp",
        "freelancetg",
        "freelance_tg",
        "freelance_job",
        "freelance_jobs_ru",
        "freelance_jobs",
        "freelance_order",
        "freelance_orders",
        "frilans_orders",
        "freetasks",
        "free_tasks",
        "freework_ru",
        "rabota_freelancee",
        "rabota_udalennaya_vakansii_tg",
        "rabota_na_domu",
        "rabota_360",
        "udafrii",
        "dubaiprofi",
        "profiwork",
        "talentedpeoples",
        "talentedp",
        "StorkLife",
        "cc_vakansii",
        "mari_vakansii",
        "mari_vakansiii",
        "mirkreatorovjob",
        "ggfreelancechat",
        "proffreelancee_baraholca",
        "rueventjob",
        "jobaem",
        "jobdsg",
        "vacanciesrus",
        "digital_hr",
        "work_finde",
        "perezvonyu",
        "morejobs",
        "seohr",
        "zakaz_design",
        "designwork_vacansii",
        "workfordesigner",
        "designerworkchat",
        "designizer",
        "design_careers",
        "design_jobs_uxui",
        "design_jobs",
        "designer_jobs",
        "jobfordesigners",
        "uxui_jobs",
        "uiux_jobs",
        "ux_ui_jobs",
        "designhunters",
        "cgfreelance",
        "design_birja",
        "ishudesignera",
        "design_orders",
        "web_design_jobs",
        "webdesigner_jobs",
        "figma_jobs",
        "tilda_jobs",
        "tilda_work",
        "tilda_chat",
        "tilda_vacancy",
        "webflow_ru",
        "webflow_jobs",
        "flru_jobs_bot",
        "fl_monitor_bot",
        "GetClient",
        "LeadRadarBot",
        "tvrn_otc",
        "tvrn_p2p",
        "pbotc",
        "otc_gucci",
        "GrailOTC",
        "SCryptOTC",
        "bears_otc",
        "web_investors",
        "vseznayka_otc",
        "RusCryptEx",
        "mexcotc",
        "cryptootcc",
        "otctopcrypto",
        "doubletop_otc",
        "otc_market_europe",
        "marketplace_otc",
        "market_community",
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
