
# flgLib is needed for StateMachine

from flgLib import *

# common superclass for flg and fpg drivers to implement the expression
# handling functions

class commonLib(object):
  # exprXYZ() functions return ExprXYZ() objects invoked with the same
  #   arguments.

  def exprOper(self, *args):
    __ret = tuple(args)
    return __ret

  def exprList(self, *args):
    __ret = list(args)
    return __ret

  def exprToken(self, *args):
    __ret = args[0]
    return __ret

  def exprString(self, *args):
    s = u''
    q = None
    qs = args[0]
    while len(qs) > 0:
      c = qs[0]
      qs = qs[1:]
      if c == u'\\':
        s += qs[0]
        qs = qs[1:]
      elif c == q:
        q = None
      elif c in "\"'":
        q = c
      else:
        s += c
    __ret = s
    return __ret

  def exprNumber(self, *args):
    __ret = int(args[0])
    return __ret

  def exprPosParam(self, *args):
    __ret = (u'$', int(args[0][1:]))
    return __ret

  def exprFuncCall(self, *args):
    __ret = (u'(', args[0], list(args[1]))
    return __ret

  # handle processDirective.  Expects to find 'allowed_directives' declared in 'self'.
  def processDirective(self, directive, value):
    if directive not in self.allowed_directives:
      raise ActionFailedException("Unknown directive %s %s" % (directive, repr(value)))
    elif directive == u'%include':
      ifile = open(value, 'rb')
      self.lexer.new_source(ifile, value)
    elif directive == u'%tokens':
      nexttoken = 1 + max(self.data[u'tokens'].values())
      for token in value:
        if isinstance(token, (list,tuple)) and token[0] == u'=':
          nexttoken = token[2]
          token = token[1]
        if not isinstance(token,basestring):
          raise ActionFailedException("Unknown expression value %s found in %s directive" % (repr(token), directive))
        self.data[u'tokens'][token] = nexttoken
        nexttoken += 1
    elif directive == u'%mode': # lexer specific
      self.data[u'mode'] = value
      if self.data[u'start'] is None:
        self.data[u'start'] = value
      if value not in self.data[u'tables']:
        self.data[u'tables'][value] = StateMachine()
    elif directive == u'%start':
      self.data[u'start'] = value
    else:
      raise ActionFailedException("Unknown directive %s %s" % (directive, repr(value)))
    return directive

