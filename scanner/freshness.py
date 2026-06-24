import datetime
from storage.models import Opportunity
from utils.time_utils import get_current_time

def get_freshness_bucket(age_minutes: int) -> str:
    """Classifies estimated age in minutes into standard buckets."""
    if age_minutes <= 15:
        return "HOT"
    elif age_minutes <= 30:
        return "FRESH"
    elif age_minutes <= 60:
        return "OK"
    elif age_minutes <= 180:
        return "OLD"
    else:
        return "TOO_OLD"

def update_freshness(opp: Opportunity, first_detected_at: datetime.datetime | None = None):
    """
    Calculates the age of the opportunity in minutes relative to the current time,
    and assigns it to the appropriate freshness bucket.
    """
    now = get_current_time()
    
    # If the listing has a specific posted_at timestamp, we base the age on it
    if opp.posted_at:
        # Avoid future timestamps (sometimes feeds have clock drift)
        if opp.posted_at > now:
            opp.posted_at = now
        delta = now - opp.posted_at
        opp.age_minutes = max(0, int(delta.total_seconds() / 60))
    else:
        # Fallback to first_detected_at or current scan detection time
        detected_time = first_detected_at or opp.first_detected_at or opp.detected_at or now
        if detected_time > now:
            detected_time = now
        delta = now - detected_time
        opp.age_minutes = max(0, int(delta.total_seconds() / 60))
        
    opp.freshness_bucket = get_freshness_bucket(opp.age_minutes)
