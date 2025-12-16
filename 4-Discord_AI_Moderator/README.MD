# Pumpoo Bot
- This is a moderator bot curated for my own discord guild.
- It uses Google Safe Browsing API, and Detoxify AI stack. It is built in mind to ensure fast and accurate as well as reliable as it is meant to be used.
- Will have further uses other than current moderation-json functions.
- Moderates on:
  - Malicious link - based on Google Safe Browsing API.
  - Spam/Self-Promo - a lite spam/self-promo checker.
  - Toxicity - Has 2 tiers, where 1 is deemed lighter, and another which has zero-tolerance. This is powered by Detoxify model.

1. Scam link detector using pysafebrowsing (Google Cloud API)
  - It correctly checks embedded links as well.
  - Uses whitelist to remove the need of using the API to check commonly accessed domains. 
  - Expand more on `miconstants.py`

2. Actual Moderation
- This category will begin to use NLP to process.
    1. Violation: Spam/Self-promo text
        - Description: Unsolicited advertising, channel bombing, 'DM me' scams.
        - Sample keywords: free nitro, DM me for details, check out my server, invite link
        - Weakness: It does not work under the condition below:
          - the offensive words are worded in a specific manner, such as "t h i s i s m a l i c i o u s", and its equivalents.
          - TODO: May use a stronger rule or another LITE AI Stack to do this task in the future.
    2. Violation: Hate speech/Harassment
        - Description: Attacks based on identity, personal insults.
        - Sample keywords: slurs, threats, aggressive targeting (advance required)
        - Similar weakness to Violation/Spam.
- AI Very Deep Learning LLM Stack is not used, is intended. I wanted to run this bot locally with limited resources as well as maintaining good resource usage to practice sustainable development.
 
---

### Tests

#### 1. Security & Bypass Tests (Priority 1)
These tests ensure that users cannot bypass your filters with clever formatting.
* **The "Invisible Character" Test:** 🔄️
    * *Input:* `y o u  a r e  a s s` (Multiple spaces or tabs). 
    * *Goal:* Verify the `normalized_for_model` regex correctly collapses whitespace so the token check hits.
    * *Note:* The current version only catches these words in `check_profanity`, but does not do anything to it. It would require way more rules (and possibly data) for it to consider typos or actual malicious intent.
* **The "Punctuation Cramming" Test:** ✅
    * *Input:* `you...4ss!!!` or `f.a.g.g.o.t`
    * *Original Goal:* Ensure the Zero-Tolerance and Profanity filters strip non-alpha characters before checking the word set.
    * *Note:* The current version only catches these words in `check_profanity`, but does not do anything to it. It would require way more rules (and possibly data) for it to consider typos or actual malicious intent.
* **The "Newline" Bypass:** ✅
    * *Input:* Putting a slur on a new line after a long paragraph of "good" text.
    * *Goal:* Verify the `content_lower` captures the entire message body, not just the first line.

#### 2. False Positive Prevention (Context Tests)
One of the biggest complaints with AI bots is over-moderation.
* **The "Medical/Educational" Context:** ✅
    * *Input:* "I have a pain in my ass/butt."
    * *Goal:* The NLP should recognize this as non-toxic (Self-referential vs. Targeted).
* **The "Reclaiming" Test:** ✅
    * *Input:* "I'm so queer and proud." (Depending on your community settings).
    * *Goal:* Check if `identity_attack` scores are triggered appropriately versus a simple `insult`.
* **The "Homonym" Test:** ✅
    * *Input:* "The bit of the drill broke." (Testing if 'bit' triggers 'bitch').
    * *Goal:* Verify that your `words.intersection` looks for **exact** word matches, not just substrings.

#### 3. Behavioral Logic & State Tests
Ensuring the JSON database and point system handle updates correctly.
* **The "Decay" Simulation (Manual):** ✅
    * *Input:* `/add_score amount: 1` followed by `/pardon amount: 1`.
    * *Goal:* Ensure the score returns to exactly `0` and doesn't go into negative numbers (which could crash the logic).
* **The "Multiple Violation" Message:** ✅
    * *Input:* A message containing both a scam link AND a slur.
    * *Goal:* Verify that the **highest priority** violation (Zero-Tolerance) is the one logged, preventing double-logging for the same message.
* **The "Nickname" Change:** ✅
    * *Input:* Change a user's nickname and then run `/stats`.
    * *Goal:* Ensure the bot tracks by `user_id` (permanent) rather than `name` (changeable).

#### 4. Performance & Reliability Tests
* **The "Model Timeout" Test:** ✅
    * *Input:* Send a very long message (near the 2000-character limit).
    * *Goal:* Ensure `itx.response.defer()` is working so the slash command doesn't time out while the Transformer model processes the long string.
* **The "API Failure" Graceful Exit:** ✅
    * *Action:* Temporarily disconnect your internet or provide a fake API key.
    * *Goal:* The bot should log an error to the console but **not crash**, allowing normal messages to still pass through.
 