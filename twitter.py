import url, base64

update_url = "https://twitter.com/statuses/update.xml"

def post(user, passwd, status):
  data= {'status' : status, 'source' : "SnargeCast"}
  auth = base64.encodestring('%s:%s' % (user, passwd))[:-1]
  headers = {'Authorization': "Basic %s" % auth} 
  try: resp = url.fetch(update_url, headers = headers, data = data)
  except url.HTTPError: resp = None
  return resp

if __name__ == "__main__":
  import sys
  if len(sys.argv) < 3:
    print "Usage: username password status"
    sys.exit(0)

  resp = post(sys.argv[1], sys.argv[2], sys.argv[3])

  print resp.status_code
  print resp.headers
  print resp.content
