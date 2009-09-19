<?xml version="1.0"?>
<[exec
WSGI.response_headers['Content-Type'] = 'application/xml'

user = request.get('user')
passwd = request.get('passwd')
hashtag = request.get('hashtag')
step = request.get('step')
post = request.get('post')

code, message = -1, "Missing parameter"

istep = -1
try: istep = int(step)
except: pass

if user and len(user) and \
   hashtag and len(hashtag):
  if passwd is None or len(passwd) == 0: past = None
  code, message = snarge(unquote(user), unquote(passwd), unquote(hashtag), istep, post)
]>
<snarge>
  <step>%(istep)d</step>
<[if code != 0]>
  <error>
    <code>%(code)d</code>
    <message>%(message)s</message>
  </error>
<[else]>
  %(message)s
<[end]>
</snarge>
