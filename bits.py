__all__ = ['__version__', 'bits', 'list_as_tuples', 'nested_dict']
__version__ = '0.1'

import re, time, random, md5, socket
 
def bits(l):
  s, x, n = '', 0, 1
  while n <= l:
    n = 1 << x
    x += 1
    if l & n != 0: s = '1' + s
    else: s = '0' + s 
  return s

def list_as_tuples(l, t):
  x = [0] * t
  i = 0
  for n in l:
    x[i] = n
    i += 1
    if i == t:
      i = 0;
      yield tuple(x)
  if i: yield tuple(x[:i])

def expand(tuples):
  """
    Creates multiple tuples for each item in the list (x, list).
    Used to convert e.g. {'a':[1,2,3], 'b':[4,5,6]} to
      [('a', 1), ('a', 2), ('a', 3), ('b', 4), ('b', 5), ('b', 6)
  """
  if isinstance(tuples, dict): tuples = tuples.items()
  return reduce(lambda rlist, (att, val): (isinstance(val, list) and 
    rlist + [(att, vali) for vali in val]) or (rlist + [(att, val)]), tuples, [])

def uuid( *args ):
  """
    Generates a universally unique ID.
    Any arguments only create more randomness.
		taken from ASPN Python Cookbook 213761
		should be changed to conform to http://www.webdav.org/specs/draft-leach-uuids-guids-01.txt
  """
  t = long( time.time() * 1000 )
  r = long( random.random()*100000000000000000L )
  try:
    a = socket.gethostbyname( socket.gethostname() )
  except:
    # if we can't get a network address, just imagine one
    a = random.random()*100000000000000000L
  data = "%s %s %s %s" % (t, r, a, args)
  data = md5.md5(data).hexdigest()
  return data

class nested_dict(dict):
    cond = re.compile('\[|\]')
    def __init__(self, basedict, index = None):
        self.__basedict = basedict
        self.index = index

    def getattr(self, item, attr):
        parts = filter(None, nested_dict.cond.split(attr))
        if item: 
          if isinstance(item, list) or isinstance(item, tuple): 
            if self.index != None:
              i = item[self.index]
              if isinstance(i, list): item = [getattr(il, parts[0]) for il in i] 
              else: item = getattr(i, parts[0])
            else:
              item = reduce(lambda rl, i:
                (isinstance(i, list) and rl + [getattr(il, parts[0]) for il in i]) or 
                rl + [getattr(i, parts[0])] , item, [])
          else: item = getattr(item, parts[0])
        else: item = self.__basedict[parts[0]]

        if len(parts) > 1:
            if parts[1][0] in ['"', "'"]: pval = parts[1][1:-1]
            else: pval = eval(parts[1])
            if isinstance(item, list) or isinstance(item, tuple): return [i[pval] for i in item]
            return item[pval]
        return item

    def __contains__(self, attr):
        attrset = item.split('.')
        start, attrset = attrset[0], attrset[1:]
        return reduce(lambda a, b:(a and hasattr(a, b) and self.getattr(a, b)) or None, attrset.split('.'), self.__basedict[start]) != None

    def __delitem__(self, item):
        attrset = item.split('.')
        start, attrset = attrset[0], attrset[1:]
        attrset, attrdel = attrset[:-1], attrset[-1]
        delfrom = reduce(lambda a, b:self.getattr(a, b), attrset, self)
        if delfrom: delfrom.__delattr__(attrdel)
        else: raise KeyError(item)

    def __getitem__(self, item):
        attrset = item.split('.')
        start, attrset = attrset[0], attrset[1:]
        return reduce(lambda a, b:self.getattr(a, b), attrset, self.getattr(None, start))

    def __setitem__(self, item, value):
        attrset = item.split('.')
        start, attrset = attrset[0], attrset[1:]
        attrset, aset = attrset[:-1], attrset[-1]
        seton = reduce(lambda a, b:self.getattr(a, b), attrset, self.getattr(None, start))
        if seton: setattr(seton, aset, value)
        else: raise KeyError(item)

    def get(self, attr): self[attr]
    def has_key(self, attr): return attr in self
    def pop(self, k, d = None): "" #todo
    def popitem(self, k, v): "" #todo
    def update(self, d): "" #todo
    def __iter__(self): return self.__basedict.__iter__()
    def __len__(self): return self.__basedict.__len__()
    def __repr__(self): return self.__basedict.__repr__()
    def clear(self): self.__basedict.clear()
    def copy(self): return nested_dict(__basedict.copy())
    def fromkeys(S, v = None): return dict.fromkeys(S, v)
    def items(self): return self.__basedict.items()
    def iteritems(self): return self.__basedict.iteritems()
    def itervalues(self): return self.__basedict.itervalues()
    def keys(self): return self.__basedict.keys()
    def setdefault(self, d): return self.__basedict.setdefault(d)
    def values(self): return self.__basedict.values()

