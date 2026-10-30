OUTPUT FILE: eval_2023/labels/out/batch_10.json

Task: you are labeling real Reddit posts/comments written in the two weeks after Spotify announced a US Premium
price increase (Individual $9.99 -> $10.99, Duo $12.99 -> $14.99, Family $15.99 -> $16.99, Student $4.99 -> $5.99).
Each row shows the thread title it was posted in, then the text. Label what the WRITER says, not what the thread says.

For every row write one JSON object with exactly these keys:
  "uid": copy the row's uid exactly
  "relevant": true if the writer is reacting to or discussing the price increase (directly or clearly by context), else false
  "sentiment": the writer's feeling about the price increase / Spotify, one of ['very_negative', 'negative', 'neutral', 'positive']
  "action": one of ['cancel', 'switch', 'downgrade', 'complain', 'accept', 'ignore', 'none']
      (cancel = will cancel Premium / go free with no named alternative; switch = will move to a named competitor; downgrade = moves to a cheaper plan or tier; complain = unhappy but staying; accept = fine with it or defends Spotify; ignore = does not care / indifferent; none = no stance or intention stated: a question, information, a joke with no stance)
      Use "complain" for negative comments that do not say they will leave. Use "accept" for defending the price or
      saying they will keep paying. Only use cancel/switch/downgrade when the writer says they will or did do it.
  "switch_to": the service named if action is "switch", else null
  "themes": 0-3 items from this list only: ['greed_corporate', 'artist_pay', 'still_good_value', 'inflation_expected', 'competitor_comparison', 'plan_cost', 'lossless_missing', 'podcast_audiobook_spending', 'app_quality_ui', 'ads_free_tier', 'affordability', 'piracy']
Theme meanings: {"greed_corporate": "Spotify/executives are greedy, profit over users", "artist_pay": "artists/royalties, will artists get more money", "still_good_value": "still worth it / cheap for what you get", "inflation_expected": "inflation, overdue, other services already raised prices", "competitor_comparison": "compares to Apple Music, YouTube Music, Tidal, Amazon etc.", "plan_cost": "Family, Duo or Student plan cost specifically", "lossless_missing": "paying more but still no HiFi/lossless", "podcast_audiobook_spending": "money wasted on podcasts/audiobooks/Rogan instead of music", "app_quality_ui": "app getting worse, UI redesign, bugs, features removed", "ads_free_tier": "ads, free tier, going back to free", "affordability": "personal budget, can't afford, cost of living", "piracy": "piracy or downloading instead"}
If relevant is false, still fill the other keys (use "none" and [] when nothing applies).

Write ONE JSON array (one object per row, same order) to the output file. Valid JSON only, no markdown fences.

ROWS (21):
[uid=comment:jt98f10] (thread: Spotify Officially Hikes Prices of Premium Plans) I pay. I love music too much to have my vibes interrupted by commercials. I listen to music for large portions of nearly every day. One extra dollar isn’t the end of the world. Still lame and unnecessary, but I’m not gonna freak out about it because music is already undervalued anymore. It’s disposable, and as a musician myself, it’s heartbreaking. I know the extra money isn’t actually gonna go to the artists, but I also collect vinyl, and I’ve certainly bought my share of cds back in the day, not to mention shirts and going to tons of shows. I wish there was a better way to directly support a
[uid=comment:jtabwc1] (thread: Spotify Officially Hikes Prices of Premium Plans) You used to be able to do that, you can't now.
[uid=comment:jt9gd08] (thread: Spotify Officially Hikes Prices of Premium Plans) You give them time (ads) which is as valuable as money.
[uid=comment:jte7e0z] (thread: Spotify Officially Hikes Prices of Premium Plans) Came here to say this. I pay 10 bucks a month for YouTube premium and music combined, which is a great deal.
[uid=comment:jtbbtud] (thread: Spotify Officially Hikes Prices of Premium Plans) first they added local taxes, then got rid of student from what I can tell, then they upped this by a dollar but ig we should be thankful it's only a dollar in this economy
[uid=comment:jtbhzip] (thread: Spotify Officially Hikes Prices of Premium Plans) It won't really happen again in significant ways, just like actors and writers won't get good residuals for streaming shows or movies ever again. If song artists and actors want good residuals than they'll have to sell cd's, records, or be on sydicated shows or frequent old movie features on cable or broadcast TV where advertisers pay up for commercials.
[uid=comment:jt8lpas] (thread: Spotify Officially Hikes Prices of Premium Plans) Been on Spotify since 2009, and never given them money and it will definitely continue
[uid=comment:jteul6q] (thread: Price increase is rediculous) Your submission was automatically removed because i.redd.it is not an approved site. Please post a Text Post, Playlist or head over to /r/truespotify. /r/spotify does not allow image posts. Thanks *I am a bot, and this action was performed automatically. Please [contact the moderators of this subreddit](/message/compose/?to=/r/spotify) if you have any questions or concerns.*
[uid=comment:jtaenuo] (thread: Price increase again‼️) Your submission was automatically removed because i.redd.it is not an approved site. Please post a Text Post, Playlist or head over to /r/truespotify. /r/spotify does not allow image posts. Thanks *I am a bot, and this action was performed automatically. Please [contact the moderators of this subreddit](/message/compose/?to=/r/spotify) if you have any questions or concerns.*
[uid=comment:jthbnov] (thread: Malaysia Escapes Spotify Premium Price Hike) YT music definitely better, since there is a lot old vid that not available on Spotify.
[uid=comment:jtd0u55] (thread: Malaysia Escapes Spotify Premium Price Hike) Sure hope it stays that way. Been loving the fact that i can listen to a lot of weeb music on spotify now
[uid=comment:jtbhpp6] (thread: Spotify Officially Hikes Prices of Premium Plans) Literally on the mobile app for it, in my playlist, searching songs right now. You just scroll up in your playlist.
[uid=comment:jtaml4b] (thread: Spotify Officially Hikes Prices of Premium Plans) YouTube music is actually really good if you’re looking for an alternative. Way more song’s available due to their licensing
[uid=comment:jtajvk2] (thread: Spotify Officially Hikes Prices of Premium Plans) I imagine it does seem pretty shit if you don’t know how to work it.
[uid=comment:jtajcbd] (thread: Spotify Officially Hikes Prices of Premium Plans) You can, that's great, I can't, I'm not the only one, their mobile app is garbage.
[uid=comment:jtd7buf] (thread: Malaysia Escapes Spotify Premium Price Hike) Yeah spotify is GOAT in recommending music next to Instagram
[uid=comment:jtccnsy] (thread: Spotify Officially Hikes Prices of Premium Plans) I hate to break it to you but this is user error
[uid=comment:jtafyz0] (thread: Spotify Officially Hikes Prices of Premium Plans) On what platform? I'm using it on PC at the moment, post-update and i can still search through playlists.
[uid=comment:jta5f8z] (thread: Spotify Officially Hikes Prices of Premium Plans) I can't even search for fucking songs in my own Playlist, Spotify is garbage.
[uid=comment:jta6m7o] (thread: Spotify Officially Hikes Prices of Premium Plans) You can, scroll to the top then you can pull down a search bar
[uid=comment:jtcxoc8] (thread: Spotify Officially Hikes Prices of Premium Plans) Do non iphone users really pay for premium plan?
