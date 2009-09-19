<HTML>
<[exec

user = request.get('user')
passwd = request.get('passwd')
hashtag = request.get('hashtag')
pics = request.get_all('pic')
scast = None

if user and len(user):
  scast = create(user, passwd, hashtag, pics)

]>
<HEAD>
<TITLE>
Create a SnargeCast
</TITLE>
</HEAD>
<BODY>
<[if user]>
%(user)s<br>
%(hashtag)s<br>
%(pics)s<br>
<[end]>
<[if scast is not None]>
<p>
<h3>%(scast.hash_tag)</h3>
<[list]>
<img src="%(pic)s"><br>
<[for pic in scast.twit_pics]>
</p>
<[end]>

<p>
<FORM ACTION="create" METHOD="POST"/>
Twitter Username: <INPUT NAME="user" TYPE=TEXT><br>
Twitter Password: <INPUT NAME="passwd" TYPE=PASSWORD><br>
Hash Tag: <INPUT NAME="hashtag" TYPE=TEXT><br>
Pic 1: <INPUT NAME="pic" TYPE="TEXT"><br>
Pic 2: <INPUT NAME="pic" TYPE="TEXT"><br>
Pic 3: <INPUT NAME="pic" TYPE="TEXT"><br>
<INPUT TYPE=SUBMIT>
</FORM>
</p>
</BODY>
</HTML>
