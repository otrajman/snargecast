import urllib2, logging
from urllib import urlencode
urllib, DownloadError = None, None
try: 
  from google.appengine.api import urlfetch
  DownloadError = urlfetch.DownloadError
except: 
  import urllib2 as urllib
  DownloadError = urllib.URLError
import mimetools

def server(url):
    type, url = urllib2.splittype(url)
    host, url = urllib2.splithost(url)
    return '%s://%s' % (type, host)

def newPath(url, new):
    return server(url) + new

class fp:
  def __init__(self, text):
    self.text = ["%s: %s" % av for av in text.items()]
    self.line_offset = 0

  def readline(self): 
    if self.line_offset == len(self.text): return None
    self.line_offset += 1
    return self.text[self.line_offset - 1]

class urlfetch_wrapper:
  def __init__(self, response):
    self.response = response
    self.headers = mimetools.Message(fp(response.headers))
    self.content = response.content
    self.status_code = response.status_code

class urllib_wrapper:
  def __init__(self, response):
    self.response = response
    self.headers = response.headers
    self.content = ''.join(response.readlines())
    self.status_code = response.code

def fetch(url, headers={}, data=None, redirect=True):
  method = urlfetch.GET
  if data: 
    data = urlencode(data)
    method=urlfetch.POST
  if urllib is None: 
    response = urlfetch.fetch(url, payload=data, method=method, headers=headers, follow_redirects=redirect)
    return urlfetch_wrapper(response)
  else: 
    request = urllib.Request(url, data)
    [request.add_header(h[0], h[1]) for h in headers]
    response = urllib.urlopen(url)
    return urllib_wrapper(response)
