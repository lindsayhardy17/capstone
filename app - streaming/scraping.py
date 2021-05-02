import settings2 # Import related setting constants from settings.py
import re
import tweepy
import psycopg2
import json
import os
import sys
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.pipeline import make_pipeline

# set up carmen library for locations
#!python setup.py install
from carmen import carmen
resolver = carmen.get_resolver()
resolver.load_locations()

# deploy our classifier
with open('text_classifier-1', 'rb') as training_model:
    model = pickle.load(training_model)

def flatten_tweets(tweet):
    """ Flattens out tweet dictionaries so relevant JSON is
        in a top-level dictionary. """
 
    tweet_obj = tweet
    ''' User info'''
    # Store the user screen name in 'user-screen_name'
    tweet_obj['user-screen_name'] = tweet_obj['user']['screen_name']
        
    # Store the user location
    tweet_obj['user-location'] = tweet_obj['user']['location']
        
    # Store number of retweets
    tweet_obj['retweet_number'] = tweet_obj['retweet_count']
    
    # Store number of favorites
    tweet_obj['favorite_number'] = tweet_obj['favorite_count']
        
    # Store hashtags
    if len(tweet_obj['entities']['hashtags']) != 0:
        tweet_obj['hashtags'] = []
        for x in range(len(tweet_obj['entities']['hashtags'])):
            tweet_obj['hashtags'].append(tweet_obj['entities']['hashtags'][x]['text'])
    if len(tweet_obj['entities']['hashtags']) == 0:
        tweet_obj['hashtags'] = 'None'
        
    # Store date
    tweet_obj['date'] = tweet_obj['created_at']
        
    #new location
    tweet_obj['location1'] = resolver.resolve_tweet(tweet_obj)
    
    ''' Text info'''
    # Check if this is a 140+ character tweet
    if 'extended_tweet' in tweet_obj:
         # Store the extended tweet text in 'extended_tweet-full_text'
        tweet_obj['extended_tweet-full_text'] = tweet_obj['extended_tweet']['full_text']
    if 'quoted_status' in tweet_obj:
            # Store the retweet user screen name in
            #'retweeted_status-user-screen_name'
        tweet_obj['quoted_status-user-screen_name'] =  tweet_obj['quoted_status']['user']['screen_name']

            # Store the retweet text in 'retweeted_status-text'
        tweet_obj['quoted_status-text'] = tweet_obj['quoted_status']['text']
    
        if 'extended_tweet' in tweet_obj['quoted_status']:
                # Store the extended retweet text in
                #'retweeted_status-extended_tweet-full_text'
            tweet_obj['quoted_status-extended_tweet-full_text'] = tweet_obj['quoted_status']['extended_tweet']['full_text']
        
        ''' Place info'''
    if 'place' in tweet_obj:
            # Store the country code in 'place-country_code'
        tweet_obj['place-country'] = 'None'
        tweet_obj['place-country_code'] = 'None'
        try:
            tweet_obj['place-country'] = tweet_obj['place']['country']
                
            tweet_obj['place-country_code'] = tweet_obj['place']['country_code']
                
            tweet_obj['location-coordinates'] = tweet_obj['place']['bounding_box']['coordinates']
        except: pass
            
        
    return tweet_obj
    
    
