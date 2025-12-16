1. Scam link detector using pysafebrowsing (Google Cloud API)
  - It correctly checks embedded links as well.
  - Uses whitelist to remove the need of using the API to check commonly accessed domains. 
  - Expand more on `miconstants.py`

2. Actual Moderation
- This category will begin to use NLP to process.
    1. Violation: Spam/Self-promo text
        - Description: Unsolicited advertising, channel bombing, 'DM me' scams.
        - Sample keywords: free nitro, DM me for details, check out my server, invite link
        - Moderation Action: DEBUG: Aiyo sticker 
    2. Violation: Hate speech/Harassment
        - Description: Attacks based on identity, personal insults.
        - Sample keywords: slurs, threats, aggressive targeting (advance required)
        - Moderation Action: DEBUG: Aiyo sticker


Tests:
1. Malware domain test (BEWARE). This it the most critical check, so must be high up in sequence. It will not detect test malware domain provided by google, only actual embeds.
2. Trusted Domains. So it does not waste computing resources.
3. Self-promo/spam check.
4. Toxic check. Use Leet Speach to further test. 
  - Less toxic way of usage: e.g.  <details><summary>Profanity</summary>* The movie was ass.
  - More toxic way of usage: e.g.  <details><summary>Profanity</summary>* You're an 455.