from datetime import datetime, timedelta, time
import re, logging, sys

def parseTime(t, fmt):
  try:
    ts = t
    tz = timedelta()
    #timezone
    h,m = 0,0
    plus = t.find('+')
    if plus != -1: 
      t,z = t.split('+')
      col = z.split(':')
      if len(col) == 2: h,m = col
      else: h,m = col[:2],col[2:]
      logging.info('%s %s %s' % (z, h, m))
      #plus means later than GMT, subtract to get to GMT
      tz = timedelta(hours=-int(h), minutes=int(m))
    else:
      x = t.split('-')
      if len(x) == 4: 
        t, z = '-'.join(x[:3]), x[3]
        col = z.split(':')
        if len(col) == 2: h,m = col
        else: h,m = col[:2],col[2:]
        #minus means earlier than GMT, add to get to GMT
        tz = timedelta(hours=int(h), minutes=int(m))

    #microseconds
    dot = t.find('.')
    if dot != -1: 
      t,d = t.split('.')
      tz += timedelta(microseconds=int(d))
  
  except Exception, err:
    exc_info = sys.exc_info()
    raise Exception("Exception %s %s parseTime '%s' '%s' '%s'" % (type(err), err.message, ts, t, fmt)), None, exc_info[2]

  try: return datetime.strptime(t, fmt) + tz
  except ValueError, err:
    exc_info = sys.exc_info()
    raise ValueError("Exception %s %s parseTime '%s' '%s' '%s'" % (type(err), err.message, ts, t, fmt)), None, exc_info[2]


#parse http time
#may not have Z
def p_http(t): 
  from email import Utils
  import time
  tt = Utils.parsedate_tz(t)
  ts = time.mktime(tt[:9])
  utc = 0 #(datetime.utcnow() - datetime.now()).seconds
  if tt[9] is not None: utc += tt[9]
  return datetime.fromtimestamp(ts - utc) 

  #t = t.strip()
  #if len(t.split(' ')) ==  6: return parseTime(t, '%a, %d %b %Y %H:%M:%S %Z')
  #else: return parseTime(t, '%a, %d %b %Y %H:%M:%S')

#parse rss time
#data=Sat Dec 6 06:00:00  fmt=%a, %d %B %Y %H:%M:%S
def p_rss(t): 
  "could be short or long month name with or without time"
  timefmt = ''

  #remove extra spaces
  parts = [p for p in t.strip().split(' ') if len(p)]
  t = ' '.join([u.strip() for u in parts[:5]]).strip()

  #look for dumb format
  if t.find('/') != -1: return parseTime(t, '%Y/%m/%d')

  #remove leading numbers
  t = re.search('\d*(.*)', t).groups()[0]

  #is there time?
  if len(parts) > 4: timefmt = ' %H:%M:%S'

  #try short and long months
  try: return parseTime(t, '%a, %d %b %Y' + timefmt)
  except ValueError: pass
  return parseTime(t, '%a, %d %B %Y' + timefmt)

#parse time for atom
def p_atom(t): 
  if t[-1] == 'Z': t = t[:-1]
  return parseTime(t, '%Y-%m-%dT%H:%M:%S')

#parse iso time
def p_iso(t): return parseTime(t, '%Y-%m-%d %H:%M:%S') 

#parse time for rdf
def p_rdf(t): 
  format = '%Y-%m-%dT%H:%M'
  ts = t.split(':')
  if len(ts) > 2 and ts[1].find('+') == -1 and ts[1].find('-') == -1: format += ':%S'
  return parseTime(t, format)

#parse datehour
def p_datehour(t): return parseTime(t, '%Y%m%d%H')

#format rss time to save as time
def f_item(t): return t.strftime('%a, %d %b %Y %H:%M:%S %Z')

#format long
def f_long(t): return t.strftime('%a, %B %d %Y %H:%M:%S %Z')

#format mysql time
def f_iso(t): return t.strftime('%Y-%m-%d %H:%M:%S')  

#format time for file system
def f_datehour(t): return t.strftime('%Y%m%d%H')

#format time for javascript date parser
def f_date(t): return t.strftime('%Y, %m - 1, %d')

def f_datetime(t): return t.strftime('%Y, %m - 1, %d, %H, %M, %S')

#format http time
def f_http(t): return t.strftime('%a, %d %b %Y %H:%M:%S %Z')

def now(): return datetime.now()

def onehour(): return now() - timedelta(hours=-1)

def fourhour(): return now() - timedelta(hours=-4)

def tomorrow(): return datetime.combine(datetime.now() + timedelta(days=1), time(0,0,0))