def protest(text,hashtag):
    """ boolean filter to be used in our classifier """
    if (len(re.findall(r'\bmarch', text)) != 0) | (len(re.findall(r'\bprotest', text)) != 0) | (len(re.findall(r'\brally', text)) != 0) | (len(re.findall(r'\bgather', text)) != 0) | (len(re.findall(r'\bsit-in', text)) != 0) | (len(re.findall(r'\bcrowd', text)) != 0) | (len(re.findall(r'\briot', text)) != 0) | (len(re.findall(r'\bcome out', text)) != 0) | (len(re.findall(r'\btake to the streets', text)) != 0) | (len(re.findall(r'\bstrik', text)) != 0) | (len(re.findall(r'\bdemonstrat', text)) != 0):
        if ('march' in text) | ('marching' in text) | ('marches' in text) & ('meet up' not in text) & ('protest' not in text) & ('rally' not in text) & ('gathering' not in text) & ('sit-in' not in text) & ('gather' not in text) & ('crowd' not in text) & ('riot' not in text) & ('come out' not in text) & ('take to the streets' not in text) & ('strik' not in text) & ('demonstrat' not in text):
            if (len(re.findall(r'\bin march', text)) != 0) | (len(re.findall(r'\bon march', text)) != 0):
                return 0
            return 1
        if (len(re.findall(r'\bprotest', text)) != 0):
            return 1
        if (len(re.findall(r'\brally', text)) != 0) & (len(re.findall(r'\bmarch', text)) == 0) & (len(re.findall(r'\bprotest', text)) == 0) & (len(re.findall(r'\bgather', text)) == 0) & (len(re.findall(r'\bsit-in', text)) == 0) & (len(re.findall(r'\bcrowd', text)) == 0) & (len(re.findall(r'\briot', text)) == 0) & (len(re.findall(r'\bcome out', text)) == 0) & (len(re.findall(r'\btake to the streets', text)) == 0) & (len(re.findall(r'\bstrik', text)) == 0) & (len(re.findall(r'\bdemonstrat', text)) == 0):
            return 1
        if (len(re.findall(r'\bgather', text)) != 0) & (len(re.findall(r'\brally', text)) != 0) & (len(re.findall(r'\bmarch', text)) == 0) & (len(re.findall(r'\bprotest', text)) == 0) & (len(re.findall(r'\bsit-in', text)) == 0) & (len(re.findall(r'\bcrowd', text)) == 0) & (len(re.findall(r'\briot', text)) == 0) & (len(re.findall(r'\bcome out', text)) == 0) & (len(re.findall(r'\btake to the streets', text)) == 0) & (len(re.findall(r'\bstrik', text)) == 0) & (len(re.findall(r'\bdemonstrat', text)) == 0):
            if (len(re.findall(r'\bdozen', text)) != 0) |(len(re.findall(r'\blarge', text)) != 0) |(len(re.findall(r'\bthousand', text)) != 0) | (len(re.findall(r'\bpolice', text)) != 0) | (len(re.findall(r'\bhundreds', text)) != 0) | (len(re.findall(r'\bpeople', text)) != 0) | (len(re.findall(r'\+', text)) != 0) | (len(re.findall(r'\bactivist', text)) != 0) | (len(re.findall(r'\bagainst', text)) != 0):
                return 1
            return 0
        if (len(re.findall(r'\bsit-in', text)) != 0) & (len(re.findall(r'\bgather', text)) != 0) & (len(re.findall(r'\brally', text)) != 0) & (len(re.findall(r'\bmarch', text)) == 0) & (len(re.findall(r'\bprotest', text)) == 0) & (len(re.findall(r'\bcrowd', text)) == 0) & (len(re.findall(r'\briot', text)) == 0) & (len(re.findall(r'\bcome out', text)) == 0) & (len(re.findall(r'\btake to the streets', text)) == 0) & (len(re.findall(r'\bstrik', text)) == 0) & (len(re.findall(r'\bdemonstrat', text)) == 0):
            return 1
        if (len(re.findall(r'\bcrowd', text)) != 0) & (len(re.findall(r'\bsit-in', text)) != 0) & (len(re.findall(r'\bgather', text)) != 0) & (len(re.findall(r'\brally', text)) != 0) & (len(re.findall(r'\bmarch', text)) == 0) & (len(re.findall(r'\bprotest', text)) == 0) & (len(re.findall(r'\briot', text)) == 0) & (len(re.findall(r'\bcome out', text)) == 0) & (len(re.findall(r'\btake to the streets', text)) == 0) & (len(re.findall(r'\bstrik', text)) == 0) & (len(re.findall(r'\bdemonstrat', text)) == 0):
            if (len(re.findall(r'\bform', text)) != 0) | (len(re.findall(r'\blarge', text)) != 0) | (len(re.findall(r'\bpeople', text)) != 0) | (len(re.findall(r'\boutside', text)) != 0) | (len(re.findall(r'\bsupport of', text)) != 0) | (len(re.findall(r'\bsupporting', text)) != 0) | (len(re.findall(r'\bfighting for', text)) != 0) | (len(re.findall(r'\bchant', text)) != 0) | (len(re.findall(r'\bdisperse', text)) != 0) | (len(re.findall(r'\bpolice', text)) != 0) | (len(re.findall(r'\bofficer', text)) != 0) | (len(re.findall(r'\bbig', text)) != 0) | (len(re.findall(r'\bhuge', text)) != 0):
                return 1
            return 0
        if (len(re.findall(r'\briot', text)) != 0) & (len(re.findall(r'\bcrowd', text)) != 0) & (len(re.findall(r'\bsit-in', text)) != 0) & (len(re.findall(r'\bgather', text)) != 0) & (len(re.findall(r'\brally', text)) != 0) & (len(re.findall(r'\bmarch', text)) == 0) & (len(re.findall(r'\bprotest', text)) == 0) & (len(re.findall(r'\bcome out', text)) == 0) & (len(re.findall(r'\btake to the streets', text)) == 0) & (len(re.findall(r'\bstrik', text)) == 0) & (len(re.findall(r'\bdemonstrat', text)) == 0):
            return 1
        if (len(re.findall(r'\bcome out', text)) != 0) & (len(re.findall(r'\briot', text)) != 0) & (len(re.findall(r'\bcrowd', text)) != 0) & (len(re.findall(r'\bsit-in', text)) != 0) & (len(re.findall(r'\bgather', text)) != 0) & (len(re.findall(r'\brally', text)) != 0) & (len(re.findall(r'\bmarch', text)) == 0) & (len(re.findall(r'\bprotest', text)) == 0) & (len(re.findall(r'\btake to the streets', text)) == 0) & (len(re.findall(r'\bstrik', text)) == 0) & (len(re.findall(r'\bdemonstrat', text)) == 0):
            return 0
        if (len(re.findall(r'\btake to the streets', text)) != 0):
            return 1
        if (len(re.findall(r'\bstrik', text)) != 0):
            return 1
        if (len(re.findall(r'\bdemonstrat', text)) != 0):
            return 1
        return 1
    elif('protest' in hashtag) | ('riot' in hashtag) | ('march' in hashtag):
        if ('protest' in hashtag):
            return 1
        if ('riot' in hashtag) & ('protest' not in hashtag) & ('march' not in hashtag):
            if ('patriot' in hashtag) | ('patriots' in hashtag) | ('marriott' in hashtag) | ('pastriot' in hashtag) | ('detroit' in hashtag):
                return 0
            return 1
        if ('march' in hashtag):
            return 1
    else:
        return 0
        

