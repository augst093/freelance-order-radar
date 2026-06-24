from abc import ABC, abstractmethod
from storage.models import Opportunity
from utils.logger import get_logger

class BaseSource(ABC):
    name: str = "base"

    def __init__(self):
        self.logger = get_logger(f"source.{self.name}")

    @abstractmethod
    async def fetch_opportunities(self) -> list[Opportunity]:
        """
        Scrapes or fetches freelance orders from the target marketplace.
        Returns a list of parsed Opportunity objects.
        """
        pass
