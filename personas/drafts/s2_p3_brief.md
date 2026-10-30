You write research personas for a marketing-analytics class project. You get real Reddit posts and comments written by members of one online community before a cutoff date. Describe only what the evidence supports. Return a single JSON object and nothing else.

Community segment: Library power users (locked in)
Persona focus: sub-cluster: artist, album, song, artists, apple music, apple, page, liked
Keyword signals in this persona's posts (share of rows): apple music 8%

Below are 40 real posts/comments that make up ONE persona (all dated before 2023-07-21).
Write the persona as one JSON object with exactly these keys:
"name": a plausible first name
"label": 3-6 word descriptive label
"who": 2 sentences, first person, who I am as a Spotify user (plan type, how I listen, what I care about)
"value_for_money": what they say or imply about price, value, free vs paid ("unclear" if the evidence does not say)
"price_sensitivity": "low" | "medium" | "high" | "unclear"
"loyalty": what keeps them on Spotify and what would make them leave
"pain_points": up to 4 short strings
"likes": up to 3 short strings
"alternatives_mentioned": services they name (may be empty)
"tone": one sentence on how they write
"typical_phrases": up to 6 short phrases (max 4 words) in their voice
"evidence_ids": the [numbers] of the 5 posts that best support this profile

Rules: use ONLY the evidence; do not invent facts; mention nothing after 2023-07-21; do NOT predict how they would react to
any price change; no usernames.

