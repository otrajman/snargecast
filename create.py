import wsgi_runner, pyt, logging
import models

def create(user, passwd, hashtag, pics):
  scast = models.SnargeCast(twitter_user=user, hash_tag = hashtag, twit_pics = pics)
  return scast

application = pyt.WSGIApplication('create.pyt', {'create':create})
def main(): wsgi_runner.run(application)
if __name__ == "__main__": main()
