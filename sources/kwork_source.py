from curl_cffi import requests
from bs4 import BeautifulSoup
from sources.base import BaseSource
from storage.models import Opportunity
from utils.hashing import generate_opportunity_hash
from utils.time_utils import get_current_time
from utils.text import clean_html, extract_budget

class KworkSource(BaseSource):
    name = "kwork"

    async def fetch_opportunities(self) -> list[Opportunity]:
        self.logger.info("Scanning Kwork project board...")
        opportunities = []
        current_time = get_current_time()
        
        try:
            # IT/Programming category on Kwork
            url = "https://kwork.ru/projects?c=11"
            # impersonate="chrome" copies Chrome's TLS fingerprint to bypass Cloudflare
            r = requests.get(url, impersonate="chrome", timeout=15)
            
            if r.status_code != 200:
                self.logger.warning(f"Kwork returned status {r.status_code}. Cloudflare block or network issue.")
                return opportunities
                
            soup = BeautifulSoup(r.content.decode("utf-8"), "html.parser")
            
            # Kwork project wants are marked with want-card class
            cards = soup.select(".want-card")
            self.logger.info(f"Found {len(cards)} want-card structures in Kwork HTML")
            
            for card in cards:
                # 1. Title and link
                title_el = card.select_one(".want-card__title a") or card.select_one(".project-card__title a")
                if not title_el:
                    continue
                title = title_el.text.strip()
                link = title_el.get("href", "")
                if not link.startswith("http"):
                    link = "https://kwork.ru" + link
                    
                # 2. Description
                desc_el = card.select_one(".want-card__description") or card.select_one(".project-card__description")
                description = desc_el.text.strip() if desc_el else ""
                
                # 3. Budget / Price
                price_el = card.select_one(".want-card__price") or card.select_one(".want-card__header-price") or card.select_one(".project-card__price")
                budget = price_el.text.strip() if price_el else None
                
                # Deduplicate using hash
                hash_id = generate_opportunity_hash(title, self.name, link, description)
                
                # Create standard Opportunity
                opp = Opportunity(
                    hash_id=hash_id,
                    source=self.name,
                    title=title,
                    description=description,
                    url=link,
                    client_name="Kwork Buyer",
                    budget=budget,
                    posted_at=None,  # Kwork doesn't show exact post seconds on preview, using top-of-feed detection
                    detected_at=current_time,
                    first_detected_at=current_time,
                    raw_data_json=None
                )
                opportunities.append(opp)
                
        except Exception as e:
            self.logger.error(f"Error fetching Kwork opportunities: {e}")
            
        return opportunities
