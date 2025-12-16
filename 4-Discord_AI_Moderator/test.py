import os
import asyncio

import discord
from discord.utils import get

from urlextract import URLExtract
from pysafebrowsing import SafeBrowsing
from detoxify import Detoxify

from utils import * 
from micontants import *

# --- Configure & Initialize ---
intents = discord.Intents.default()
intents.message_content = True  
bot = discord.Client(intents=intents)
 
# --- Others Initialize---
url_extractor = URLExtract()

try:
    safe_browser = SafeBrowsing(GSB_API_KEY)
    print("INIT: Safe Browsing Client initialized.")
except Exception as e :
    print(f"INIT: FAILED to initialize Safe Browing Client. Error: {e}")
    safe_browser = None

try:
    toxicity_model = Detoxify('unbiased', device='cpu')
    print("INIT: Detoxify model initialized.")
except Exception as e:
    print(f"INIT: FAILED to initialize Detoxify model. Error: {e}")
    toxicity_model = None

# --- External Functions ---
# URL Safety Vibe Check
async def check_url_safety(urls: list) -> dict:
    """ Using Google Safe Browsing API to get a list of bad acting URLs"""
    result = 0

    if not safe_browser:
        print("URL SAFETY: GSB client not available. Skipping check.")
        return {}
    print("URL SAFETY: GSB client running. Checking using asyncio.to_thread()...")

    try: 
        result = await asyncio.to_thread(safe_browser.lookup_urls, urls)
        return result
    except Exception as e:
        print(f"URL SAFETY: Error during Safe Browsing API check: {e}")
        return {}
    
# Toxicity Check
async def check_toxicity(text: str) -> dict:
    if not toxicity_model:
        return {}
    
    results = await asyncio.to_thread(toxicity_model.predict, text)
    return results

# --- Bot Events ---
@bot.event
async def on_message(message): 
    if message.author == bot.user:
        return
    
    content = message.content.lower()

    # DEBUG: Says hello when detecting "hello" in chat 
    if "hello" in content: 
        print(f"User '{message.author.name}' said 'hello'. Replying...")
         
        await message.channel.send("hello")

    # --- Link Detection ---
    urls = url_extractor.find_urls(message.content)
    sus_urls = [url for url in urls if not is_whitelist(url)]
    if sus_urls:
        print(f"URL SAFE: Detected URLs in message from {message.author}: {urls}")

        # GSB API Check 
        safety_results = await check_url_safety(sus_urls)
        
        # Moderation action
        malicious_urls = {
            url: data['threads'] 
            for url, data in safety_results.items() if data and data.get('malicious')
        }

        if malicious_urls:
            threats = ", ".join(set(t for d in malicious_urls.values() for t in d))
            print(f"URL SAFE: SUS DETECTED: {malicious_urls} - Threats: {threats}")

            # Action: Delete message
            # DEBUG
            # await message.delete()

            # Action: Send warning
            warning_message = (
                f"YOOO WHAT THIS LINK. {message.author.mention} SUS AF! "
                f"Deleted because it contain a confirmed **malicious link**."
                f"(`{threats}). Stop it of you will be banned! "
                f"Calling pumpy. <@{OWNER_ID}> "
                # TODO: Future ping owner/admins
            )
            await message.channel.send(warning_message)
            return
    
    # --- Toxic Check ---
    # Using HuggingFace's detoxify mini transformer
    if fast_profanity_check(content):
        print(f"FASTFILTER: Potential toxicity detected by keyword.")

        # Check using model
        toxicity_scores = await check_toxicity(content)
        # Action: Warn
        if toxicity_scores.get('toxicity', 0) > TOXICITY_THRESHOLD:
            score = toxicity_scores['toxicity']

            # Action: Delete message
            # DEBUG
            # await message.delete()

            # Action: Send warning 
            warning_message = (
                f"AYO NO NO NO {message.author.mention}! "
                f"NO TOXICITY IN THE BACKYARD. " 
                f"Calling pumpy. <@{OWNER_ID}> "
            )
            await message.channel.send(warning_message)
            return
 


# --- Defaults ---
@bot.event
async def on_ready(): 
    print(f'Bot is ready. Logged in as {bot.user}')

bot.run(TOKEN)