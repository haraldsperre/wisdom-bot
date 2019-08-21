import simplejson as json
import praw
import re
import time

from random import choice
from prawcore.exceptions import PrawcoreException as APIException # PRAW API exception handlers

ENVIRONMENT = 'test'

reddit = praw.Reddit(site_name='wisdom')

with open('settings/subreddits.json') as subreddits_file:
  subs = json.load(subreddits_file)[ENVIRONMENT]
  subreddits = '+'.join([sub['name'] for sub in subs])

with open('settings/keywords.json') as keywords_file:
  keywords = json.load(keywords_file)

with open('data/answered') as answered_file:
  answered_comments = answered_file.read().split('\n')

with open('data/quotes.json') as quote_file:
  quotes = json.load(quote_file)

while True:
  try:
    for comment in reddit.subreddit(subreddits).stream.comments():
      if not type(comment) is praw.models.reddit.comment.Comment:
        continue
      comment_text = comment.body
      comment_id = comment.id

      if (any(re.match(keyword, comment_text, re.IGNORECASE) for keyword in keywords) and
        comment.author != 'braid_tugger-bot' and
        comment_id not in answered_comments):

        quote = choice(quotes['None'])
        try:
          comment.reply(quote)
        except APIException as e:
          raise e
        else:
          print("success")
          print(comment_text)
          with open('data/answered', 'a') as answered_file:
            answered_file.write(comment_id + '\n')
  except KeyboardInterrupt:
    print('Logging off reddit..')
    break
  except APIException as e:
    print(e)
    print(comment_text)
    time.sleep(10)


def yield_comments_from_post(post):
  if post.comments is callable:
    for comment in post.comments():
      yield comment
    else:
      for comment in post.comments.list():
        yield comment
