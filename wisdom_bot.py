import simplejson as json
import praw
import re
import time

from random import choice
from prawcore.exceptions import PrawcoreException as APIException # PRAW API exception handlers

class WisdomBot:

  def __init__(self):
    with open('settings/environment.txt') as environment_file:
      self.environment = environment_file.read().strip()

    self.reddit = praw.Reddit(site_name='wisdom') # site name defines reddit variables from praw.ini
    with open('settings/subreddits.json') as subreddits_file:
      subs = json.load(subreddits_file)[self.environment]
      self.subreddits = '+'.join([sub['name'] for sub in subs]) # get '+'-separated list of subreddits
                                                                # '/r/WOT+wetlanderhumor' works
    with open('settings/keywords.json') as keywords_file:
      self.keywords = json.load(keywords_file) # create the list of keywords to listen for in comments

    with open('data/answered') as answered_file:
      self.answered_comments = answered_file.read().split('\n') # don't reply to the same comment more than once

    with open('data/blocked_users') as blocked_file:
      self.blocked_users = blocked_file.read().split('\n') # don't reply to users who don't want replies

    with open('data/quotes.json') as quote_file:
      self.quotes = json.load(quote_file) # Dictionary of quotes indexed by spoiler scope

  def log(self, string):
    if self.environment == 'PRODUCTION':
      with open('data/log.txt', 'a') as log_file:
        log_file.write(string + '\n')
    else:
      print(string)

  def get_flair(self, comment):
    if comment.subreddit_name_prefixed.lower() == 'r/wetlanderhumor':
      return 'All Print'
    return comment.submission.link_flair_text

  def register_reply(self, comment_id):
    self.answered_comments.append(comment_id)
    with open('data/answered', 'a') as answered_file: # log successful reply so we
      answered_file.write(comment_id + '\n')          # don't reply again

  def get_legal_quote(self, comment):
    flair = self.get_flair(comment)
    try:
      index = self.quotes[flair]['index']
    except KeyError:
      index = 0
    quotes = sum([
                 self.quotes[scope]['quotes'] for scope in self.quotes.keys() if self.quotes[scope]['index'] <= index
              ], [])
    return choice(quotes)

  def get_comment_from_id(self, id):
    return self.reddit.comment(id)


  def wisdom_bot(self):
    while True:
      self.log('\n\nRunning wisdom on reddit.com/r/'+self.subreddits)
      try:
        for comment in self.reddit.subreddit(self.subreddits).stream.comments(): # continuous stream of comments
                                                                            # from chosen subreddits
          comment_text = comment.body
          comment_id = comment.id
          if (any(re.search(keyword, comment_text, re.IGNORECASE) for keyword in self.keywords) and
            comment.author != 'braid_tugger-bot' and
            comment.author not in self.blocked_users and
            comment_id not in self.answered_comments):

            quote = self.get_legal_quote(comment)
            # quote = choice(self.quotes['None']) # Random spiler-free quote
            reply = quote.replace('{user}', '/u/'+comment.author.name) # personalize some quotes
            try:                           # try to reply to the comment
              comment.reply(reply)
            except APIException as e: # in case of too many requests, propagate the error
              raise e                 # to the outer try, wait and try again
            else:
              print(comment_text)
              print(reply)
              self.register_reply(comment_id)
      except KeyboardInterrupt:
        self.log('Logging off reddit..\n')
        break
      except APIException as e: # most likely due to frequency of requests. Wait before retrying
        if 'braid_tugger-bot' in [c.author.name for c in comment.replies]:
          self.register_reply(comment_id)
        self.log(str(e))
        self.log(comment_text)
        time.sleep(10)

if __name__ == '__main__':
  bot = WisdomBot()
  bot.wisdom_bot()
