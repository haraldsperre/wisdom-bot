import simplejson as json
import praw
import re

from random import choice

ENVIRONMENT = 'test'

reddit = praw.Reddit(site_name='wisdom')

with open('settings/subreddits.json') as subreddits_file:
  subs = json.load(subreddits_file)[ENVIRONMENT]

with open('settings/keywords.json') as keywords_file:
  keywords = json.load(keywords_file)

with open('data/answered') as answered_file:
  answered_comments = answered_file.read().split('\n')

with open('data/quotes.json') as quote_file:
  quotes = json.load(quote_file)

for subreddit in subs:
  for submission in reddit.subreddit(subreddit['name']).hot():
    for comment in submission.comments.list():
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
        except Exception as e:
          print(e)
          print(submission.title)
          print(comment_text)
        else:
          print("success")
          print(submission.title)
          print(comment_text)
          with open('data/answered', 'a') as answered_file:
            answered_file.write(comment_id + '\n')

def yield_comments_from_post(post):
  if post.comments is callable:
    for comment in post.comments():
      yield comment
    else:
      for comment in post.comments.list():
        yield comment
