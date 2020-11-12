import tweepy
  
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)


# using this to follow all members of lists

list_id = 5057137

    
# fetching the members 
members = api.list_members(list_id = list_id) 
  
# printing the member screen names 
for member in members:

    member.follow()


# do later - > dont tread on me
