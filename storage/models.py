import datetime
import json
from dataclasses import dataclass, field, asdict

@dataclass
class Opportunity:
    hash_id: str
    source: str
    title: str
    description: str
    url: str
    client_name: str | None = None
    budget: str | None = None
    posted_at: datetime.datetime | None = None
    detected_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    first_detected_at: datetime.datetime | None = None
    age_minutes: int = 0
    freshness_bucket: str = "HOT"
    category: str = "Other"
    score: int = 5
    difficulty: str = "MEDIUM"
    status: str = "new"  # new, saved, applied, skipped
    suggested_reply: str | None = None
    raw_data_json: str | None = None
    id: int | None = None

    def to_dict(self) -> dict:
        """Converts the Opportunity into a dictionary suitable for database and json operations."""
        d = asdict(self)
        # Convert datetimes to iso strings
        if d.get("posted_at"):
            d["posted_at"] = d["posted_at"].isoformat()
        if d.get("detected_at"):
            d["detected_at"] = d["detected_at"].isoformat()
        if d.get("first_detected_at"):
            d["first_detected_at"] = d["first_detected_at"].isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Opportunity":
        """Reconstructs Opportunity from a dictionary."""
        # Convert iso strings back to datetime
        for key in ("posted_at", "detected_at", "first_detected_at"):
            if d.get(key) and isinstance(d[key], str):
                d[key] = datetime.datetime.fromisoformat(d[key])
        return cls(**d)
