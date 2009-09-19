#import pdb
"""
<xml>
    <prop1>
        Value
    </prop1>
    <prop2>
        <prop3>Value</prop3>
        <prop4>Value</prop4>
    </prop2>
</xml>
"""

__version__ = '1.2'

import os
import urllib, re
from xml.dom.minidom import parseString
from xml.parsers.expat import ErrorString, ExpatError

class XMLData:
    _stdAtts = ['_name', '_parent', '_value', '_cdata', '_types', '_init', '_node', '_stdAtts', '_namespace', '_fullname', '_children', '_partRE', '_cls', '_list_cls']
    _partRE = re.compile('(.*)\[(.*)\]')

    def __init__(self, xml, parent = None, cls = None, list_cls = None):
        "pass in the document root, e.g. xml.firstChild"
        self._init = True
        if cls is None: self._cls = self.__class__
        else: self._cls = cls

        if list_cls is None: self._list_cls = list
        else: self._list_cls = list_cls

        self._node = xml
        self._fullname = xml.tagName
        if ':' in self._fullname: self._namespace, self._name = self._fullname.split(':')
        else: self._name = self._fullname
        self._parent = parent
        child = xml.firstChild
        self._value = None
        self._cdata = False
        if child:
          if child.nodeType == xml.TEXT_NODE: self._value = child.data.strip()
          elif child.nodeType == xml.CDATA_SECTION_NODE:
            self._value = child.data.strip()
            self._cdata = True
          if self._value is not None and len(self._value) == 0: self._value = None

        self._types = {}

        #map attributes
        if xml._get_attributes(): map(lambda i:self.__setitem__(i[0], i[1]), xml._get_attributes().items())

        #map child nodes
        self._children = self._list_cls()
        map(self.parseProp, xml.childNodes)
        self._init = False

    def deepcopy(self):
        "Create full copy of the entire structure"
        x = ParseAsXMLData('<?xml version="1.0"?><xml/>', self._cls)
        map(lambda d:(isinstance(d[1], self._cls) and not d[0] == '_parent' and x.__dict__.__setitem__(d[0], d[1].deepcopy())) or \
                x.__dict__.__setitem__(d[0], d[1]), self.__dict__.items())
        return x

    def update(self, xmld):
        #update attributes
        for att, val in filter(lambda (att, val):att[0] == '@', xmld.__dict__.items()): self.__setattr__(att, val)

        #update children
        for child in xmld._children:
          if isinstance(child, XMLData): self.__setattr__(child._name, child.deepcopy())
          else: self.__setattr__(child[0], child[1])

    def ignoreAttribute(self, att):
        "Add att to list of ignored attributes when seralizing, etc.  Examples include _name and _parent"
        if isinstance(att, list): self._stdAtts += att
        else: self._stdAtts.append(att)

    def attributeType(self, att, att_type = None):
        "Set data types to interpret attributes"
        if isinstance(att, list): 
          if isinstance(att_type, list): att = dict(zip(att, att_type))
          else: att = dict([(a, att_type) for a in att])
        
        if isinstance(att, dict): self._types.update(att)
        else: self._types[att] = att_type

    def parseProp(self, xml):
        "Internal method to parse a DOM xml node"
        tagName = None
        if xml.nodeType in [xml.TEXT_NODE, xml.COMMENT_NODE]: return
        try: tagName = xml.tagName
        except: return #comment
        #kids = len(xml.childNodes)
        #if kids == 0: return
        #check for text node child
        child = xml.firstChild
        if child and child.nodeType == xml.TEXT_NODE and len(child.data.strip()) and not len(xml._get_attributes()): 
          child_data = child.data.strip()
          self.__setattr__(tagName, child_data)
          self._children.append((tagName, child_data))
        else:
          x = self._cls(xml, self, cls = self._cls, list_cls = self._list_cls)
          self._children.append(x) 
          self.__setattr__(tagName, x)

    def xmlAttr(self, attr, value = None):
        "Create and store new xml attribute"
        val = ParseAsXMLData('<?xml version="1.0"?><%s/>' % attr, self._cls)
        if value: val._value = value
        return val

    def __setattr__(self, attr, val):
        #make sure non attributes are XMLData
        #if attr[0] != '@' and not attr in self._stdAtts:
        #  if isinstance(val, list): val = [(isinstance(v, XMLData) and v) or self.xmlAttr(attr, v) for v in val]
        #  elif not isinstance(val, XMLData): val = self.xmlAttr(attr, val)

        #basic set vs append to list
        if attr in self.__dict__ and not attr in self._stdAtts and not isinstance(val, list):
            if isinstance(self.__dict__[attr], list): 
              self.__dict__[attr].append(val)
              if not self._init: self._children.append((attr, val))
            elif self._init: 
              self.__dict__[attr] = self._list_cls([self.__dict__[attr], val])
            else: 
              old = self.__dict__[attr]
              if not isinstance(old, XMLData): old = (attr, old)
              if old in self._children: 
                index = self._children.index(old)
                self._children.pop(index)
                self._children.insert(index, (attr, val))
              else: self._children.append((attr, val))
              self.__dict__[attr] = val
        else: 
          self.__dict__[attr] = val
          if not self._init and attr != '_init': self._children.append((attr, val))

        #not at init, update children for XMLData
        if '_init' in self and not self._init and not attr in self._stdAtts:
            if isinstance(val, XMLData): 
              val._parent = self
              self._children.append(val)
            if isinstance(val, list): 
              fvals = filter(lambda v: isinstance(v, XMLData) and v._parent != self, val)
              if len(fvals):
                map(lambda v:v.__setattr__('_parent', self), fvals)
                self._children += fvals
              fvals = filter(lambda v: not isinstance(v, XMLData), val)
              if len(fvals): self._children += self._list_cls([(attr, fval) for fval in fvals])

    def __setitem__(self, attr, val): self.__setattr__('@' + attr, val)
    def __getitem__(self, attr): return self.__getattr__('@' + attr)
    def __delitem__(self, attr): self.__delattr__('@' + attr)

    def childNodes(self): 
        "Ordered list of children nodes"
        return self._children 
    def childValues(self): 
        "Dictionary of tag names to nodes and values"
        return dict(filter(lambda c:c[0][0] != '@' and c[0] not in self._stdAtts, self.__dict__.items()))
    def attributes(self): 
        "Dictionary of attributes"
        return dict(map(lambda a:(a[0][1:],a[1]), filter(lambda c:c[0][0] == '@', self.__dict__.items())))

    def keys(self): 
        "Keys of of attributes and childValues"
        return dict(filter(lambda c:c[0] not in self._stdAtts, self.__dict__.items()))
    def values(self): 
        "Unordered list of values of childValues (not including attributes)"
        return reduce(lambda x,y:(isinstance(y, list) and x + y) or (not isinstance(y, list) and x + [y]), self.childNodes().values(), [])

    def __hasattr__(self, attr): return attr in self.__dict__
    def __getattr__(self, attr): 
      if attr in self._types: return self._types[attr](self.__dict__[attr])
      return self.__dict__[attr]
    def __delattr__(self, attr): self.remove(attr)
    def __repr__(self): 
      if '_value' in self.__dict__ and self.__dict__['_value']: return self.printvalue(self.__dict__['_value'], self.__dict__['_cdata'])
      #if '_cdata' in self.__dict__ and self.__dict__['_cdata']: return '<![CDATA[%s]]>' % self._value
      #else: return self._value
      return "<%s %s>" % (repr(self._cls)[1:-1], self._name)
    def __str__(self): 
      if '_value' in self.__dict__ and self.__dict__['_value']: return self.printvalue(self.__dict__['_value'], self.__dict__['_cdata'])
      return "<%s %s>" % (repr(self._cls)[1:-1], self._name)
      #return repr(self)
    def __eq__(self, d): return isinstance(d, XMLData) and (object.__repr__(self) == object.__repr__(d) or cmp(self.toxml(), d.toxml()) == 0)
    def __ne__(self, d): return self.__eq__(d) != True
    def __contains__(self, key): return key in self.__dict__
    def __nonzero__(self): return True

    def find(self, path):
        "XPath to find an XMLData"
        parts = path.split('/')
        if len(parts) and not len(parts[-1]): parts.pop() #trailing '/'
        if len(parts[0]) == 0: #context is root, call this on the root
            if self._parent:
                root = self._parent
                while root._parent: root = root._parent
                return root.find(path)
            else: parts.pop(0) #this is the root

        context = [self]
        for part in parts:
            if not context: return
            value = None
            specs = None

            #check for any criteria on this part
            if '[' in part: #spec
                try: part, subspec = tuple(XMLData._partRE.match(part).groups())
                except: raise "Error in find, parsing", part
                specs = map(lambda m:tuple(map(lambda n:n.strip('\'" \t'), m.split('='))), subspec.split('and'))
                
            context = filter(lambda m:hasattr(m, part), context)
            #this reduction extracts the part attribute from sibling contexts and forms a list of sub parts, all cousins
            context = reduce(lambda x, y:(isinstance(getattr(y, part), list) and x + getattr(y, part)) or
                                        ((not isinstance(getattr(y, part), list)) and x + self._list_cls([getattr(y, part)])), context, self._list_cls())
            #exclude contexts that don't match
            if context and specs: context = filter(lambda m:m.matchesCriteria(specs), context)
        return context

    def matchCriteria(self, spec):
        attr, value = spec
        if attr in self:
            cmpTo = getattr(self, attr)
            if not value: return True
            if isinstance(cmpTo, list):
                if value in cmpTo: return True
            elif value == cmpTo: return True
        return False

    def matchesCriteria(self, specs):
        #specs is an AND list of criteria, either exists or =
        return len(filter(self.matchCriteria, specs)) == len(specs)

    def remove(self, xmld):
        "Remove specified XMLData from the tree.  Use find to get an XMLData"
        if isinstance(xmld, XMLData):
          if xmld._parent is self:
            if isinstance(self.__dict__[xmld._name], list):
              if xmld in self.__dict__[xmld._name]: 
                self.__dict__[xmld._name].remove(xmld)
                self._children.remove(xmld)
            else:
              assert self.__dict__[xmld._name] == xmld
              self._children.remove(self.__dict__[xmld._name])
              del self.__dict__[xmld._name]
          elif xmld._parent: xmld._parent.remove(xmld)
        else:
          frem = filter(lambda x:isinstance(x, tuple) and x[0] == xmld, self._children)
          [self._children.remove(x) for x in frem]
          del self.__dict__[xmld]

    def printvalue(self, value, cdata):
        if not isinstance(value, str) and not isinstance(value, unicode): value = repr(value)
        if not cdata:
          if value.find('<') != -1: return '<![CDATA[%s]]>' % value
          if value.find('>') != -1: return '<![CDATA[%s]]>' % value
          if value.find('"') != -1: return '<![CDATA[%s]]>' % value
          if value.find("'") != -1: return '<![CDATA[%s]]>' % value
          amp =  value.find('&')
          if amp != -1:
            semi = value[amp:].find(';')
            if semi > 4: return '<![CDATA[%s]]>' % value
        return value

    def toxml(self):
        attributes = ' '.join(map(lambda a:'%s="%s"' % (a[0][1:], Quote(a[1])), filter(lambda m:m[0][0] == '@', self.__dict__.items())))
        if len(attributes): attributes = ' ' + attributes
        children = map(self.xmlnode, self._children)
        if len(children): return '<%s%s>%s</%s>' % (self._fullname, attributes, ''.join(children), self._fullname)
        elif self._value is not None: return '<%s%s>%s</%s>' % (self._fullname, attributes, self.printvalue(Quote(self._value), self._cdata), self._fullname)
        else: return '<%s%s/>' % (self._fullname, attributes)

    def xmlnode(self, name_value):
        name, value = None, None
        if isinstance(name_value, XMLData): name, value = name_value._name, name_value
        else: name, value = name_value

        if isinstance(value, list): return ''.join(map(lambda m: self.xmlnode((name, m)), value))
        if isinstance(value, XMLData): return value.toxml()

        attributes = ' '.join(map(lambda a:'%s="%s"' % (a[0][1:], a[1]), filter(lambda m:m[0][0] == '@', self.__dict__.items())))
        if len(attributes): attributes = ' ' + attributes
        if isinstance(value, str) or isinstance(value, unicode): 
          if len(value): return '<%s%s>%s</%s>' % (name, attributes, Quote(value), name)
          return '<%s%s/>' % (name, attributes)
        else: return '<%s%s>%s</%s>' % (name, attributes, Quote(value), name)

    def toprettyxml(self, indent = 0):
        attributes = ' '.join(map(lambda a:'%s="%s"' % (a[0][1:], a[1]), filter(lambda m:m[0][0] == '@', self.__dict__.items())))
        if len(attributes): attributes = ' ' + attributes
        children = map(lambda x:self.prettyxmlnode(x, indent + 1), self._children)
        tabs = ''.join(map(lambda t:'\t', range(indent)))
        if len(children): return '<%s%s>%s\n%s</%s>' % (self._fullname, attributes, ''.join(children), tabs, self._fullname)
        elif self._value: return '<%s%s>%s</%s>' % (self._fullname, attributes, self.printvalue(Quote(self._value), self._cdata), self._fullname)
        else: return '<%s%s/>' % (self._fullname, attributes)

    def prettyxmlnode(self, name_value, indent):
        name, value = None, None
        if isinstance(name_value, XMLData): name, value = name_value._name, name_value
        else: name, value = name_value

        tabs = ''.join(map(lambda t:'\t', range(indent)))
        if isinstance(value, list): return ''.join(map(lambda m: self.prettyxmlnode((name, m), indent), value))
        if isinstance(value, XMLData): return '\n%s%s' % (tabs, value.toprettyxml(indent))

        attributes = ' '.join(map(lambda a:'%s="%s"' % (a[0][1:], a[1]), filter(lambda m:m[0][0] == '@', self.__dict__.items())))
        if len(attributes): attributes = ' ' + attributes
        if isinstance(value, str) or isinstance(value, unicode):
          if len(value):return '\n%s<%s%s>%s</%s>' % (tabs, name, attributes, Quote(value), name)
          return '\n%s<%s%s/>' % (tabs, name, attributes)
        else: return '%s<%s%s>%s</%s>' % (tabs, name, attributes, Quote(value), name)

