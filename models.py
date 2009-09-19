from google.appengine.ext import db

class SnargeCast(db.Model):
  twitter_user = db.StringProperty(required=True)
  hash_tag = db.StringProperty(required=True)
  twit_pics = db.StringListProperty()
  tweet_stream = db.StringListProperty()
