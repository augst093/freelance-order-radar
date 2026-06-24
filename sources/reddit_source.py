import httpx
from bs4 import BeautifulSoup
from sources.base import BaseSource
from storage.models import Opportunity
from utils.hashing import generate_opportunity_hash
from utils.time_utils import get_current_time, parse_rss_date
from utils.text import clean_html, extract_budget

class RedditSource(BaseSource):
    name = "reddit"
    
    # Track freelance subreddits
    SUBREDDITS = [
        "forhire",
        "freelance",
        "designjobs",
        "TelegramBots"
    ]

    async def fetch_opportunities(self) -> list[Opportunity]:
        opportunities = []
        current_time = get_current_time()
        
        # Reddit requires a unique User-Agent to avoid 429 errors
        headers = {
            "User-Agent": "python:freelance-order-radar:v1.0 (by /u/freelancer_radar_bot)"
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
            for sub in self.SUBREDDITS:
                url = f"https://www.reddit.com/r/{sub}/new/.rss"
                self.logger.info(f"Scanning Reddit RSS: {url}")
                try:
                    response = await client.get(url)
                    if response.status_code == 429:
                        self.logger.warning(f"Reddit rate-limited (429) for r/{sub}. Skipping this scan.")
                        continue
                    if response.status_code != 200:
                        self.logger.warning(f"Failed to fetch Reddit RSS for r/{sub}: Status {response.status_code}")
                        continue
                        
                    soup = BeautifulSoup(response.text, "xml")
                    entries = soup.find_all("entry")
                    self.logger.info(f"Found {len(entries)} entries in r/{sub}")
                    
                    for entry in entries:
                        title_tag = entry.find("title")
                        link_tag = entry.find("link")
                        content_tag = entry.find("content")
                        updated_tag = entry.find("updated")
                        author_tag = entry.find("author")
                        
                        if not title_tag or not link_tag:
                            continue
                            
                        title = title_tag.text.strip()
                        # Reddit RSS links are in href attributes
                        url = link_tag.get("href", "")
                        
                        # Skip if it is not a hiring post
                        # forhire posts usually start with [Hiring] or [LFW] (Looking For Work)
                        # We only want hiring posts
                        title_lower = title.lower()
                        if "forhire" in sub:
                            if not ("[hiring]" in title_lower or "hiring" in title_lower or "looking for" in title_lower) or "[lfw]" in title_lower:
                                continue
                        
                        # Extract description from content tag
                        description = clean_html(content_tag.text.strip()) if content_tag else ""
                        
                        posted_at = None
                        if updated_tag:
                            posted_at = parse_rss_date(updated_tag.text)
                            
                        client_name = "Reddit User"
                        if author_tag:
                            name_tag = author_tag.find("name")
                            if name_tag:
                                client_name = name_tag.text.replace("/u/", "").strip()
                                
                        budget = extract_budget(title) or extract_budget(description)
                        hash_id = generate_opportunity_hash(title, self.name, url, description)
                        
                        opp = Opportunity(
                            hash_id=hash_id,
                            source=self.name,
                            title=title,
                            description=description,
                            url=url,
                            client_name=client_name,
                            budget=budget,
                            posted_at=posted_at,
                            detected_at=current_time,
                            first_detected_at=posted_at or current_time,
                            raw_data_json=None
                        )
                        opportunities.append(opp)
                        
                except Exception as e:
                    self.logger.error(f"Error parsing Reddit RSS for r/{sub}: {e}")
                    
        return opportunities