none = type(None)

def location2(place):
    """ carmen function to get location """
    if type(place) != none:
        return place
    else:
        return 'no'
    
def city1(place):
    """ find city for carmen """
    if type(place) != none:
        if 'city' in place:
            place2 = place.replace("\'", "")
            place3 = place.replace("\'", "")
            lst = re.split('=|,', place3)
            ind = lst.index(' city')
            c2 = lst[ind+1]
            return c2
        else:
            return None
    else:
        return None
    
def state1(place):
    """ find state for carmen """
    if type(place) != none:
        if 'state' in place:
            place2 = place.replace("\'", "")
            place3 = place.replace("\'", "")
            lst = re.split('=|,', place3)
            ind = lst.index(' state')
            s2 = lst[ind+1]
            return s2
        else:
            return None
    else:
        return None
        
        
class MyStreamListener(tweepy.StreamListener):
    """
    Listen for tweets with our keywords and decide which ones to store.
    """
    
    def on_status(self, status):
        """ Extract info from tweets """

        tweet = flatten_tweets(status._json)
        
        # deal with text in Extended tweets
        if 'extended_tweet' in tweet:
            text = tweet['extended_tweet-full_text']
            #rt_user_screen_name = tweet['quoted_status-user-screen_name']
        elif 'quoted_status' in tweet:
            if 'extended_tweet' in tweet['quoted_status']:
                text = tweet['quoted_status-extended_tweet-full_text']
            else:
                text = tweet['quoted_status-text']
        elif 'retweeted_status' in tweet:
            if 'extended_tweet' in tweet['retweeted_status']:
                text = status.retweeted_status.extended_tweet["full_text"]
            else:
                text = status.retweeted_status.text
        else:
            text = tweet['text'].lower()
            
        # other important info from tweets
        lang = tweet['lang']
        user_location = tweet['user-location']
        place_country = tweet['place-country']
        place_country_code = tweet['place-country_code']
        user_description = status.user.description
        user_screen_name = tweet['user-screen_name']
        retweet_number = tweet['retweet_number']
        hashtags = str(tweet['hashtags'])
        date = status.created_at
        location1 = str(tweet['location1'])
        bf = protest(text, hashtags)
        user_followers_count =status.user.followers_count
        favorite_count = status.favorite_count
        
        # work with lat, long, and locations
        longitude = None
        latitude = None
        if status.coordinates:
            longitude = status.coordinates['coordinates'][0]
            latitude = status.coordinates['coordinates'][1]

            
        if location1 != None:
            loc2 = location2(location1)
            if loc2 != 'no':
                city = city1(loc2)
                state = state1(loc2)
            
        else:
            city = None
            state = None
            
        # if tweet passes the boolean filter, we run it through the classifier
        if bf == 1:
            classifier = int(model.predict([text]))
        else:
            classifier = 0
            
        
        # for space reasons let's only store where the classifier == 1
        # Store all data in Heroku PostgreSQL
        if classifier == 1:
            cur = conn.cursor()
            sql = "INSERT INTO {} (user_followers_count, favorite_count, text, lang, user_location,\
                place_country, place_country_code, user_description, longitude, \
                latitude, user_screen_name, retweet_number,hashtags, date, location1, bf, classifier, city, state) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, \
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)".format(settings2.TABLE_NAME)
            val = (user_followers_count, favorite_count, text, lang, user_location, place_country, place_country_code, user_description, longitude, latitude, \
                user_screen_name, retweet_number,hashtags, date, location1, bf, classifier, city, state)
            cur.execute(sql, val)
            cur.close()
            conn.commit()
    
    def on_error(self, status_code):
        """ Since Twitter API has rate limits, stop srcraping data as it exceed to the thresold. """
        if status_code == 420:
            # return False to disconnect the stream
            return False


# connect to database
DATABASE_URL= 'postgres://ondoitzgzsialv:77775a500c6f7d4db808d3709ccf1c275893ea9b3f631e1ab50687c3638be2ac@ec2-52-1-115-6.compute-1.amazonaws.com:5432/dee64c87blrg0l'
conn = psycopg2.connect(DATABASE_URL, sslmode='require')

'''
# this is only needed when creating the database
cur = conn.cursor()

Check if this table exits. If not, then create a new one.


cur.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = '{0}'
        """.format(settings2.TABLE_NAME))
if cur.fetchone()[0] == 0:
    cur.execute("CREATE TABLE {} ({});".format(settings2.TABLE_NAME, settings2.TABLE_ATTRIBUTES))
    conn.commit()

cur.close()
'''


# connect to Twitter
consumer_key = ""
consumer_secret = ""

access_token = ""
access_token_secret = ""
  
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

# stream tweets using our keywords
myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth = api.auth, listener = myStreamListener)
myStream.filter(languages=["en"], track = settings2.TRACK_WORDS)

# Close the MySQL connection as it finished
# However, this won't be reached as the stream listener won't stop automatically
# Press STOP button to finish the process.
conn.close()
 