EVIDENCE:
[0] (2022-08-03) Hit refresh a few times after you’ve added a few songs. I find mine does this too. Almost like when it doesn’t know what to recommend it defaults to random stuff.
[1] (2022-08-07) Huh last time i had access to that feature it only listed songs i didnt have liked
[2] (2022-08-30) Good question. At the moment I support selected artists by adding to my playlists. It seems the algorithms change sometimes. It's not easy to look behind...
[3] (2022-09-22) Yeah about that. Sometimes I just prefer to add some songs from the radio playlist to the queue or sometimes open the artist's page and add some songs to the queue. Too bad I can't see it that way.
[4] (2022-10-02) I'm no longer able to play songs from artist's popular list. It makes me click through to the album. Is this change affecting anyone else?
[5] (2022-10-09) Removing the ability to like songs with one click, removing the ability to add albums to playlists and removing the ability to add whole albums to liked songs??? Did y’all just sit down at the office and have a conversation about how you can make even more people cancel their subscriptions!?!?!?
[6] (2022-10-09) If they implement this change service-wide, then I'll be transitioning to another music app. There's a clear and specific reason I choose to like certain songs versus entire albums of music. If they get rid of that, and change the likes to some sort of ambiguous, poorly-defined feature, then they're going to lose a lot of people, starting with me.
[7] (2022-11-13) Man at least you have that feature! I have over 2,200 liked songs and would love to get that feature back! It is so convenient at times.
[8] (2022-12-27) Exactly!! Also did anyone else notice that they silently got rid of the feature where a radio plays after the queue is cleared? Now I just get “playing recommended songs for you” and it will play lots of music ive already heard. It also only changes based on genre.
[9] (2022-12-30) I love opening the app and being shown an interesting selection of music, only for it to vanish after clicking one artist.
[10] (2023-01-14) I don't know if I'm just being an idiot but there seem to be a LOT of songs missing from artists. To make it worse entire albums don't seem to show up on the artists page, however if I search for a specific song, the song will (sometimes) be there, listed under an album that Spotify apparently doesn't have. WTF?
[11] (2023-01-19) Yes! My two MAJOR issues: 1. I can’t see an artist’s full song library in a list and play it. I have to play album by album, or play their “This is ____” playlist, which doesn’t have everything. It’s so frustrating, why can’t we just click discography and get an option to view all of their tracks at once? 2. The shuffle is definitely screwed up. I keep hearing repeats within an hour.
[12] (2023-01-22) Oh finally a chance to talk about the changes I’ve HATED 1. I HATE that there’s no separate liked songs thing anymore. Like why is it considered one big playlist that is stupid lol 2. I HATE that all the artists from songs I’ve liked don’t show up. As far as I can tell now I have to specifically follow an artist for them to show up in my artists tab 3. I think recently the whole library thing got 
[13] (2023-01-25) This is the kind of stuff they need to update. Making clean versions more accessible. Alternative versions of songs can be found due to the artist having a clean version.
[14] (2023-02-28) Possibly someone mentioned your album in a YouTube video or showed it in one. This can result in an increase Maybe the algorithm is prioritising your music. Can happen to...
[15] (2023-03-01) IMO this actually sucks. It started playing music I don't listen to at all. Like my top artists are JID, Connor Price, and Twenty One Pilots and it started playing Billy Joel. And even within the artists I like, it plays old music that I don't listen to. Wish I could just add it to my playlist or tell it I hate half the music it is playing.
[16] (2023-03-10) I haven't gotten that update yet, but I've been hearing the rumblings for a week or two. It is pretty dumb, but with the way they've got it set up now, liking a song does nothing but add it to your "liked songs" playlist anymore anyway. It used to be when you went to your library, it had everything you've added to your library. Now, there is no "songs" section because that's what the playlist is f
[17] (2023-03-11) Stop fixing what ain’t broke. Now when I listen to an album I can’t see the songs I’ve already liked - if this feature doesn’t get fixed I will unsubscribe again. I did when you had that horrible experiment a few months ago and only returned it when returned to normal on the mobile app.
[18] (2023-03-11) right? such an asinine update, I listen to a new album almost everyday and i used to be able to easily tell which songs I liked and which I didnt, now its almost like I have to listen to an album all over again cause they removed that feature
[19] (2023-03-11) Yeah, I’m dealing with this and it’s bullshit. For example, I’m listening to a new album, saved some songs, didn’t save others. When looking at the track list of the album, you cannot see any of the songs you saved or did not since there is no heart next to them. You have to click the song, save it to a playlist, and then see if it’s in your “liked” playlist or not. You gotta do this track by trac
[20] (2023-03-12) Interesting. And it’s a Free user! Based on how creepy/angry it was when it launched, I would’ve expected it to complain that it can’t skip songs and wonder why it only sees an un-clickable list of songs on albums and playlists. 😂
[21] (2023-03-15) I think they intentionally make it aggravating for people who just unsubscribed. This happened for about 2 weeks where I click on the song titles and it doesn't let me see the tracks on a playlist shortly after unsubscribing. After some time passes, it'll let you do it again. It's really, really stupid, but it's only for a little bit.
[22] (2023-03-24) This is exactly my issue. Very nice to see at a glance what songs you have liked by an artist or on a playlist. I will never understand these sorts or degenerative updates that simply take features away
[23] (2023-03-26) You're probably right. They probably don't care that some users don't like it. I'm debating if I should cancel my subscription and find something else. I just have years of input into my music selection and I really enjoyed the daily mix playlist. I just feel like the front page isn't user friendly and you can't navigate it as easily.
[24] (2023-04-14) This is actually a great feature. I’ve discovered a bunch of songs through it that I added to my liked songs. You should try it before ranting
[25] (2023-04-28) Okay. You don't want to discover new music, that's fine. The next you get one of the "ads" for new music on your music streaming platform click on "learn more" and you can stop them from there.
[26] (2023-05-15) I'm pretty sure they have an algorithm to push certain songs more. I feel my Playlist is much more lively in offline mode.
[27] (2023-05-25) Hate the fact that song radios now don’t show you music based off of said song. It just shows you recommended music that you’ll probably like (when most of said music is in my likes music already.)
[28] (2023-05-31) This drives me crazy. Why is it impossible to see all the songs I have downloaded by an artist? Why would they take away such basic functionality?
[29] (2023-06-02) I hate it, it used to be simple to see which songs you’ve liked without having to go to the artists and dig through the liked songs there. Makes using the discover area difficult too. I just don’t see the need for it
[30] (2023-06-04) What?! This is what I want. Every time I get the same songs. It doesn't matter how many times I skip these songs. I keep on getting the same songs. It sucks I have to actually play an artist's profile to avoid it.
[31] (2023-06-21) Yeah just noticed I got it the other day. Honestly OG pandora from like a decade ago had more features than this. There's no way to select why you like something or see why the songs are being chosen and the only interactive option is to skip. Kinda lame.
[32] (2023-06-23) yeah, it's really convenient, I'll try. it turns out that you subscribe even to artists who have added only 2-3 songs, right?
[33] (2023-06-27) You said it. I f-u-c-k-i-n-g hate the side panel popping up whenever playing songs, especially infuriating when you're browsing to look for new artists. Think this is the first time I've even considered ending the decade long subscription and changing platforms.
[34] (2023-07-03) Why is the songs lacking an extremely basic feature? This is something that has been annoying me for years. When I search for any artist and navigate to the Songs tab, it brings up all their most popular songs (usually), and I select any of them, why does it not play the next song on that list once the selected song has finished playing?? And go on playing the rest of the songs by that artist? I h
[35] (2023-07-03) Why is the Songs tab lacking an extremely basic feature? This is something that has been annoying me for years. When I search for any artist and navigate to the Songs tab, it brings up all their most popular songs (usually), and I select any of them, why does it not play the next song on that list once the selected song has finished playing?? And go on playing the rest of the songs by that artist?
[36] (2023-07-07) Artist’s songs keep getting automatically added to my library, even though I’m not following them? I am not following Peter Mcpoland, I don’t have any of his music on my playlists, so I have no idea why it keeps getting automatically added to my liked songs. It’s not a huge deal, but I would like to know the reason why it’s happening.
[37] (2023-07-08) Well that's disappointing, it costs money, I don't think it's worth money just to see how many times I've listened to songs, guess I'll have to do without.
[38] (2023-07-10) Yes I am having the same issue and it's very frustrating. I have been using web player since the beginning. Hopefully it's just a bug that is going to be fixed soon and not a system update feature. Can anyone confirm that they can play a specific song in an album page for a free subscription?
[39] (2023-07-20) I'm probably the only person in the world that wants this feature...but if there's any way to show artists that you follow, but don't have any songs saved for...that would be awesome.