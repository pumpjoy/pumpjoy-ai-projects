# TODO: Future implement log system

import os
import asyncio
import datetime

import discord 
from discord.ext import commands
from discord import app_commands

from urlextract import URLExtract
from pysafebrowsing import SafeBrowsing
from detoxify import Detoxify

from utils import * 
from micontants import *

# --- Configure & Initialize ---
intents = discord.Intents.default()
intents.message_content = True
# bot = discord.Client(intents=intents)
# bot = commands.Bot(command_prefix="7", intents=intents)

class PumpooBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        
    async def setup_hook(self): 
        await self.tree.sync()
        print("Slash commands synced!")
bot = PumpooBot()

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

# Json save offenders data
async def log_offense(user, offense_type, content, point_value=None, extra_info=""):
    data = load_data()
    user_id = str(user.id)
    
    if user_id not in data:
        data[user_id] = {"name": user.name, "behavior_score": 0, "history": []}
    
    # If point_value is passed (manual), use it. 
    # Otherwise, look up the automated severity.
    pts = point_value if point_value is not None else SEVERITY_SCORES.get(offense_type, 1)
    
    data[user_id]["behavior_score"] += pts
    # Prevent negative total scores
    if data[user_id]["behavior_score"] < 0:
        data[user_id]["behavior_score"] = 0
        
    current_score = data[user_id]["behavior_score"]
    
    # Single Save Point
    entry = {
        "offense": offense_type,
        "points": pts,
        "content": content,
        "timestamp": str(datetime.datetime.now())
    }
    data[user_id]["history"].append(entry)
    save_data(data)

    # Single Logging Point (Embed)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        # Green for pardons (negative pts), Red/Orange for offenses
        color = 0x2ecc71 if pts < 0 else (0xff0000 if pts >= 50 else 0xffa500)
        embed = discord.Embed(title="📈 Behavior Update", color=color)
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Action", value=offense_type, inline=True)
        embed.add_field(name="Point Change", value=f"{pts:+}", inline=True) # Shows + or -
        embed.add_field(name="New Total", value=f"**{current_score}**", inline=True)
        embed.add_field(name="Details", value=content, inline=False)
        
        await log_channel.send(embed=embed)

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

            # Action: Log and Delete message 
            await log_offense(message.author, "Malicious Link", message.content)
            # await message.delete() # DEBUG

            # Action: Send warning 
            warning_message = (
                f"YOOO WHAT THIS LINK. {message.author.mention} SUS AF! "
                f"Deleted because it contain a confirmed **malicious link**. \n"
                f"(`{threats}). Stop it of you will be banned! \n"
                f"Calling pumpy. <@{OWNER_ID}> " # Error is caught by python itself
            )
            await message.channel.send(content=warning_message)
            await message.channel.send(stickers=[await message.guild.fetch_sticker(STICKER_AYONONONO)]) 
            return
        
    # --- Zero Tolerance Check ---
    is_triggered, clean_text = check_profanity(content, TOXIC_ZERO_TOLERANCE_WORDS)
    if is_triggered:
        print(f"TOXIC ZEROTOL: Potential zero-tolerance toxicity detected by keyword.")
        # Action: Log and Delete message
        await log_offense(message.author, "Toxicity Zero-Tolerance", message.content)
        # await message.delete() # DEBUG

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
  
        await message.channel.send(stickers=[await message.guild.fetch_sticker(STICKER_AYONONONO)]) # Error is caught by discordpy itself, it will not crash
 
        # Action: Log and Delete message
        await log_offense(message.author, "Spam/Self-Promo", message.content)
        # await message.delete() # DEBUG 
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

            # Action: Log and Delete message
            await log_offense(message.author, "Toxicity", message.content)
            # await message.delete() # DEBUG  
            
            # Action: Send warning 
            warning_message = (
                f"AYO NO NO NO {message.author.mention}! \n"
                f"NO TOXICITY IN THE BACKYARD. \n" 
                f"Calling pumpy. <@{OWNER_ID}> "
            )
            await message.channel.send(content=warning_message)
            await message.channel.send(stickers=[await message.guild.fetch_sticker(STICKER_AYONONONO)])
            return
    await bot.process_commands(message)

