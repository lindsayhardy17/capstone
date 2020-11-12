import tweepy
import json, csv
import datetime

  
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)


def get_timeline(username):
    print(username)

    startDate = datetime.datetime(2018, 1, 1, 0, 0, 0)
    endDate =   datetime.datetime(2020, 11, 3, 0, 0, 0) # dont forget to change

    tweets = []
    tmpTweets = api.user_timeline(screen_name = username, count = 199)

    for tweet in tmpTweets:
        if tweet.created_at < endDate and tweet.created_at > startDate:
            tweets.append(tweet)
    #print("first ", len(tmpTweets))
    while (len(tmpTweets) > 1) and (tmpTweets[-1].created_at > startDate):
        #print("Last Tweet @", tmpTweets[-1].created_at, " - fetching some more")
        tmpTweets = api.user_timeline(screen_name = username, count = 199, max_id = tmpTweets[-1].id)
        for tweet in tmpTweets:
            if tweet.created_at < endDate and tweet.created_at > startDate:
                tweets.append(tweet)
        #print("in loop: ", len(tmpTweets))
                
    #print("Total tweets downloaded from" + str(username) + "are " + str(len(tweets)))
    return tweets
                
# get all people i follow
follow = []
for user in tweepy.Cursor(api.friends, screen_name="capston94713048").items(1500):
    follow.append(user.screen_name)
print("people im following: " , len(follow))


# make a text file for users you have gone through
f1 = open("following.txt", "r")
complete = f1.readlines()
f1.close()

print("people done: ", len(complete))
new = [x for x in follow if x not in complete]
print("new: " , len(new))

scraped = []
alltweets = []
bad = []
for person in follow:
    test = person + "\n"
    if test not in complete:
        try:
            alltweets.extend(get_timeline(person))
            scraped.append(test)
        except:
            bad.append(test)
            

print("bad: ", bad)
# add the scraped users to the txt file
f1 = open("following.txt", "a")
for user in scraped:
    f1.write(user)
f1.close()

F_NAME = 'tweets9.json'
with open(F_NAME,'a') as f_out:
  
    for status in alltweets:
        json.dump(status._json, f_out)
        f_out.write('\n')



