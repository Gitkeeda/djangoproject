import tweepy
from textblob import TextBlob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import _datetime
import re
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from wordcloud import WordCloud
import json
import csv

from geopy.geocoders import Nominatim

import plotly.express as px

consumer_key = 'rhvoAYliYV5M5NXINAMInoQ6T'
consumer_secret = 'ES2OKGrzd4IkBauB07iP1cG6h3yNeDHzFRxV3mPO8bewAyEDwo'
access_token = '1323580048008376321-jVo4cQMMJdEeVhEss5G0oZP19H9cs1'
access_token_secret = 'RKNzLWq3mAvM3H9LuZ0fx7FsQESkmpTcNUA4bICfuYOcj'

tag = input('\nEnter The Hashtag: ')
ntweets = int(input('Number Of Tweets To Be Analysed(Range[1-10000]): '))
if((ntweets<10000) and (ntweets>0)):
  limit = int(ntweets)
else:
  limit= 500

rts = int(input('\nWant to include retweets in this analysis?(yes=0/no=1): '))
if(rts==0):
  hashtag = tag #+ "-filter:retweets"
else:
  hashtag = tag + "-filter:retweets"

start_date = _datetime.date(2021,2,5)
end_date = _datetime.date(2022,2,12)

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

search = [tweet for tweet in tweepy.Cursor(api.search,q=hashtag,count=1000,
                          since=start_date, until= end_date).items(limit)]


pos = 0
neg = 0
neu = 0
for tweet in search:
    analysis = TextBlob(tweet.text)
    if analysis.sentiment[0]>0:
       pos = pos +1
    elif analysis.sentiment[0]<0:
       neg = neg + 1
    else:
       neu = neu + 1
if((pos != 0) and (neg !=0) and (neu != 0)):
  print("\n\nTweet Sentiment:")
  print("Positive = ", round(pos/(pos+neg+neu)*100, 1), "%  (",pos,"tweets)")
  print("Negative = ", round(neg/(pos+neg+neu)*100, 1), "%  (",neg,"tweets)")
  print("Neutral = ", round(neu/(pos+neg+neu)*100, 1), "%  (",neu,"tweets)")
  
  labels = 'Positive', 'Negative', 'Neutral'
  sizes = [pos, neg, neu]
  colors = ['#ffca3e', '#ff6f50', '#58cced']
  explode = (0.1, 0, 0)
  plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140, textprops={'fontsize':10, 'color':"#0A0A0A", 'style':'oblique', 'weight':'bold'})
  plt.axis('equal')
  plt.show()
  
  
  my_list_of_dicts = []
  for each_json_tweet in search:
    my_list_of_dicts.append(each_json_tweet._json)
    
  with open(tag+'.txt', 'w') as file:
    file.write(json.dumps(my_list_of_dicts, indent=4))
  
  my_demo_list = []
  with open(tag+'.txt', encoding='utf-8') as json_file:
    all_data = json.load(json_file)
    for each_dictionary in all_data:
      tweet_id = each_dictionary['id']
      text = each_dictionary['text']
      user_id = each_dictionary['user']['id']
      user_location = each_dictionary['user']['location']
      created_at = each_dictionary['created_at']
      user_lang = each_dictionary['metadata']['iso_language_code']
      user_imp = each_dictionary['user']['followers_count']
      my_demo_list.append({'created_at': created_at,
                           'tweet_id': str(tweet_id),
                           'user_id': str(user_id),
                           'user_location': str(user_location),
                           'text': str(text),
                           'language':  str(user_lang),
                           'impressions': user_imp
                           })
        
      tweet_dataset = pd.DataFrame(my_demo_list, columns = 
                                   ['created_at', 'tweet_id', 'user_id',
                                    'user_location', 'text', 'language','impressions'
                                    ])


  tweet_dataset.to_csv(tag+'.csv')
  file= open(tag+'.csv')
  reader= csv.reader(file)
  lines = len(list(reader)) - 1

  def remove_pattern(input_txt, pattern):
    r = re.findall(pattern, input_txt)
    for i in r:
      input_txt = re.sub(i, '', input_txt)
      
    return input_txt 
    
  tweet_dataset['text'] = np.vectorize(remove_pattern)(tweet_dataset['text'], "@[\w]*")

  corpus = []
  for i in range(0, lines):
    tweet = re.sub('[^a-zA-Z0-9]', ' ', tweet_dataset['text'][i])
    tweet = tweet.lower()
    tweet = re.sub('rt', '', tweet)
    tweet = re.sub('http', '', tweet)
    tweet = re.sub('https', '', tweet)
    tweet = re.sub('co', '', tweet)
    tweet = tweet.split()
    ps = PorterStemmer()
    tweet = [ps.stem(word) for word in tweet if not word in set(stopwords.words('english'))]
    tweet = ' '.join(tweet)
    corpus.append(tweet)



  df = pd.read_csv(tag+'.csv')
  print("\n\nPotential Impressions : ",df["impressions"].sum())



  print("\n\nVerbal Collection :")  
  #Word Cloud
  all_words = ' '.join([text for text in corpus])
  wordcloud = WordCloud( width=500, height=300, random_state=21, max_words=50 
                        ,background_color="white", max_font_size=110 
                        , collocations=False).generate(all_words)
  plt.figure(figsize=(7, 5))
  plt.imshow(wordcloud)
  plt.axis('off')
  plt.show()



  print("\n\nSample Tweet Map :\n")
  locator = Nominatim(user_agent= "geopy")
  csvFile = open(tag+'_location.csv', 'w')
  csvWriter = csv.writer(csvFile)
  csvWriter.writerow(["Latitude","Longitude", "Location"])
  df = pd.read_csv(tag+".csv", nrows=20)
  loc = df["user_location"]
  for row in loc:
    if(len(str(row)) != 3):
      try:
        location= locator.geocode(row)
        csvWriter.writerow([location.latitude, location.longitude, row ])
      except AttributeError:
        csvWriter.writerow(["",""])
        
  csvFile.close()
  
  twitterly_map = pd.read_csv(tag+"_location.csv")
  fig = px.scatter_mapbox(twitterly_map, lat="Latitude", lon="Longitude", hover_data=["Location"],
                        color_discrete_sequence=["#0a0a0a"], zoom=1, height=700, width= 1000, center= dict(lat=35, lon=7))
  fig.update_layout(mapbox_style="carto-positron")
  fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
  fig.show()

else:
  print("\nEnter a right hashtag")
