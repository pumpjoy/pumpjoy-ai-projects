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
    

ROLE_PUM = 1139018430129897592

TRUSTED_DOMAINS = {
    "youtube.com", 
    "youtu.be", 
    "media.tenor.com",
    "tenor.com",
    "google.com",
    "google.test"  
}

TOXIC_TRIGGER_WORDS = {
    "cunt", "nigger", "kys", "kill yourself"
}

TOXICITY_THRESHOLD = 0.8