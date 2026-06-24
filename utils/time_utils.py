import datetime
import email.utils
import re

def get_current_time() -> datetime.datetime:
    """Returns the current timezone-naive datetime (local time)."""
    return datetime.datetime.now()

def parse_rss_date(date_str: str) -> datetime.datetime | None:
    """
    Parses common RSS date formats (like RFC 2822 / 822) to naive local datetime.
    """
    if not date_str:
        return None
    try:
        # RFC 2822 parse
        parsed_struct = email.utils.parsedate_to_datetime(date_str)
        # Convert to local time zone (naive)
        local_dt = parsed_struct.astimezone().replace(tzinfo=None)
        return local_dt
    except Exception:
        # Fallback parsing attempts
        for fmt in (
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S",
            "%d.%m.%Y %H:%M",
            "%d %b %Y %H:%M:%S"
        ):
            try:
                dt = datetime.datetime.strptime(date_str.strip(), fmt)
                if dt.tzinfo:
                    dt = dt.astimezone().replace(tzinfo=None)
                return dt
            except ValueError:
                continue
    return None

def parse_relative_time(relative_str: str) -> datetime.datetime | None:
    """
    Parses relative time strings like '5 minutes ago', '2 hours ago', '10м назад', '2 часа назад'
    and returns estimated local datetime.
    """
    if not relative_str:
        return None
        
    current = get_current_time()
    relative_str = relative_str.lower().strip()
    
    # English patterns
    match_min = re.search(r'(\d+)\s*(min|minute|m)', relative_str)
    match_hour = re.search(r'(\d+)\s*(hour|hr|h)', relative_str)
    match_day = re.search(r'(\d+)\s*(day|d)', relative_str)
    
    # Russian patterns
    match_min_ru = re.search(r'(\d+)\s*(мин|минут)', relative_str)
    match_hour_ru = re.search(r'(\d+)\s*(час|ч)', relative_str)
    match_day_ru = re.search(r'(\d+)\s*(день|дня|дней|д)', relative_str)
    
    minutes = 0
    hours = 0
    days = 0
    
    if match_min:
        minutes = int(match_min.group(1))
    elif match_min_ru:
        minutes = int(match_min_ru.group(1))
    elif match_hour:
        hours = int(match_hour.group(1))
    elif match_hour_ru:
        hours = int(match_hour_ru.group(1))
    elif match_day:
        days = int(match_day.group(1))
    elif match_day_ru:
        days = int(match_day_ru.group(1))
    else:
        # Check if contains "just now" or "только что"
        if "just now" in relative_str or "только что" in relative_str or "now" in relative_str:
            return current
        return None
        
    delta = datetime.timedelta(days=days, hours=hours, minutes=minutes)
    return current - delta

def calculate_age_minutes(posted_at: datetime.datetime | None, detected_at: datetime.datetime, first_detected_at: datetime.datetime | None = None) -> int:
    """
    Calculates age in minutes.
    If posted_at is available, age = (current_time - posted_at).
    If not, we use the first_detected_at time.
    """
    ref_time = posted_at or first_detected_at or detected_at
    delta = get_current_time() - ref_time
    return max(0, int(delta.total_seconds() / 60))
