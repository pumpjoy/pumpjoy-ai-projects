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