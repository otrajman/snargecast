import os, sys, logging

def write(s): print s

def sr(stat, head): 
  print stat
  print '\n'.join(["%s: %s" % h for f in head.items()])
  print
  return write
 
def run(application):
  try: from google.appengine.ext.webapp.util import run_wsgi_app
  except: 
    environ = os.environ.copy()
    environ['WSGI_INPUT'] = ''
    logging.info('running main')
    application(environ, sr)
  else: 
    logging.info('running wsgi')
    run_wsgi_app(application)
