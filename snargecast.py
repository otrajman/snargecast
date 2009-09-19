import wsgi_runner, pyt, logging, urllib
import models, twitpic

application = pyt.WSGIApplication('snargecast.pyt', \
  {'snargecasts':models.snargecasts,
   'unquote':urllib.unquote,
   'image':twitpic.image
  })
def main(): wsgi_runner.run(application)
if __name__ == "__main__": main()