def sscanf(arg_str, format, data = None):
  "Perform sscanf function using format to parse arg_str and save results in data"
  def param(arg, fmt, data):
    "("
    label, fmt_label = fmt.split(")")
    label = label[1:] #drop leading (
    dlist = []
    arg = formats[fmt_label[0]](arg, fmt_label, dlist)
    dval = None
    if len(dlist): dval = dlist[0]
    if isinstance(data, list): data.append((label, dval))
    elif len(label):
      if label[0] == '[': 
        label = label[1:-1]
        if len(label):
          if label[0] in ("'", '"'): data[label[1:-1]] = dval
          else: data[eval(label)] = dval
        else: raise Exception("Invalid format with no label %s", fmt)
      else: setattr(data, label, dval)
    else: raise Exception("Invalid format with no label %s", fmt)
    return arg

  def hash(arg, fmt, data):
    "#"

  def zero(arg, fmt, data):
    "0"
    
  def minus(arg, fmt, data):
    "-"
    
  def space(arg, fmt, data):
    " "

  def plus(arg, fmt, data):
    "+"

  def decimal(arg, fmt, data):
    "d"
    arg_pair =  match_greedy(arg, fmt)
    data.append(long(arg_pair[0]))
    return arg_pair[1]

  def integer(arg, fmt, data):
    "i"
    arg_pair =  match_greedy(arg, fmt)
    data.append(int(arg_pair[0]))
    return arg_pair[1]

  def octal(arg, fmt, data):
    "o"
    arg_pair =  match_greedy(arg, fmt)
    data.append(eval('0' + arg_pair[0]))
    return arg_pair[1]

  def unsigned_octal(arg, fmt, data):
    "u"
    return octal(arg, fmt, data)

  def hex_lower(arg, fmt, data):
    "x"
    arg_pair =  match_greedy(arg, fmt, '0x', True, True)
    arg = arg_pair[0].lower().split('x')
    if len(arg) == 1: arg = '0x' + arg[0]
    else: arg = arg_pair[0]
    data.append(eval(arg))
    return arg_pair[1]

  def hex_upper(arg, fmt, data):
    "X"
    return hex_lower(arg, fmt, data)

  def float_lower(arg, fmt, data):
    "e"
    arg_pair =  match_greedy(arg, fmt, 'e', False, True)
    data.append(eval(arg))
    return arg_pair[1]

  def float_upper(arg, fmt, data):
    "E"
    return float_upper(arg, fmt, data)

  def float_decimal_lower(arg, fmt, data):
    "f"
    arg_pair =  match_greedy(arg, fmt, '.', False, True)
    data.append(eval(arg))
    return arg_pair[1]
 
  def float_decimal_upper(arg, fmt, data):
    "F"
    return float_decimal_lower(arg, fmt, data)

  def float_g_lower(arg, fmt, data):
    "g"
    arg_pair =  match_greedy(arg, fmt, 'e', True, True)
    data.append(eval(arg))
    return arg_pair[1]

  def float_g_upper(arg, fmt, data):
    "G"
    return float_g_upper(arg, fmt, data)

  def char(arg, fmt, data):
    "c"
    data.append(arg[0])
    return arg[1:]

  def represent(arg, fmt, data):
    "r"
    arg_pair = match_greedy(arg, fmt)
    data.append(arg_pair[0])
    return arg_pair[1]

  def string(arg, fmt, data):
    "s"
    return represent(arg, fmt, data)
    
  def literal(arg, fmt):
    flen = len(fmt)
    cmp_str = arg[:flen]
    if fmt != cmp_str: raise Exception("Format and argument do not match at %s:%s" % (fmt, cmp_str))
    return arg[flen:]

  def match_greedy(arg, fmt, skip_to = None, skip_opt = False, skip_case_ins = False):
    "Match the first instance of fmt in arg, return tuple of prefix and suffix"
    fmt = fmt[1:]
    flen, arg_len = len(fmt), len(arg)
    i = end = arg_len - flen

    start = 0
    if skip_to: #start at first index of this char
      if skip_case_ins: start = arg.lower().find(skip_to.lower())
      else: start = arg.find(skip_to)
      if start == -1: 
        if skip_opt: start = 0
        else: raise Exception("Failed to find key char %s in %s" % (skip_to, arg))
    
    if flen:
      for i in range(start, end):
        if fmt == arg[i:i + flen]: break

    prefix = (arg, None)
    if i != end:
      if i == arg_len - flen - 1: i += 1 #check for run to end
      if fmt != arg[i:i + flen]: raise Exception("Mismatch post format %s %s" % (fmt, arg[i:i + flen]))
      prefix = (arg[:i], arg[i + flen:])
    return prefix


  format_funcs = [param, hash, zero, minus, space, plus, decimal, integer, octal, unsigned_octal, 
                  hex_lower, hex_upper, float_lower, float_upper, float_decimal_lower,
                  float_decimal_upper, float_g_lower, float_g_upper, char, represent, string]
  
  formats = dict([(f.__doc__, f) for f in format_funcs])

  if data is None: data = []

  args = re.split('%', format) #arg is list of 'prefx', 'arg)format prefix'...
  arg_str = literal(arg_str, args.pop(0))
  reduce(lambda x, y:formats[y[0]](x, y, data), args, arg_str)
  return data
