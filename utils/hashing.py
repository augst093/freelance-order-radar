import hashlib
import re

def normalize_string(s: str) -> str:
    """Lowercase, remove special characters and extra whitespace."""
    if not s:
        return ""
    # Lowercase
    s = s.lower()
    # Remove HTML tags if any
    s = re.sub(r'<[^>]*>', '', s)
    # Remove non-alphanumeric characters but keep spaces
    s = re.sub(r'[^\w\s]', '', s)
    # Collapse multiple whitespaces
    s = " ".join(s.split())
    return s

def generate_opportunity_hash(title: str, source: str, url: str | None = None, description: str | None = None) -> str:
    """
    Generates a unique MD5 hash for the opportunity to prevent duplicates.
    Uses normalized title + source + URL hash.
    If URL is unavailable or empty, hashes title + description + source.
    """
    norm_title = normalize_string(title)
    norm_source = normalize_string(source)
    
    if url and url.strip():
        # Clean URL (remove tracking params, query parameters if variable)
        clean_url = url.strip().split("?")[0]
        data_str = f"{norm_title}||{norm_source}||{clean_url}"
    else:
        norm_desc = normalize_string(description or "")
        data_str = f"{norm_title}||{norm_source}||{norm_desc}"
        
    return hashlib.md5(data_str.encode("utf-8")).hexdigest()
