
import sys
from flgLexer import *
from flgParser import *
from flgLib import *
from commonLib import *

DEBUGGING_PARSER = False
DEBUGGING_LEXER = False

class flgLexerDriver(flgLexer):
  def processToken(self, token, table, nexttable):
    return token

  if DEBUGGING_LEXER:
    def debug(self, token, table, nexttable):
      print >> sys.stderr, "%s:%s.%s = %s(%s)" % (token.location[u'file'], token.location[u'line'], token.location[u'char'], token.token, token.value)
  else:
    def debug(self, token, table, nexttable):
      pass


class flgParserDriver(flgParser,commonLib):

  def rule_text(self, rulenum):
    rule = self.rules[rulenum]
    return "[%d] %s <- %s" % (rulenum, self.nonterms[rule[0]], " ".join([(((sym > 0) and self.nonterms[sym]) or self.tokens[-sym]) for sym in rule[1]]))

  if DEBUGGING_PARSER:
    def debug(self, rule, states, values, lookahead, action):
      print >> sys.stderr, "Reducing rule %s\n> states=%s values=%s lookahead=%s action=%s" % (self.rule_text(rule), "[" + ", ".join(map(str, states)) + "]", str(values), str(lookahead), str(action))
  else:
    def debug(self, rule, states, values, lookahead, action):
      pass

  if DEBUGGING_PARSER:
    __eval_action_indent = 0
    def _eval_action(self, action, rulevars):
      self.__eval_action_indent += 1
      __call = "_eval_action" + repr( (action,rulevars) )
      print >> sys.stderr, "%s%s" % (">" * self.__eval_action_indent, __call)
      try:
        __ret = super(fpgParserDriver,self)._eval_action(action, rulevars)
      except Exception,e:
        print >> sys.stderr, "%s%s -> %s" % ("*" * self.__eval_action_indent, __call, e)
        raise
      print >> sys.stderr, "%s%s -> %s" % ("<" * self.__eval_action_indent, __call, repr(__ret))
      self.__eval_action_indent -= 1
      return __ret

  # tells the commonLib.processDirectives method which directives are allowed.
  allowed_directives = ( '%mode', '%start', '%tokens', '%include' )

  MAX_UNICODE_VALUE = 0x10FFFF

  def initializeParser(self):
    self.data = {
      'tokens': {u'%eof':0},
      'mode': None,
      'start': None,
      'tables': {},
    }

  def finalizeParser(self, values):
    tables = self.data['tables']

    # convert each lexer NFA to a DFA, then to a state table
    for lextbl in tables.keys():
      tables[lextbl] = tables[lextbl].toDFA().toTable()

    # add any undefined tokens to the end of the tokens list
    # then replace all tokens with their token number
    maxtoken = max(self.data['tokens'].values())
    for lextbl in tables.keys():
      for statenum in range(len(tables[lextbl])):
        state = tables[lextbl][statenum]
        if state[0] is not None:
          token = state[0]
          if isinstance(token, tuple):
            token = token[0]
          if token[0] != '%':
            if token not in self.data['tokens']:
              maxtoken += 1
              self.data['tokens'][token] = maxtoken
              print >> sys.stderr, "Warning: setting token %s to token value %d." % (token, maxtoken)
            if isinstance(state[0], tuple):
              new_accept = (self.data['tokens'][token],) + state[0][1:]
            else:
              new_accept = self.data['tokens'][token]
            tables[lextbl][statenum] = (new_accept,) + state[1:]

    # set the lexer table meta-data
    tables['%initial'] = self.data['start']
    tables['%tokens'] = [token for (tnum,token) in sorted([(tnum,token) for (token,tnum) in self.data['tokens'].items()])]
    tables['%tokenmap'] = self.data['tokens']

    return tables

  def _tuplify(self,val):
    if isinstance(val, (list,tuple)):
      return tuple([self._tuplify(item) for item in val])
    return val

  def rxAddRuleToTable(self, token, NFA, action=None):
    sm = self.data['tables'][self.data['mode']]
    s1 = State()
    s2 = State()
    s2.accepts = token
    action = self._tuplify(action)
    s2.nexttable = action
    s1.transition(None, NFA[0])
    NFA[1].transition(None, s2)
    sm.startState().transition(None, s1)
    return token

  rxStandardEscapes = {
    u'n': 10,
    u't': 9,
    u'a': 7,
    u'b': 8,
    u'v': 11,
    u'r': 13,
    u'f': 12,
  }

  def rxAtomValue(self, atom):
    if atom[0] == u'\\':
      if len(atom) == 2:
        atom = self.rxStandardEscapes.get(atom[1], ord(atom[1]))
      elif atom[1] in u'xuU':
        atom = int(atom[2:],16)
      elif atom[1] in '01234567':
        atom = int(atom[1:],8)
      else:
        raise ActionFailedException("Unknown escape sequence found: %s" % (atom,))
    else:
      assert len(atom) == 1
      atom = ord(atom)
    return atom

  def rxMakeAtomNFA(self, atom):
    if atom == u'.':
      atom = ( (0,9), (11, self.MAX_UNICODE_VALUE) )
    else:
      atom = self.rxAtomValue(atom)
      atom = ( (atom,atom), )
    s1 = State()
    s2 = State()
    for symrange in atom:
      s1.transition(symrange,s2)
    return [s1,s2]

  def rxMakeCharClassNFA(self, start, cc):
    negation = u'^' in start
    ranges = []
    for spec in u'-]':
      if spec in start:
        atom = self.rxAtomValue(spec)
        ranges.append( (atom,atom) )
    ranges.extend([(self.rxAtomValue(b),self.rxAtomValue(e)) for (b,e) in cc])
    ranges.sort()
    # coalesce adjacent ranges, merge overlapping ranges
    i = 1
    while i < len(ranges):
      if ranges[i][0] <= ranges[i-1][1]+1:
        if ranges[i][1] > ranges[i-1][1]:
          ranges[i-1] = (ranges[i-1][0], ranges[i][1])
        del ranges[i]
      else:
        i += 1
    # negate if needed:
    if negation:
      prevEnd = -1
      for i in xrange(len(ranges)):
        nextEnd = ranges[i][1]
        ranges[i] = (prevEnd+1, ranges[i][0]-1)
        prevEnd = nextEnd
      ranges.append((prevEnd+1, self.MAX_UNICODE_VALUE))
    s1 = State()
    s2 = State()
    for range in ranges:
      s1.transition(range,s2)
    return [s1,s2]

  def rxMakeSequenceNFA(self, *seq):
    s1 = seq[0][0]
    s2 = seq[-1][1]
    for i in range(1,len(seq)):
      seq[i-1][1].transition(None, seq[i][0])
    return [s1,s2]

  def rxMakeAlternateNFA(self, *seq):
    s1 = State()
    s2 = State()
    for alt in seq:
      s1.transition(None, alt[0])
      alt[1].transition(None, s2)
    return [s1,s2]

  def rxMakePlusNFA(self, NFA):
    s1 = State()
    s2 = State()
    s2.transition(None,s1)
    s1.transition(None,NFA[0])
    NFA[1].transition(None,s2)
    return [s1,s2]

  def rxMakeStarNFA(self, NFA):
    s1 = State()
    s2 = State()
    s1.transition(None,s2)
    s2.transition(None,s1)
    s1.transition(None,NFA[0])
    NFA[1].transition(None,s2)
    return [s1,s2]

  def rxMakeQuestionNFA(self, NFA):
    s1 = State()
    s2 = State()
    s1.transition(None,s2)
    s1.transition(None,NFA[0])
    NFA[1].transition(None,s2)
    return [s1,s2]


if __name__ == '__main__':
  from flgLexer import flgLexer
  l = flgLexerDriver()
  p = flgParserDriver()
  result = p.parse(l)

  print "  tables={"
  for (key,val) in result.items():
    print "    %s:%s," % (repr(key),repr(val))
  print "  }"


 
