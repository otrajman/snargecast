import re, os, sys, bits
import mimetools, logging
from wsgiref import headers

try: import cPickle as pickle
except: import pickle

__version__ = '0.3.1'
__all__ = ['__version__', 'pyt', 'template', 'run']

## Methods ##
def f_text(code, arg, vars):
    "Replace variables in text"
    try: return arg % bits.nested_dict(vars)
    except ValueError, err: raise Exception("Error at %s:\n%s" % (arg, err))
    except TypeError, err: raise Exception("Error at %s:\n%s" % (arg, err))

def f_link(code, arg, vars):
    "Insert a hyper link to the file"
    return '<a href="%s">%s</a>' % (arg, code.run(vars))

def f_embed(code, arg, vars):
    "Embed reference or contents of file"
    return pyt(open('%s/%s' % (os.getcwd(), eval(arg, vars)), 'r').readlines()).run(vars)

def f_exec(code, arg, vars):
    "Execute a command"
    try: exec(arg, vars)
    except Exception, err: #raise err 
      exc_info = sys.exc_info()
      raise Exception("Error %s at %s...:\n%s" % (type(err), arg, err.message)), None, exc_info[2]

def f_list(code, arg, vars):
    "List comprehension, follow with a for var in varlist"
    forcode = code.stack[-1]
    listvar, setvar, condition = forcode.arg
    result = []
    if condition and len(condition): #check here, it's faster than within the loop
        for v in eval(setvar, vars):
            if len(listvar) == 1: vars[listvar[0]] = v
            elif not (isinstance(v, tuple) or isinstance(v, list)): raise ValueError("Cannot unpack %s into %s" % map(repr, (v, listvar)))
            elif len(v) != len(listvar): raise ValueError("Cannot unpack %s into %s" % tuple(map(repr, (v, listvar))))
            else: map(lambda (x,y):vars.__setitem__(x, y), zip(listvar, v))
            if eval(condition, vars): result.append(code.run(vars, -1))
    else:
        for v in eval(setvar, vars):
            if len(listvar) == 1: vars[listvar[0]] = v
            elif not (isinstance(v, tuple) or isinstance(v, list)): raise ValueError("Cannot unpack %s into %s" % (repr(v), repr(listvar)))
            elif len(v) != len(listvar): raise ValueError("Cannot unpack %s into %s" % (repr(v), repr(listvar)))
            else: map(lambda (x,y):vars.__setitem__(x, y), zip(listvar, v))
            result.append(code.run(vars, -1))
    return ''.join(result)

def f_if(code, arg, vars):
    "Conditional evaluation"
    if eval(arg, vars): return code.run(vars, -1)
    else: return code.stack[-1].process(vars)

def f_else(code, arg, vars):
    "Conditional choice"
    if arg and len(arg):
        if eval(arg, vars): return code.run(vars, -1)
        else: return code.stack[-1].process(vars)
    return code.run(vars, -1)

def f_while(code, arg, vars):
    "Repeats expression between while and loop until argument is false"
    results = []
    while eval(arg, vars): results.append(code.run(vars))
    return ''.join(results)

## Loading ##
class pyt_opcode:
    def __init__(self, func = None, arg = None):
        self.func = func
        self.arg = arg
        self.stack = []

    def __repr__(self):
        if self.arg:
            if isinstance(self.arg, list) or isinstance(self.arg, tuple): return '%s %s' % (' '.join(map(str, self.arg)), ' '.join(map(str, self.stack)))
            else: return '%s %s' % (self.arg, ' '.join(map(str, self.stack)))
        return ' '.join(map(str, self.stack))

    def add(self, code): self.stack.append(code)

    def process(self, vars):
        if self.func: return self.func(self, self.arg, vars)
        else: return self.run(vars)

    def run(self, vars, limit = None):
        if limit is not None: return ''.join(filter(None, map(lambda c:c.process(vars), self.stack[:limit])))
        return ''.join(filter(None, map(lambda c:c.process(vars), self.stack)))

def method_arg(arg):
    space = arg.find(' ')
    tab = arg.find('\t')
    newline = arg.find('\n')
    offset = space
    if tab != -1 and tab < offset: offset = tab
    if newline != -1 and newline < offset: offset = newline
    if offset != -1: return arg[:offset].strip(), arg[offset + 1:].strip()
    return arg, ''

def s_link(inst_part, stack):
    if len(inst_part) > 4: #end link
        code = pyt_opcode(f_link, method_arg(inst_part)[1])
        stack[-1].add(code)
        stack.append(code)
    else: #begin link
        code = stack.pop()
        if code.func != f_link: raise Exception("Encountered unexpected link at %s" % code)

