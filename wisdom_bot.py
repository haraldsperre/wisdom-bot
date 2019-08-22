import simplejson as json
import praw
import re
import time

from random import choice
from prawcore.exceptions import PrawcoreException as APIException # PRAW API exception handlers

ENVIRONMENT = 'production' # 'test' = testingground4bots, 'production' = WoT subreddits

reddit = praw.Reddit(site_name='wisdom') # site name defines reddit variables from praw.ini

with open('settings/subreddits.json') as subreddits_file:
  subs = json.load(subreddits_file)[ENVIRONMENT]
  subreddits = '+'.join([sub['name'] for sub in subs]) # get '+'-separated list of subreddits
                                                       # '/r/WOT+wetlanderhumor' works

with open('settings/keywords.json') as keywords_file:
  keywords = json.load(keywords_file) # create the list of keywords to listen for in comments

with open('data/answered') as answered_file:
  answered_comments = answered_file.read().split('\n') # don't reply to the same comment more than once

with open('data/quotes.json') as quote_file:
  quotes = json.load(quote_file) # Dictionary of quotes indexed by spoiler scope

while True:
  print('Running wisdom on reddit.com/r/'+subreddits)
  try:
    for comment in reddit.subreddit(subreddits).stream.comments(): # continuous stream of comments
                                                                   # from chosen subreddits
      comment_text = comment.body
      comment_id = comment.id
      if (any(re.search(keyword, comment_text, re.IGNORECASE) for keyword in keywords) and
        comment.author != 'braid_tugger-bot' and
        comment_id not in answered_comments):

        quote = choice(quotes['None']) # Random spiler-free quote
        try:                           # try to reply to the comment
          comment.reply(quote.replace("{user}", "/u/"+comment.author.name))
        except APIException as e: # in case of too many requests, propagate the error
          raise e                 # to the outer try, wait and try again
        else:
          print(comment_text)
          print(quote)
          with open('data/answered', 'a') as answered_file: # log successful reply so we
            answered_file.write(comment_id + '\n')          # don't reply again
  except KeyboardInterrupt:
    print('Logging off reddit..')
    break
  except APIException as e: # most likely due to frequency of requests. Wait before retrying
    print(e)
    print(comment_text)
    time.sleep(10)
