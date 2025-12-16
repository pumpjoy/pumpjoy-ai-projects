import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN') 
GSB_API_KEY = os.getenv('GSB_API_KEY')
OWNER_ID = os.getenv('OWNER_ID')
if not TOKEN:
    print("FATAL ERROR: DISCORD_TOKEN environment variable not set.")
if not GSB_API_KEY:
    print("FATAL ERROR: GSB_API_KEY environment variable not set.")

if not OWNER_ID:
    print("TOKEN ERROR: OWNER_ID environment variable not set.")
    OWNER_ID = 0

LOG_CHANNEL_ID = 1450377914624376883
DATA_FILE = "discord_channel_offenders.json"

ROLE_PUM = 1139018430129897592 # Is a guild specific role id 

STICKER_AYONONONO = 1450046205798252635 # Is a guild specific sticker
STICKER_IDS = [STICKER_AYONONONO]

SEVERITY_SCORES = {
    "Spam/Self-Promo": 1,
    "Toxicity": 3,
    "Malicious Link": 5,
    "Toxicity Zero-Tolerance": 5
}

TRUSTED_DOMAINS = {
    "youtube.com", 
    "youtu.be", 
    "media.tenor.com",
    "tenor.com",
    "google.com",
    "google.test"  
}

LEET_SUBSTITUTIONS = {
    '4': 'a',
    '@': 'a',
    '3': 'e',
    '8': 'b',
    '!': 'i',
    '1': 'i',
    '0': 'o',
    '5': 's',
    '$': 's',
    '7': 't',
    '+': 't',
    '9': 'g',
    '|': 'l',
    'v': 'u',
    'z': 's' 
}

TOXIC_ZERO_TOLERANCE_WORDS = {
    'kys', 'kill yourself',
    "nigger", "nigga",  
    "faggot", "fag", "fagg",
    "chink", "kike",
    'retard', 'retarded', 'retarde'
}

TOXIC_TRIGGER_WORDS = { 
    'ass', 'asshat', 'shit', 'bullshit',
    'cunt','fuck', 'sucks', 'suck',
    'dummy', 'dumb', 'dum', 'stupid', 'idiot', 
}
 
THRESHOLD_INSULT = 0.9
THRESHOLD_THREAT = 0.9
THRESHOLD_SEXUAL = 0.9

SPAM_TRIGGER_PHRASES = {
    "free nitro",           # Fake Nitro giveaways
    "dm me for",            # Direct message solicitations
    "check out my server",  # Self-promotion
    "join my discord",      # Self-promotion
    "join my server",      # Self-promotion
    "invite link",          # Self-promotion
    "airdrop",              # Crypto/NFT scam keyword
    "won a prize",          # Unsolicited giveaway scam
    "crypto giveaway",      # Crypto/NFT scam keyword
    "steam account"         # Common phishing vector (Discord-Steam scam)
}