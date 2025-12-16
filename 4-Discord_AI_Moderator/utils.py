import os
import re
import json
from urllib.parse import urlparse
from micontants import (
    TRUSTED_DOMAINS, 
    LEET_SUBSTITUTIONS,  
    SPAM_TRIGGER_PHRASES,
    LOG_CHANNEL_ID, DATA_FILE,
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
    
def check_profanity(text: str, word_list: list) -> bool:
    """
    Checks for profanity, including common Leet Speak substitutions, 
    by normalizing the text before tokenization.
    """ 
    # Leet Speak Substitution 
    text_processed = list(text.lower())
    for i, char in enumerate(text_processed):
        if char in LEET_SUBSTITUTIONS:
            text_processed[i] = LEET_SUBSTITUTIONS[char]
    
    # Join back into a single string
    text_substituted = "".join(text_processed) 

    # Removes non-alphanumerical, lowercase words
    normalized = re.sub(r'[^a-z\s]', '', text_substituted)
    no_spaces = normalized.replace(" ", "")

    # Splits the sentence into words and check each of them
    words = set(normalized.split())
    is_toxic = bool(words.intersection(word_list))
    
    # Substring match in the 'no_spaces' version
    # This catches 'y o u r e a n a s s' because it becomes 'youreanass'
    if not is_toxic:
        for bad_word in word_list:
            if bad_word in no_spaces:
                is_toxic = True
                break
    return is_toxic, normalized

def check_spam(text: str) -> bool: 
    content_lower = text.lower()
    
    # Checks for direct intersection
    for phrase in SPAM_TRIGGER_PHRASES:
        if phrase in content_lower:
            return True
            
    return False

# JSON
# Load or initialize the data file
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If the file is empty or corrupted, return an empty dict
        print(f"{DATA_FILE} was empty or corrupted. Resetting...")
        return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