# --- Bot Commands ---
# ADMIN: Audits a string of text to see what the AI thinks.
@bot.tree.command(name="audit", description="Check toxicity scores for a specific text")
@app_commands.describe(text="The text you want the AI to analyze")
@app_commands.checks.has_permissions(manage_messages=True)
async def audit(itx: discord.Interaction, text: str):
    """Audits a string of text to see what the AI thinks."""
    await itx.response.defer(thinking=True) # Give the AI time to think
    
    is_triggered, clean_text = check_profanity(text, TOXIC_TRIGGER_WORDS)
    scores = await check_toxicity(clean_text)

    # Format the results into a nice embed
    embed = discord.Embed(title="AI Audit Report", color=0x3498db)
    embed.add_field(name="Normalized Text", value=f"`{clean_text}`", inline=False)
    embed.add_field(name="Fast Trigger?", value="Yes" if is_triggered else "No", inline=True)
    
    # List the main categories
    important_categories = ['toxicity', 'insult', 'threat', 'identity_attack']
    for cat in important_categories:
        score = scores.get(cat, 0)
        # Highlight high scores in the display
        status = "⚠️" if score > 0.6 else "✅"
        embed.add_field(name=cat.capitalize(), value=f"{status} {score:.4f}", inline=True)
    
    await itx.followup.send(embed=embed)

# ADMIN: Command to manually increase score
@bot.tree.command(name="add_score", description="Manually increase a user's behavior score")
@app_commands.describe(user="The offender", amount="Points to add", reason="Why?")
@app_commands.checks.has_permissions(manage_messages=True)
async def add_score(itx: discord.Interaction, user: discord.Member, amount: int, reason: str):
    # Just call the unified function
    await log_offense(user, "Manual Adjustment", reason, point_value=amount)
    await itx.response.send_message(f"✅ Added {amount} points to {user.display_name}.", ephemeral=True)

# ADMIN: Command to manually decrease score 
@bot.tree.command(name="pardon", description="Reduce a user's behavior score")
@app_commands.describe(user="The user", amount="Points to remove", reason="Why?")
@app_commands.checks.has_permissions(manage_messages=True)
async def pardon(itx: discord.Interaction, user: discord.Member, amount: int, reason: str):
    # Pass the amount as a negative number
    await log_offense(user, "Manual Pardon", reason, point_value=-amount)
    await itx.response.send_message(f"🩹 Pardoned {amount} points for {user.display_name}.", ephemeral=True)

# ADMIN: Check offender's stats 
@bot.tree.command(name="stats", description="View a user's behavior score and history")
async def stats(itx: discord.Interaction, user: discord.Member):
    data = load_data()
    user_id = str(user.id)
    
    if user_id not in data:
        await itx.response.send_message(f"No records found for {user.display_name}.", ephemeral=True)
        return
        
    score = data[user_id]["behavior_score"]
    await itx.response.send_message(f"**{user.display_name}** has a behavior score of **{score}**.")

