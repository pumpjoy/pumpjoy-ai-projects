# TODO: Future implement log system

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

    # --- Link Check ---
    # External check with highest confidence
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
                f"Calling pumpy. <@{OWNER_ID}> " # Error is caught by python itself
            )
            await message.channel.send(content=warning_message)
            await message.channel.send(stickers=[await message.guild.fetch_sticker(STICKER_AYONONONO)]) 
            return
        
    # --- Zero Tolerance Check ---
    is_triggered, clean_text = check_profanity(content, TOXIC_ZERO_TOLERANCE_WORDS)
    if is_triggered:
        print(f"TOXIC ZEROTOL: Potential zero-tolerance toxicity detected by keyword.")
        # Action: Delete message
        # DEBUG
        # await message.delete()
        warning_message = (
            f"ABSOLUTELY NO NO {message.author.mention}! "
            f"DO NOT USE THAT WORD AGAIN OR HEAVIER CONSEQUENCE WILL HAPPEN! " 
            f"Calling pumpy. <@{OWNER_ID}> "
        )
        await message.channel.send(content=warning_message)
        await message.channel.send(stickers=[await message.guild.fetch_sticker(STICKER_AYONONONO)])
        return


    # --- Spam/Self-promo Check ---
    # Quick check
    if check_spam(content):
        print(f"SPAM: Scam/Self-promo keyword found: '{content}'")

        # Moderation action 
        await message.channel.send(stickers=[await message.guild.fetch_sticker(STICKER_AYONONONO)]) # Error is caught by discordpy itself, it will not crash
        # DEBUG
        # await messsage.delete()
        return
    
    # --- Toxic Check ---
    # Takes the longest to process, so will put at the end
    # Using HuggingFace's detoxify mini transformer
    
    is_triggered, clean_text = check_profanity(content, TOXIC_TRIGGER_WORDS)
    if is_triggered:
        print(f"TOXIC: Potential toxicity detected by keyword.")

        # Check using model
        toxicity_scores = await check_toxicity(clean_text) 
        print(f"TOXIC: CLEAN TEXT: {clean_text}")
        print(f"TOXIC: SCORE: {toxicity_scores}")
        # Action: Warn
        insult_score = toxicity_scores.get('insult', 0)
        threat_score = toxicity_scores.get('threat', 0)
        sexual_score = toxicity_scores.get('sexual_explicit', 0)

        if (insult_score > THRESHOLD_INSULT or 
            threat_score > THRESHOLD_THREAT or 
            sexual_score > THRESHOLD_SEXUAL):

            # Action: Delete message
            # DEBUG
            # TODO: log the message with message link
            # TODO: excel to keep track of users who offended?
            # await message.delete()
            
            # Action: Send warning 
            warning_message = (
                f"AYO NO NO NO {message.author.mention}! "
                f"NO TOXICITY IN THE BACKYARD. " 
                f"Calling pumpy. <@{OWNER_ID}> "
            )
            await message.channel.send(content=warning_message)
            await message.channel.send(stickers=[await message.guild.fetch_sticker(STICKER_AYONONONO)])
            return
 


# --- Defaults ---
@bot.event
async def on_ready(): 
    print(f'Bot is ready. Logged in as {bot.user}')

bot.run(TOKEN)