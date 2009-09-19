import wsgi_runner, pyt, logging, urllib
import models, twitter, XMLData


def snarge(user, passwd, hashtag, step, post):
  if step < 0: return 3, "Step %d cannot be negative" % step

  scast = models.snargecasts(user, hashtag)
  if len(scast) == 0: return 1, "No such snargecast"
  if len(scast) != 1: return 2, "More than one snargecast for user with this hashtag"

  scast = scast[0]
  if step >= len(scast.tweet_stream): return 4, "Step %d is past the end of the stream" % step

  if post: 
    resp = twitter.post(user, passwd, scast.tweet_stream[step])
    if resp: return 0, resp.content
    return 5, "Post to twitter failed"
    
  text = scast.tweet_stream[step]
  message = XMLData.DictToXMLData({}, "status")
  message.text = text
  return 0, message.toxml()

application = pyt.WSGIApplication('snarge.pyt', \
  {'snarge':snarge,
   'unquote':urllib.unquote
  })
def main(): wsgi_runner.run(application)
if __name__ == "__main__": main()