def s_embed(inst_part, stack): stack[-1].add(pyt_opcode(f_embed, method_arg(inst_part)[1]))
def s_exec(inst_part, stack): stack[-1].add(pyt_opcode(f_exec, method_arg(inst_part)[1]))

# list
def s_list(inst_parts, stack):
    code = pyt_opcode(f_list, None)
    stack[-1].add(code)
    stack.append(code)

def s_for(inst_part, stack):
    lcode = stack.pop()
    if lcode.func != f_list: raise Exception("Encounted unexpected for at %s" % lcode)

    setcomp = method_arg(inst_part)[1]
    in_offset = setcomp.find(' in ')
    if in_offset == -1: raise Exception("Invalid for statement %s" % inst_part)
    listvar, setvar = setcomp[:in_offset].strip(), setcomp[in_offset + 4:].strip()
    
    #support tuples
    listvar = listvar.strip('()')
    listvar = map(lambda s:s.strip(), listvar.split(','))
    
    condition = None
    if_offset = setvar.find('if')
    if if_offset != -1: setvar, condition = setvar[:if_offset].strip(), setvar[if_offset + 2:].strip()

    code = pyt_opcode(None, (listvar, setvar, condition))
    lcode.add(code)

# if
def s_if(inst_part, stack):
    code = pyt_opcode(f_if, method_arg(inst_part)[1])
    stack[-1].add(code)
    stack.append(code)

def s_else(inst_part, stack):
    if stack[-1].func not in (f_if, f_else): raise Exception("Encounted unexpected else at %s" % stack[-1])
    code = pyt_opcode(f_else, method_arg(inst_part)[1])
    stack[-1].add(code)
    stack.append(code)

def s_end(inst_part, stack):
    code = stack.pop()
    if code.func not in (f_if, f_else): raise Exception("Encounted unexpected end at %s" % code)
    code.add(pyt_opcode(None, None))
    while code.func != f_if: #remove all contiguous elses up to and including the last if
        if len(stack) == 0: raise Exception("Encounted unexpected end at %s" % code)
        code = stack.pop()
        if code.func not in (f_if, f_else): raise Exception("Encounted unexpected end at %s" % code)

def s_while(inst_part, stack):
    code = pyt_opcode(f_while, method_arg(inst_part)[1])
    stack[-1].add(code)
    stack.append(code)

def s_loop(inst_part, stack):
    wcode = stack.pop()
    if wcode.func != f_while: raise Exception("Encounted unexpected loop at %s" % ''.join(map(str, wcode.stack)))

## Parsing ##
functions = {'link':s_link, 'embed':s_embed, 'exec':s_exec, 'list':s_list, 'for':s_for, 'if':s_if, 'else':s_else, 'end':s_end, 'while':s_while, 'loop':s_loop}

class pyt_stack:
    space, percent, psub = re.compile('\ |\t|\n'), re.compile('%([^\(])'), '%%\g<1>'
    def __init__(self, instructions):
        self.code = pyt_opcode()

        stack = [self.code]
        for inst in instructions:
            parts = pyt_stack.space.split(inst)
            if parts[0] in functions: functions[parts[0]](inst, stack)
            else:
                inst = pyt_stack.percent.sub(pyt_stack.psub, inst)
                if len(inst) and inst[0] == '[': inst = '<' + inst
                stack[-1].add(pyt_opcode(f_text, inst))

    def process(self, vars): return self.code.process(vars)

pyt_template = []
inst = re.compile('(?:\<\[)|(?:\]\>)')
class pyt:
    def __init__(self, text = globals()['pyt_template']):
        self.compile(text)

    def compile(self, text):
        if isinstance(text, list): text = ''.join(text)
        if isinstance(text, file): text = ''.join(text.readlines())
        #ignore # on the first line for script support
        if len(text) > 0 and text[0] == '#': 
            newline = text.find('\n')
            if newline != -1: text = text[newline + 1:]
        self.stack = pyt_stack(inst.split(text))

    def save(self, file_path): pickle.dump(self.stack, open(file_path, 'w'))
    def load(self, file_path): self.stack = pickle.load(open(file_path, 'r'))
    def run(self, vars = globals()): return self.stack.process(vars)

def template(text):
    """Sets the template to run"""
    global pyt_template
    pyt_template.append(text)

def run(name, vars = globals()):
    """If run as main, print the resulting string to stdout, otherwise return it."""
    data = pyt().run(vars = vars)
    if name == '__main__': print data
    else: return data

