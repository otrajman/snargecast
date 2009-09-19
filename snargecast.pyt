<HTML>
<[exec

user = request.get('user')
hashtag = request.get('hashtag')

if user: unquote(user)
if hashtag: unquote(hashtag)

scasts = snargecasts(user, hashtag)
]>
<HEAD>
<TITLE>
SnargeCasts
</TITLE>
<BODY>
<[list]>

<p>
<h3>%(scast.hash_tag)s</h3>
<[list]>
<[exec img=image(pic)]>
<a href="%(pic)s"><img border=0 src="%(img)s"></a><br>
<[for pic in scast.twit_pics]>
</p>

<[for scast in scasts]>
</BODY>
</HEAD>
</HTML>
