OUTPUT FILE: sim_2023/out/plain_r5.json

Task: simulate how 26 different members of the r/spotify subreddit would each react to the announcement below. Make them a realistic mix of the community.

ANNOUNCEMENT:
Spotify announcement, July 24, 2023: Spotify is raising the price of Premium in the US and dozens of other markets. US prices: Premium Individual goes from $9.99 to $10.99 per month, Duo from $12.99 to $14.99, Family from $15.99 to $16.99, and Student from $4.99 to $5.99. This is the first US price increase for Premium since Spotify launched in the US in 2011. Spotify says the change will let it keep investing in the product and deliver value to fans and artists. New prices apply to new subscribers now; existing subscribers will be notified by email before their price changes.

Output: write ONE JSON array to the output file, one object per simulated member, with exactly these keys:
  "id": "u1" to "u26"
  "comment": what they would post in an r/spotify thread about this announcement (1-4 sentences, their own voice)
  "sentiment": one of ['very_negative', 'negative', 'neutral', 'positive']
  "action": one of ['cancel', 'switch', 'downgrade', 'complain', 'accept', 'ignore']  (cancel = will cancel Premium / go free with no named alternative; switch = will move to a named competitor; downgrade = moves to a cheaper plan or tier; complain = unhappy but staying; accept = fine with it or defends Spotify; ignore = does not care / indifferent)
  "switch_to": name of the service if action is "switch", else null
  "themes": 1-3 items from this list only: ['greed_corporate', 'artist_pay', 'still_good_value', 'inflation_expected', 'competitor_comparison', 'plan_cost', 'lossless_missing', 'podcast_audiobook_spending', 'app_quality_ui', 'ads_free_tier', 'affordability', 'piracy']
  "intensity": integer 1 (barely cares) to 5 (furious or thrilled)
Theme meanings: {"greed_corporate": "Spotify/executives are greedy, profit over users", "artist_pay": "artists/royalties, will artists get more money", "still_good_value": "still worth it / cheap for what you get", "inflation_expected": "inflation, overdue, other services already raised prices", "competitor_comparison": "compares to Apple Music, YouTube Music, Tidal, Amazon etc.", "plan_cost": "Family, Duo or Student plan cost specifically", "lossless_missing": "paying more but still no HiFi/lossless", "podcast_audiobook_spending": "money wasted on podcasts/audiobooks/Rogan instead of music", "app_quality_ui": "app getting worse, UI redesign, bugs, features removed", "ads_free_tier": "ads, free tier, going back to free", "affordability": "personal budget, can't afford, cost of living", "piracy": "piracy or downloading instead"}
React only as strongly as this person plausibly would; real communities include people who shrug, defend the company,
or just complain and stay. "ignore" and "accept" are valid answers.