def outputfilter(filter):
    """Implements apache mod_python output filter"""
    globals()['request'] = filter.req
    text = ""
    s = filter.read()
    while s:
        text += s
        s = filter.read()
    filter.write(pyt(text).run())
    filter.close()

def fixup_var(i, v):
  i = i.upper().replace('.', '_')
  return (i, v)

class fp:
  def __init__(self, text):
    self.text = text.split('\n')
    self.line_offset = 0

  def readline(self):
    if self.line_offset == len(self.text): return None
    self.line_offset += 1
    return self.text[self.line_offset - 1]
  

def parseQuery(qs):
  form = {}
  if len(qs) == 0: return form
  try:
    for (a,v) in [q.split('=') for q in qs.split('&')]:
      if a in form:
        w = form[a]
        if isinstance(w, list): w.append(v)
        else: form[a] = [w,v]
      else: form[a] = v
    return form
  except: raise Exception("Malformed query string '%s'" % qs)

def parseValue(val):
  return dict([(x[0], x[1].strip('"')) for x in [h.strip().split('=', 1) for h in val.split(';')] if len(x) == 2])

def parsePost(method, ct, query, msg):
  logging.info('Processing %s %s' % (method, ct))
  values = {}
  if query and len(query): values = parseQuery(query)
  if ct == 'application/x-www-form-urlencoded': values.update(parseQuery(msg))
  if ct.find('multipart/form-data') != -1:
    cth = parseValue(ct)
    mvars = msg.split('--' + cth['boundary'])
    for var in mvars:
      var = var.strip()
      vmsg = mimetools.Message(fp(var))
      if vmsg.has_key('content-disposition'):
        hd = parseValue(vmsg.get('content-disposition'))
        i,p = var.find('\n\n'), 2
        if i == -1: i,p = var.find('\r\n\r\n'), 4
        a,v = hd['name'].strip(), {'filename':hd['filename'],'data':var[i + p:]}
        values[a] = v
  return values

class Request():
  def __init__(self, env):
    self.content_type = ''
    if 'CONTENT_TYPE' in env: self.content_type = env['CONTENT_TYPE']
    self.body = mimetools.Message(env['WSGI_INPUT'])
    self.cookies = {}
    if 'HTTP_COOKIE' in env: self.cookies = parseValue(env['HTTP_COOKIE'])
    self.form = parsePost(env['REQUEST_METHOD'], self.content_type, env['QUERY_STRING'], self.body.fp.read())

  def get(self, att, default=''):
    if att in self.form:
      val = self.form[att]
      if isinstance(val, list): return val[0]
      else: return val
    return default

  def get_all(self, att):
    if att in self.form:
      val = self.form[att]
      if isinstance(val, list): return val
      return [val]
    return []

  def arguments(self): return self.form.keys()

class WSGIApplication():
  """Implements wSGI compatible application
    Argu,enst are the pyt or pyc file and additonal dict of vars"""
  def __init__(self, pyt_file, vars = {}):
    self.status = '200 Ok'
    self.response_headers = headers.Headers([('Content-Type','text/html')])

    self.template = pyt()
    self.vars = {'WSGI':self}
    self.vars.update(vars)
    self.pyt_file = pyt_file
    self.load_template()

  def load_template(self):
    if self.pyt_file.rfind('.ptc') == len(self.pyt_file) - 4:
      try:  self.template.load(self.pyt_file)
      except: self.template.compile(open(self.pyt_file, 'r').readlines())
    else: self.template.compile(open(self.pyt_file, 'r').readlines())
    self.mtime = os.stat(self.pyt_file).st_mtime

  def __call__(self, environ, start_response):
    t_mtime = os.stat(self.pyt_file).st_mtime
    if self.mtime < t_mtime: self.load_template()

    vars = dict([fixup_var(i,v) for (i,v) in environ.items()])
    vars.update(self.vars)
    vars['request'] = Request(vars)

    logging.info("Running %s" % self.pyt_file)
    result = self.template.run(vars)

    write = start_response(self.status, self.response_headers.items())
    write(result)

  def __iter__(self): pass

if __name__ == '__main__':
    import sys, os
    if len(sys.argv) < 2: print 'Usage: %s template_file' % os.path.split(sys.argv[0])[1]
    else:
        p = pyt()
        if sys.argv[1].rfind('.ptc') == len(sys.argv[1]) - 4:
            try:  p.load(sys.argv[1])
            except: p.compile(open(sys.argv[1], 'r').readlines())
        else: p.compile(open(sys.argv[1], 'r').readlines())
        print p.run()
