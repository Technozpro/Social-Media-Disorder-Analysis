# -*- coding: utf-8 -*-
import tweepy
import os
import string

# API Authentication
#Twitter API credentials
consumer_key = "tfH5NYUhi6mln60JDYRuqjrKn"
consumer_secret = "ViD4tBKoqSs5KgTZBoRJIFvsieJ9SevTLQAWWwvvE5K5FJC7kr"
access_key = "1194914448793686018-jpzibdUZ7yJybMK75IgEyt90LOTXc1"
access_secret = "fvT8uV70okmdUcQ8SEGG4PE8jHTI3PMEui6jIxpvZWBtW"

#authorize twitter, initialize tweepy
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth)

# Fetch tweets by username
def getTweets(username,count=300):
    timeline = api.user_timeline(screen_name = username,count=300, tweet_mode='extended',lang = 'en')
    #print(timeline)
    #tweets = [tweet.text.encode('utf-8').translate(None, '!.,?') for tweet in timeline]
    tweets=[]
    for tweet in timeline:
        if (hasattr(tweet, "retweeted_status") and tweet.lang=='en'):
            tweets.append(tweet.retweeted_status.full_text.translate(str.maketrans('','',string.punctuation)))
        elif tweet.lang=='en':
            tweets.append(tweet.full_text.translate(str.maketrans('','',string.punctuation)))	
    '''
    if hasattr(timeline, "retweeted_status"):
	    print("yes")

	    tweets = [tweet.retweeted_status.full_text.translate(str.maketrans('','',string.punctuation)) for tweet in timeline]
    else:
	    tweets = [tweet.full_text.translate(str.maketrans('','',string.punctuation)) for tweet in timeline]							
    '''
    #print(tweets)	
    return tweets

# Remove hashtags, mentions, links
def cleanTweets(tweets):
	clean_data = []
	for tweet in tweets:
	    item = ' '.join(word.lower() for word in tweet.split() \
	    	if not word.startswith('#') and \
	    	   not word.startswith('@') and \
	    	   not word.startswith('http') and \
	    	   not word.startswith('RT'))
	    if item == "" or item == "RT":
	        continue
	    clean_data.append(item)
	#print(clean_data)		
	return clean_data

def getTrainData():
	positives, negatives, traindata = [], [], []
	for filename in os.listdir("train"):
	    if filename == "POSITIVE.txt":
		    with open('train/'+filename) as f:
			    positives = [(tweet, 'pos') for tweet in f.readlines()]
	    if filename == "NEGATIVE.txt":
		    with open('train/'+filename) as f:
			    negatives = [(tweet, 'neg') for tweet in f.readlines()]

	for (words, sentiment) in negatives + positives:
		words_filtered = [e for e in words.split() if len(e) > 2]
		traindata.append((words_filtered, sentiment))

	return traindata

def export(filename, data, p):
    with open(filename, p,encoding="utf8") as output:
    	for line in data:
        	#print(line)			
        	output.write(line+"\n")