def ParseAsXML(xml):
    try:
        #doc = parseString(urllib.unquote(xml)).firstChild
        doc = parseString(xml).firstChild
        while doc.nodeType in [doc.TEXT_NODE, doc.COMMENT_NODE, doc.PROCESSING_INSTRUCTION_NODE]: doc = doc.nextSibling
        return doc
    except ExpatError, error: 
      context = '\n'.join([c[error.offset - 50: error.offset + 50] for c in xml.split('\n')[error.lineno - 2: error.lineno + 2]])
      context += '-' * 50 + '^\n'
      raise Exception('Error parsing xml near \n%s\n%s' % (context, error))

def ParseAsXMLData(xml, cls = XMLData, list_cls = list): return cls(ParseAsXML(xml), cls = cls, list_cls = list_cls)
def LoadXML(xmlFile): return ParseAsXML(''.join(file(xmlFile, 'r').readlines()))
def LoadXMLData(xmlFile, cls = XMLData, list_cls = list): return ParseAsXMLData(''.join(file(xmlFile, 'r').readlines()), cls, list_cls)
def SaveXMLData(xmld, xmlFile):
    try: os.makedirs(os.path.dirname(xmlFile))
    except: pass
    file(xmlFile, 'w').write('<?xml version="1.0"?>\n' + xmld.toprettyxml())
def NodeList(node):
    if not isinstance(node, list): return [node]
    return node
def NodeMap(node, attributeKey):
    if isinstance(node, list): return dict([(n.__dict__[attributeKey],n) for n in node])
    return {node.__dict__[attributeKey]:node}
def ValueList(node):
    return map(lambda v:(isinstance(v, XMLData) and v._value) or v, NodeList(node))

def DictToXMLData(x, cls = XMLData, list_cls = list):
    template = ParseAsXMLData('<?xml version="1.0"?><template/>\n', cls, list_cls)
    for key, value in x.items():
      if isinstance(value, dict): setattr(template, key, DictToXMLData(value, cls, list_cls))
      elif isinstance(value, list): setattr(template, key, list_cls(value))
      else: template[key] = value
    return template

SpecialChars = "<>&'\"/"
EncodeMap = [ord(x) for x in SpecialChars]

def EncodeChar(c):
  x = ord(c)
  if x < 128 and x not in EncodeMap: return c
  return '&#%04d;' % x

def Quote(text): return ''.join([EncodeChar(x) for x in text]) 