# ADMIN: Checks history of last 5 offenses commited by a user
@bot.tree.command(name="history", description="View the recent offense history of a user")
@app_commands.describe(user="The user whose history you want to check")
@app_commands.checks.has_permissions(manage_messages=True)
async def history(itx: discord.Interaction, user: discord.Member):
    data = load_data()
    user_id = str(user.id)
    
    if user_id not in data or not data[user_id]["history"]:
        await itx.response.send_message(f"No history found for {user.display_name}.", ephemeral=True)
        return
        
    user_data = data[user_id]
    recent_history = user_data["history"][-5:]  # Get the 5 most recent entries
    recent_history.reverse() # Show newest at the top
    
    embed = discord.Embed(
        title=f"📜 Behavior History: {user.display_name}",
        description=f"Total Behavior Score: **{user_data['behavior_score']}**",
        color=0x34495e
    )
    embed.set_thumbnail(url=user.display_avatar.url)

    for entry in recent_history:
        # Format the timestamp for readability
        # Assuming timestamp was saved as str(datetime.datetime.now())
        date_str = entry['timestamp'][:16] # Get YYYY-MM-DD HH:MM
        
        pts = entry['points']
        pts_formatted = f"{pts:+}" # Shows +5 or -10
        
        field_name = f"{date_str} | {entry['offense']} ({pts_formatted})"
        # Content is spoilered in the history for safety
        field_value = f"Message: ||{entry['content']}||"
        
        embed.add_field(name=field_name, value=field_value, inline=False)

    await itx.response.send_message(embed=embed) 


# ADMIN: Dynamically add to `TRUSTED_DOMAIN` or an `EXCLUDED_WORDS` list
# NOTE: This command is currently useless, whitelist.txt is not referred anywhere.
@bot.tree.command(name="whitelist_domain", description="Add a domain to the trusted whitelist")
@app_commands.describe(domain="The domain to trust (e.g., github.com)")
@app_commands.checks.has_permissions(administrator=True)
async def whitelist_domain(itx: discord.Interaction, domain: str):
    # Standardize the input
    clean_domain = domain.lower().strip().replace("https://", "").replace("http://", "").split('/')[0]
    
    if clean_domain.startswith("www."):
        clean_domain = clean_domain[4:]
        
    TRUSTED_DOMAINS.add(clean_domain)
    
    # Optional: Save this to a file so it persists after bot restarts
    with open("whitelist.txt", "a") as f: f.write(f"\n{clean_domain}")
    
    await itx.response.send_message(f"The domain `{clean_domain}` is now trusted.", ephemeral=True)

# Shows /help
@bot.tree.command(name="help", description="View the documentation for Pumpoo Bot")
async def help_command(itx: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Moderator System Documentation",
        description="A system that detects malicious links, spam, self-promo and toxicity. Note that this is curated for my specific guild.",
        color=0x3498db
    )

    embed.add_field(
        name="🛡️ Automated Protection",
        value=(
            "• **Zero-Tolerance:** Immediate deletion of severe slurs.\n"
            "• **Scam Check:** Scans links via Google Web Risk API.\n"
            "• **Hybrid Profanity:** Catches leet-speak (4ss, @ss) and uses Detoxify NLP for short context.\n"
            "• **Spam/Self-Promo Filter:** Detects spams and self-promo."
        ),
        inline=False
    )

    embed.add_field(
        name="📊 Behavior System",
        value=(
            "Every violation adds points to a user's **Behavior Score**:\n"
            "Of course, we weigh the offenses.\n"
            "Note that the current system only has negative behavior score.\n"
            "This means we only track bad behaviours. 0 = Good."
        ),
        inline=False
    )

    embed.add_field(
        name="🛠️ Moderator Commands",
        value=(
            "• `/audit [text]`: See raw toxicity scores for any string based on Detoxify.\n"
            "• `/history [user]`: View the last 5 offenses and score.\n"
            "• `/add_score [user] [pts] [reason]`: Manually penalize.\n"
            "• `/pardon [user] [pts] [reason]`: Remove points.\n"
            "• `/whitelist_domain [url]`: Trust a specific website."
        ),
        inline=False
    )

    embed.set_footer(text="System Status: Online | Powered by My PC, Detoxify & Google Web Risk")
    
    await itx.response.send_message(embed=embed, ephemeral=True)


# --- Defaults ---
@bot.event
async def on_ready(): 
    print(f'Bot is ready. Logged in as {bot.user}')

# Handle Permission Error
@bot.tree.error
async def on_app_command_error(itx: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await itx.response.send_message("Beep! Beep! You don't have the required permissions to use this command.", ephemeral=True)
    else:
        print(f"Unhandled Error: {error}")


bot.run(TOKEN)