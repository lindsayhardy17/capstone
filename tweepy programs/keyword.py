import tweepy
import json, csv
import datetime

  
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

"""
def find_key():
    startDate = datetime.datetime(2020, 11, 1, 0, 0, 0)
    tweets = []
    tmpTweets = api.home_timeline(since ='2020-11-01', count = 199)
    for tweet in tmpTweets:
        if "protest" in tweet.text or "rally" in tweet.text:
            tweets.append(tweet)

    while (len(tmpTweets) > 1) and (tmpTweets[-1].created_at > startDate):

        tmpTweets = api.home_timeline(since ='2020-11-01', count = 199, max_id = tmpTweets[-1].id)
        
        for tweet in tmpTweets:
            if "protest" in tweet.text or "rally" in tweet.text:
                tweets.append(tweet)

    return tweets


"""

scrape = []
search_words = "protest OR rally"
date_since = '2020-11-01'
# originally tried home_timeline
tweets = tweepy.Cursor(api.search, q=search_words, lang="en", since=date_since).items(5)
for tweet in tweets:
    if "protest" in tweet.text or "rally" in tweet.text:
        scrape.append(tweet)
        
print(len(scrape) , " tweets found!")
F_NAME = 'keyword.json'
with open(F_NAME,'a') as f_out:
  
    for status in scrape:
        json.dump(status._json, f_out)
        f_out.write('\n')
"""
scrape = find_key()


"""
