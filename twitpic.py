def image(url, size = 'full'):
  id = url.split('/')[-1]
  return "http://twitpic.com/show/%s/%s" % (size, id)
