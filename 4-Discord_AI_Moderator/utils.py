import re
from urllib.parse import urlparse
from micontants import (
    TRUSTED_DOMAINS, TOXIC_TRIGGER_WORDS
)

def is_whitelist(url: str) -> bool:
    try:
        parse_url = urlparse(url)
        domain = parse_url.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        print("URL SAFE: Whitelist checked.")
        return domain in TRUSTED_DOMAINS

    except Exception as e:
        print("URL SAFE: Error parsing URL for Whitelisting: {e}")
        return False 
    
def fast_profanity_check(text: str) -> bool:
    # Removes non-alphanumerical, lowercase words
    normalized  = re.sub(r'[^a-z\s]', ' ', text.lower())

    words = set(normalized.split())
    return bool(words.intersection(TOXIC_TRIGGER_WORDS))
