import httpx
from bs4 import BeautifulSoup
from sources.base import BaseSource
from storage.models import Opportunity
from utils.hashing import generate_opportunity_hash
from utils.time_utils import get_current_time, parse_rss_date
from utils.text import clean_html, extract_budget

class FreelancehuntSource(BaseSource):
    name = "freelancehunt"
    RSS_URL = "https://freelancehunt.com/projects.rss"

    async def fetch_opportunities(self) -> list[Opportunity]:
        self.logger.info("Scanning Freelancehunt RSS feed...")
        opportunities = []
        current_time = get_current_time()
        
        async with httpx.AsyncClient(headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }, timeout=15.0) as client:
            try:
                response = await client.get(self.RSS_URL)
                if response.status_code != 200:
                    self.logger.warning(f"Failed to fetch Freelancehunt RSS: Status {response.status_code}")
                    return opportunities
                    
                soup = BeautifulSoup(response.text, "xml")
                items = soup.find_all("item")
                self.logger.info(f"Found {len(items)} items in RSS feed")
                
                for item in items:
                    title_tag = item.find("title")
                    link_tag = item.find("link")
                    desc_tag = item.find("description")
                    pub_date_tag = item.find("pubDate")
                    
                    if not title_tag or not link_tag:
                        continue
                        
                    title = title_tag.text.strip()
                    url = link_tag.text.strip()
                    description = clean_html(desc_tag.text.strip()) if desc_tag else ""
                    
                    posted_at = None
                    if pub_date_tag:
                        posted_at = parse_rss_date(pub_date_tag.text)
                        
                    # Extract budget from description or title if possible
                    budget = extract_budget(title) or extract_budget(description)
                    
                    # Deduplicate using hash
                    hash_id = generate_opportunity_hash(title, self.name, url, description)
                    
                    opp = Opportunity(
                        hash_id=hash_id,
                        source=self.name,
                        title=title,
                        description=description,
                        url=url,
                        client_name="Freelancehunt Client",
                        budget=budget,
                        posted_at=posted_at,
                        detected_at=current_time,
                        first_detected_at=posted_at or current_time,
                        raw_data_json=None
                    )
                    opportunities.append(opp)
                    
            except Exception as e:
                self.logger.error(f"Error parsing Freelancehunt RSS: {e}")
                
        return opportunities
