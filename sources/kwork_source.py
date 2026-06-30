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
                
            import re, json
            soup = BeautifulSoup(r.content.decode("utf-8", "ignore"), "html.parser")
            
            wants = []
            scripts = soup.find_all('script')
            for s in scripts:
                if s.string and len(s.string) > 100000:
                    match = re.search(r'window\.stateData\s*=\s*(.*?);window', s.string)
                    if match:
                        try:
                            state = json.loads(match.group(1))
                            wants = state.get('wantsListData', {}).get('wants', [])
                            break
                        except Exception as e:
                            self.logger.error(f"Kwork JSON parse error: {e}")
            
            self.logger.info(f"Found {len(wants)} projects in Kwork JSON state")
            
            for w in wants:
                title = w.get("name", "").strip()
                if not title:
                    continue
                link = f"https://kwork.ru/projects/{w.get('id')}/view"
                description = w.get("description", "").strip()
                budget = str(w.get("priceLimit", ""))
                if budget:
                    budget += " ₽"
                    
                hash_id = generate_opportunity_hash(title, self.name, link, description)
                
                opp = Opportunity(
                    hash_id=hash_id,
                    source=self.name,
                    title=title,
                    description=description,
                    url=link,
                    client_name="Kwork Buyer",
                    budget=budget,
                    posted_at=None,
                    detected_at=current_time,
                    first_detected_at=current_time,
                    raw_data_json=json.dumps(w)
                )
                opportunities.append(opp)
                
        except Exception as e:
            self.logger.error(f"Error fetching Kwork opportunities: {e}")
            
        return opportunities
