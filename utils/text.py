import re

def clean_html(text: str) -> str:
    """Removes HTML tags and unescapes HTML entities."""
    if not text:
        return ""
    # Strip HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    # Basic HTML entity resolution
    entities = {
        "&quot;": '"',
        "&amp;": '&',
        "&lt;": '<',
        "&gt;": '>',
        "&nbsp;": ' ',
        "&apos;": "'",
        "&#039;": "'"
    }
    for entity, char in entities.items():
        text = text.replace(entity, char)
    return text

def contains_keyword(text: str, keywords: list[str]) -> bool:
    """Checks if any keyword in the list is present in the text (case-insensitive)."""
    if not text or not keywords:
        return False
    
    text_lower = text.lower()
    for kw in keywords:
        kw_lower = kw.lower()
        # Word boundary or simple substring check depending on the keyword length
        if len(kw_lower) <= 3:
            # Short keywords need word boundaries to avoid false positives (e.g. 'bot' in 'both')
            pattern = r'\b' + re.escape(kw_lower) + r'\b'
            if re.search(pattern, text_lower):
                return True
        else:
            if kw_lower in text_lower:
                return True
    return False

def count_keyword_matches(text: str, keywords: list[str]) -> int:
    """Counts how many unique keywords from the list match the text."""
    if not text or not keywords:
        return 0
        
    text_lower = text.lower()
    count = 0
    for kw in keywords:
        kw_lower = kw.lower()
        if len(kw_lower) <= 3:
            pattern = r'\b' + re.escape(kw_lower) + r'\b'
            if re.search(pattern, text_lower):
                count += 1
        else:
            if kw_lower in text_lower:
                count += 1
    return count

def extract_budget(text: str) -> str | None:
    """
    Tries to extract budget information if present.
    Finds numbers associated with currency symbols like $, €, £, ₽, руб, usd, eur.
    """
    if not text:
        return None
        
    # Standard budget patterns in descriptions
    patterns = [
        r'(?:budget|price|бюджет|цена|оплата|стоимость)\s*(?:is|:|:-)?\s*[\d\s\.,]+(?:usd|eur|rub|руб|р|\$|€|₽)',
        r'[\d\s\.,]+(?:usd|eur|rub|руб|р|\$|€|₽)',
        r'(?:\$|€|₽|£)\s*[\d\s\.,]+'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Return the first reasonable match, stripped
            clean_match = matches[0].strip()
            # If it's just a number like "10" or "0", let's be careful. Let's make sure it contains digits.
            if any(char.isdigit() for char in clean_match):
                return clean_match
                
    return None

def summarize_text(text: str, max_chars: int = 200) -> str:
    """Truncates text to a maximum size and adds ellipsis if needed."""
    if not text:
        return ""
    text = clean_html(text).strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].strip() + "..."
