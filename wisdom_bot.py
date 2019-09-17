import simplejson as json
import praw
import re
import time

from random import choice
from prawcore.exceptions import PrawcoreException as APIException # PRAW API exception handlers

ENVIRONMENT = 'production' # 'test' = testingground4bots, 'production' = WoT subreddits

reddit = praw.Reddit(site_name='wisdom') # site name defines reddit variables from praw.ini

def log(string):
  if ENVIRONMENT == 'production':
    with open('data/log.txt', 'a') as log_file:
      log_file.write(string + '\n')
  else:
    print(string)

def register_reply(comment_id):
  with open('data/answered', 'a') as answered_file: # log successful reply so we
    answered_file.write(comment_id + '\n')          # don't reply again
with open('settings/subreddits.json') as subreddits_file:
  subs = json.load(subreddits_file)[ENVIRONMENT]
  subreddits = '+'.join([sub['name'] for sub in subs]) # get '+'-separated list of subreddits
                                                       # '/r/WOT+wetlanderhumor' works

with open('settings/keywords.json') as keywords_file:
  keywords = json.load(keywords_file) # create the list of keywords to listen for in comments

with open('data/answered') as answered_file:
  answered_comments = answered_file.read().split('\n') # don't reply to the same comment more than once

with open('data/blocked_users') as blocked_file:
  blocked_users = blocked_file.read().split('\n') # don't reply to users who don't want replies

with open('data/quotes.json') as quote_file:
  quotes = json.load(quote_file) # Dictionary of quotes indexed by spoiler scope

while True:
  log('\n\nRunning wisdom on reddit.com/r/'+subreddits)
  try:
    for comment in reddit.subreddit(subreddits).stream.comments(): # continuous stream of comments
                                                                   # from chosen subreddits
      comment_text = comment.body
      comment_id = comment.id
      if (any(re.search(keyword, comment_text, re.IGNORECASE) for keyword in keywords) and
        comment.author != 'braid_tugger-bot' and
        comment.author not in blocked_users and
        comment_id not in answered_comments):

        quote = choice(quotes['None']) # Random spiler-free quote
        reply = quote.replace('{user}', '/u/'+comment.author.name) # personalize some quotes
        try:                           # try to reply to the comment
          comment.reply(reply)
        except APIException as e: # in case of too many requests, propagate the error
          raise e                 # to the outer try, wait and try again
        else:
          print(comment_text)
          print(reply)
          register_reply(comment_id)
  except KeyboardInterrupt:
    log('Logging off reddit..\n')
    break
  except APIException as e: # most likely due to frequency of requests. Wait before retrying
    if 'braid_tugger-bot' in [c.author.name for c in comment.replies]:
      register_reply(comment_id)
    log(e)
    log(comment_text)
    time.sleep(10)
