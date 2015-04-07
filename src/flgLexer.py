#!/usr/bin/python
########################################################################
# This file was automatically generated by flg version 1.0.0-alpha1
########################################################################

import sys
import codecs

try:
  LexerException
except NameError:
  class LexerException(Exception): pass
  class LexerFatalException(LexerException): pass
  class LexerWarningException(LexerException): pass

class flgLexerToken(object):
  """A token returned by flgLexer.  The minimal token has a token name, value, and location."""

  def __init__(self, token=None, value=None, location=None):
    """Create a new token with the given token name, value, and location, if provided."""
    if isinstance(token,flgLexerToken):
      self.token = token.token
      self.value = token.value[:]
      self.location = dict(token.location.items())
    else:
      self.token = token
      self.value = value
      self.location = location
  def copy(self):
    return flgLexerToken(self)
  def __str__(self):
    return u"%s(%s)" % (self.token, self.value)
  def __repr__(self):
    return u"%s(token=%s,value=%s,location=%s)" % (self.__class__.__name__, repr(self.token), repr(self.value), repr(self.location))

class flgLexer(object):
  """The flgLexer lexer class.  This contains the tables for the lexer, plus the lexer code itself."""

  def __init__(self, source=sys.stdin, filename=u"(stdin)"):
    """Initialize the lexer with the initial source and filename.  If not provided, these parameters default to a source of sys.stdin and a filename of "(stdin)"."""
    # first, initialize the different stacks that track information related to a particular input source.
    # these are "stacks" in order to allow for new input sources to be "pushed" into the middle of an existing source.

    # self.location holds the stack of location dicts; each location dict tracks the current location within the source stream at the same stack depth.
    self.location = []
    # self.source holds the stack of source streams.
    self.source = []
    # self.lookahead holds the stack of lookahead arrays associated with their source streams.  Each lookahead array tracks all the characters that have been read from the stream since the last accepted token.
    self.lookahead = []
    # self.pushed_tokens is a per-source token buffer that allows the parser to temporarily push tokens back onto the input stream.
    # this is currently used by the standard parser routines to preserve the input token whenever a production action is taken, in case the production action changes the lexer's input stream.
    # self.pushed_tokens gets initialized with an empty list, so that tokens can still be pushed after the lexer has officially hit end-of-file on the last input stream.
    self.pushed_tokens = [[]]  # allow for pushed tokens after the last end-of-file

    # now set up the initial source.
    self.new_source(source=source, filename=filename)

    # The table stack is for lexers that need to recursively change lexing tables, to provide a sort of context for the lexing.
    # The main use case I see for this is to allow nested comments, when comments have unique begin/end symbols.
    # The table stack gets initialized with the initial table from the lexer tables, or u'default' if no initial table is provided.
    self.table_stack = [ self.tables.get(u'%initial', u'default') ]

    # The error_state will normally be False.  It is set to True on a
    # syntax error (a condition where the lexer has read a symbol with
    # no transitions possible and no possible tokens to accept).  The
    # next time next_token() is called, the first character in the lookahead
    # buffer will be removed.  No further error tokens will be generated
    # until a token can be accepted or the end-of-file has been reached
    # on the last input source.
    self.error_state = False

  # the tables are generated by the lexer generator class.
  # The initial table is recorded in the "%initial" entry.
  # The tokens list, with associated values, is recorded in the "%tokens" entry.
  tables={
u'comment':[
(None,(((0,9),5),((10,10),5),((11,39),5),((40,40),3),((41,57),5),((58,58),1),((59,1114111),5))),
(u'%skip',(((41,41),2),)),
((u'%skip',(u'(',u'pop',(u'comment',))),()),
(u'%skip',(((58,58),4),)),
((u'%skip',(u'(',u'push',(u'comment',))),()),
(u'%skip',())
],
'%initial':u'normal',
u'normal':[
(None,(((9,10),23),((32,32),23),((34,34),21),((36,36),19),((37,37),17),((39,39),14),((40,40),12),((41,41),11),((43,43),10),((44,44),9),((45,45),7),((47,47),6),((48,57),5),((60,60),3),((61,61),2),((65,90),1),((95,95),1),((97,122),1))),
(1,(((48,57),1),((65,90),1),((95,95),1),((97,122),1))),
(3,()),
(None,(((45,45),4),)),
(15,()),
(4,(((48,57),5),)),
((17,u'regexp'),()),
(None,(((48,57),5),((62,62),8))),
((16,(u'(',u'push',(u'expression',))),()),
(9,()),
(None,(((48,57),5),)),
(8,()),
(7,(((58,58),13),)),
((u'%skip',(u'(',u'push',(u'comment',))),()),
(None,(((0,38),14),((39,39),16),((40,91),14),((92,92),15),((93,1114111),14))),
(None,(((0,9),14),((11,1114111),14))),
(6,(((34,34),21),((39,39),14))),
(None,(((97,122),18),)),
(2,(((97,122),18),)),
(None,(((48,57),20),)),
(5,(((48,57),20),)),
(None,(((0,33),21),((34,34),16),((35,91),21),((92,92),22),((93,1114111),21))),
(None,(((0,9),21),((11,1114111),21))),
(u'%skip',(((9,10),23),((32,32),23)))
],
'%tokens':[
u'%eof',
u'C_TOKEN',
u'C_DIRECTIVE',
u'C_EQUALS',
u'C_NUMBER',
u'C_POS_PARAM',
u'C_QUOTEDSTR',
u'C_PAREN_OPEN',
u'C_PAREN_CLOSE',
u'C_COMMA',
u'C_PLUS',
u'C_MINUS',
u'C_TIMES',
u'C_DIVIDE',
u'C_MODULO',
u'C_DERIVES',
u'C_ACTION',
u'L_RX_START',
u'L_RX_END',
u'L_RX_ALTERNATE',
u'L_RX_PLUS',
u'L_RX_QUESTION',
u'L_RX_STAR',
u'L_RX_ATOM',
u'L_RX_CHARCLASS',
u'L_RX_CC_CHAR',
u'L_RX_CC_END',
u'L_RX_CC_RANGE',
u'L_RX_GRP_CLOSE',
u'L_RX_GRP_OPEN'
],
u'charclass':[
(None,(((0,44),20),((45,45),19),((46,91),20),((92,92),2),((93,93),1),((94,1114111),20))),
((26,u'regexp'),()),
(None,(((0,47),20),((48,55),17),((56,84),20),((85,85),9),((86,116),20),((117,117),5),((118,119),20),((120,120),3),((121,1114111),20))),
(None,(((48,57),4),((65,70),4),((97,102),4))),
(None,(((48,57),20),((65,70),20),((97,102),20))),
(None,(((48,57),6),((65,70),6),((97,102),6))),
(None,(((48,57),7),((65,70),7),((97,102),7))),
(None,(((48,57),8),((65,70),8),((97,102),8))),
(None,(((48,57),20),((65,70),20),((97,102),20))),
(None,(((48,57),10),((65,70),10),((97,102),10))),
(None,(((48,57),11),((65,70),11),((97,102),11))),
(None,(((48,57),12),((65,70),12),((97,102),12))),
(None,(((48,57),13),((65,70),13),((97,102),13))),
(None,(((48,57),14),((65,70),14),((97,102),14))),
(None,(((48,57),15),((65,70),15),((97,102),15))),
(None,(((48,57),16),((65,70),16),((97,102),16))),
(None,(((48,57),20),((65,70),20),((97,102),20))),
(None,(((48,55),18),)),
(None,(((48,55),20),)),
(27,()),
(25,())
],
'%tokenmap':{
u'C_TOKEN':1,
u'L_RX_STAR':22,
u'C_TIMES':12,
u'C_DERIVES':15,
u'C_COMMA':9,
u'L_RX_GRP_OPEN':29,
u'L_RX_CC_CHAR':25,
u'%eof':0,
u'C_DIRECTIVE':2,
u'C_PAREN_CLOSE':8,
u'C_DIVIDE':13,
u'L_RX_ATOM':23,
u'C_QUOTEDSTR':6,
u'L_RX_CHARCLASS':24,
u'L_RX_CC_END':26,
u'L_RX_ALTERNATE':19,
u'L_RX_END':18,
u'C_PAREN_OPEN':7,
u'C_POS_PARAM':5,
u'L_RX_QUESTION':21,
u'C_ACTION':16,
u'C_PLUS':10,
u'L_RX_GRP_CLOSE':28,
u'L_RX_CC_RANGE':27,
u'C_MINUS':11,
u'C_EQUALS':3,
u'C_NUMBER':4,
u'L_RX_START':17,
u'L_RX_PLUS':20,
u'C_MODULO':14
},
u'regexp':[
(None,(((0,39),29),((40,40),28),((41,41),27),((42,42),26),((43,43),25),((44,46),29),((47,47),24),((48,62),29),((63,63),23),((64,90),29),((91,91),19),((92,92),2),((93,123),29),((124,124),1),((125,1114111),29))),
(19,()),
(None,(((0,47),29),((48,55),17),((56,84),29),((85,85),9),((86,116),29),((117,117),5),((118,119),29),((120,120),3),((121,1114111),29))),
(None,(((48,57),4),((65,70),4),((97,102),4))),
(None,(((48,57),29),((65,70),29),((97,102),29))),
(None,(((48,57),6),((65,70),6),((97,102),6))),
(None,(((48,57),7),((65,70),7),((97,102),7))),
(None,(((48,57),8),((65,70),8),((97,102),8))),
(None,(((48,57),29),((65,70),29),((97,102),29))),
(None,(((48,57),10),((65,70),10),((97,102),10))),
(None,(((48,57),11),((65,70),11),((97,102),11))),
(None,(((48,57),12),((65,70),12),((97,102),12))),
(None,(((48,57),13),((65,70),13),((97,102),13))),
(None,(((48,57),14),((65,70),14),((97,102),14))),
(None,(((48,57),15),((65,70),15),((97,102),15))),
(None,(((48,57),16),((65,70),16),((97,102),16))),
(None,(((48,57),29),((65,70),29),((97,102),29))),
(None,(((48,55),18),)),
(None,(((48,55),29),)),
((24,u'charclass'),(((45,45),22),((93,93),21),((94,94),20))),
((24,u'charclass'),(((45,45),22),((93,93),21))),
((24,u'charclass'),(((45,45),22),)),
((24,u'charclass'),()),
(21,()),
((18,u'normal'),()),
(20,()),
(22,()),
(28,()),
(29,()),
(23,())
],
u'expression':[
(None,(((9,9),20),((10,10),19),((32,32),20),((34,34),17),((36,36),15),((37,37),14),((39,39),11),((40,40),10),((41,41),9),((42,42),8),((43,43),7),((44,44),6),((45,45),5),((47,47),4),((48,57),3),((61,61),2),((65,90),1),((95,95),1),((97,122),1))),
(1,(((48,57),1),((65,90),1),((95,95),1),((97,122),1))),
(3,()),
(4,(((48,57),3),)),
(13,()),
(11,(((48,57),3),)),
(9,()),
(10,(((48,57),3),)),
(12,()),
(8,()),
(7,()),
(None,(((0,38),11),((39,39),13),((40,91),11),((92,92),12),((93,1114111),11))),
(None,(((0,9),11),((11,1114111),11))),
(6,(((34,34),17),((39,39),11))),
(14,()),
(None,(((48,57),16),)),
(5,(((48,57),16),)),
(None,(((0,33),17),((34,34),13),((35,91),17),((92,92),18),((93,1114111),17))),
(None,(((0,9),17),((11,1114111),17))),
((u'%skip',(u'(',u'pop',(u'expression',))),()),
(u'%skip',())
]
}

  def new_source(self, source, filename):
    """Start processing from a new source.  Save the current source so that when the new source finishes, the lexer will continue where it was in the current source."""

    # create the utf-8-encoded input stream
    self.source.insert(0, codecs.EncodedFile(source, u'utf-8'))
    # push the default starting location, lookahead buffer, and pushed-tokens buffer
    self.location.insert(0, { u'file':filename, u'line':0, u'char':0, u'newline':True })
    self.lookahead.insert(0, [])
    self.pushed_tokens.insert(0, [])

  def processToken(self, token, table, nexttable):
    """A token processing hook.  Subclasses can override this to transform the token if needed before it is returned to the caller."""
    return token


  def debug(self, token, table, nexttable):
    """A debugging hook.  Subclasses can override this to provide debugging information as the lexer accepts tokens."""
    pass


  # read the next character from the given source.
  # if needed, update the location.
  def read_char(self, source, location):
    """Read a character from the given source at the given location.  If needed, update the location.  This is factored out of the rest of the code in case special file handling is required by a subclass."""
    return source.read(1)

  # fetch the next character from the source stack.
  # assumption: once an end-of-file is returned, this will never be called again
  def __next_char(self):
    """Fetch the next character from the lookahead and source stack.  This uses self.read_char() to actually read from a source.  This method updates the current location and lookahead buffer for the newly read character, and returns an integer representing the character: either -1 if the end-of-file was reached for the current input source, or the unicode character point for the character."""

    # cache some local references to my instance variables
    la = self.lookahead[0]
    li = self.lookahead_idx

    # we keep looping to read a new character as long as our
    # lookahead index is past the end of the lookahead buffer.
    while li >= len(la):

      # before we read a character, we update the current location
      # to where that character is being read from.
      if self.location[0][u'newline']:
        self.location[0][u'line'] += 1
        self.location[0][u'char'] = 1
      else:
        self.location[0][u'char'] += 1

      # Remove the 'newline' flag from self.location and make a copy
      # before reading.  The newline flag will get recreated afterwards,
      # but this allows us to have a copy to record and pass around
      # without having the confusing flag in it.
      del self.location[0][u'newline']
      symloc = self.location[0].copy()

      # call self.read_char() to actually read a [utf-8] character from
      # the source, then add it to the lookahead buffer.
      c = self.read_char(self.source[0], self.location[0])
      la.append( (c, symloc) )

      # Re-create the 'newline' flag in the current location to indicate
      # whether the next location update should shift to a new line or not.
      self.location[0][u'newline'] = (c == u'\n')

    #-- end: while li >= len(la):

    # fetch the character we'll be returning, and convert it to an integer:
    # either -1 for an end-of-file on the current source, or the unicode
    # character point for the character.
    c = la[li][0]
    if c == u'':
      return -1
    return ord(c)

  def push(self, token):
    """Push a token back into the tokenizer; it will be read before any additional characters are read from the input source."""
    self.pushed_tokens[0].insert(0, token)

  def next_token(self):
    """Return the next token from the source.  It will either return a flgLexerToken object with a valid token, an %eof token, or an %error token, or it will return None if we have no valid source stream to read from."""

    # this is the tokenizer engine.  It processes the state transitions
    # through the lexer tables until it reaches a point where either a
    # token can be accepted, or it's impossible for any token to be
    # accepted (a syntax error).

    # first, check if we have any pushed tokens on the stack.  If so,
    # pop one off and return it.

    if len(self.pushed_tokens[0]) > 0:
      token = self.pushed_tokens[0].pop(0)
      return token

    # if we don't have an input source anymore, raise StopIteration.

    if len(self.source) == 0:
      return None

    # initialize the state machine by fetching the current state
    # table and starting the state pointer at state 0 (our lexer
    # lexer generator always creates the initial state as state 0).
    # TODO: this should be parameterized as self.tables[u'%start']
    # Also initialize the lookahead index to 0 so we're looking at
    # the first character in the lookahead buffer, and reset the
    # accepting state to None.

    dfa = self.tables[self.table_stack[0]]
    state = 0

    self.lookahead_idx = 0
    accept = None

    # Loop until we have a token, the end of all input streams, or
    # a syntax error.
    while 1:

      # check if the current state can accept a token.  if so,
      # record the state and lookahead index.
      if dfa[state][0] is not None:
        accept = (state,self.lookahead_idx)

      # Fetch the next character, either from the lookahead buffer
      # or by reading a character from the current input source.
      # sym will be an integer representing the character that was
      # read: either a unicode code point, or -1 if end-of-file was
      # reached on the current input source.

      sym = self.__next_char()

      # look through the transition ranges for the current state to
      # see if the symbol can cause a transition.  next_state will
      # hold the target state of the transition, or will remain None
      # if no transition is possible.

      next_state = None
      for ((symfirst,symlast),transition_state) in dfa[state][1]:
        # optimization: assuming that transitions are sorted on the
        # symbol ranges, we can short-circuit the loop:
        # if symlast is >= sym, this is the last transition to check
        if symlast >= sym:
          # if symfirst <= sym, our character matches the transition
          if symfirst <= sym:
            # set the next state to this transition state
            next_state = transition_state
          # we're done with the loop
          break

      # if we have a legal transition, take it.  Adjust the state
      # machine's state and shift the lookahead index.
      if next_state is not None:
        state = next_state
        self.lookahead_idx += 1

      # We don't have a legal transition.  If we have passed through
      # an accept state up to this point, we can now accept the token
      # at the last accept state found.  When we do so, we'll pull the
      # token value out of the start of the lookahead buffer and shift
      # the rest of the lookahead buffer to be ready for the start of
      # the next state machine run.
      elif accept is not None:

        # fetch the accepted state and accepted index point.
        (accepted_state, accepted_idx) = accept

        # the lookahead buffer records both symbols and locations.  To
        # create the token value, we join together just the symbol part
        # of the lookahead buffer up through the accepted index point.
        val = u"".join(map(lambda x:x[0], self.lookahead[0][0:accepted_idx]))

        # Use the location from the first character of the lookahead buffer
        # as the location of the token.
        loc = self.lookahead[0][0][1]

        # Remove the part of the lookahead buffer that we are returning.
        self.lookahead[0] = self.lookahead[0][accepted_idx:]

        # Find the token that was accepted from the state table for the
        # accepted state.
        tkn = dfa[accepted_state][0]

        # If the token is a tuple, that means that accepting the token
        # at that state causes a transition to a different table.
        # Record that information now so we can process it later.
        if isinstance(tkn, tuple):
          (tkn,nexttable) = tkn
        else:
          nexttable = None

        # Generate the token object that will be returned.  Pass it
        # through the processToken hook in case the token needs to
        # be transformed before returning it to the parser.
        token = flgLexerToken(token=tkn, value=val, location=loc)
        token = self.processToken(token, self.table_stack[0], nexttable)


        # call the debugging hook with the token and the next table.
        self.debug(token, self.table_stack[0], nexttable)


        # If the next table information itself is a tuple, that means
        # that it uses a transition function such as push or pop.
        # (grr, stupid context-sensitive "context free" languages)
        if isinstance(nexttable, tuple):

          # The lexer generator should never generate anything other
          # than:  ( u'(', <function>, (<table>,) )
          # that is: a three-element tuple, consisting of a left-paren,
          # the name of the transition function, and a one-element tuple
          # holding the new table name.
          if len(nexttable) != 3              or not isinstance(nexttable[2], tuple)              or len(nexttable[2]) != 1 :
               raise LexerFatalException("Invalid transition function format for token %s in table %s" % (repr(tkn), self.table_stack[0]))

          # if the transition function is "push", push the new table name
          # to the front of the table stack.
          if unicode(nexttable[1]) == u'push':
            self.table_stack.insert(0, nexttable[2][0])

          # if the transition function is "pop", pop the front of the table
          # stack.  The table name argument is ignored.
          elif unicode(nexttable[1]) == u'pop':
            self.table_stack.pop(0)

          # Anything else will cause a lexer error.  This should never happen,
          # since this should be checked by the lexer generator's parser before
          # this file ever gets generated.
          else:
            raise LexerFatalException("Unknown transition function name for token %s in table %s" % (repr(tkn), self.table_stack[0]))
        elif nexttable is not None:

          # We just have a simple table transition; replace the first table in
          # the table stack with the new table name.
          self.table_stack[0] = nexttable

        # reset the error state to indicate that syntax errors may once again
        # be reported.
        self.error_state = False

        # return the new token
        return token

      #-- end: elif accept is not None:

      # We did not have a valid transition and we did not have an accept state.
      # Check if we have an end-of-file that is the only thing in the lookahead
      # buffer (if we get here on an end-of-file but there is other stuff in the
      # lookahead buffer, then that other stuff caused a syntax error).
      elif sym == -1 and len(self.lookahead[0]) == 1:

        # If we have more than one source in our source stack, then we need to
        # pop a source out of the stack and keep going.

        # If we only have one source in our source stack, then we're done and
        # we need to return the %eof token.

        # Save the location of the eof, in case this is a real eof.
        loc = self.lookahead[0][0][1].copy()

        # Pop off the first element of source, lookahead, location, and pushed_tokens.
        self.source.pop(0)
        self.lookahead.pop(0)
        self.location.pop(0)
        self.pushed_tokens.pop(0)

        # If our source stack is now empty, generate and return an %eof token.
        if len(self.source) == 0:
          token = u'%eof'
          return flgLexerToken(token=self.tables[u'%tokenmap'][token], value=token, location=loc)

        # Otherwise, we'll just let the loop continue with the revealed previous source.

      #-- end: elif sym == -1 and len(self.lookahead[0]) == 1:

      # If we reach this point, we have read tokens up to a state that
      # does not transition # on the current symbol, and we have not
      # passed any accept states.  This is a syntax error.
      else:

        # TODO: is this the right way to handle this?
        # first, we create our %error token, fetching the value and
        # location from the lookahead buffer
        val = u"".join(map(lambda x:x[0], self.lookahead[0]))
        loc = self.lookahead[0][0][1]
        token = flgLexerToken(token=u'%error', value=val, location=loc)

        # Mark us as being in an error state, so that we can try to
        # scanning for a valid token.
        self.error_state = True

        # return the %error token we previously generated.
        return token

  # normally, applications won't call next_token() directly.  They'll
  # use the lexer instance as an iterator and iterate through the tokens.
  # the __iter__ method sets this up, by returning the instance as its
  # own iterator.

  def __iter__(self):
    """Return the lexer itself as its own iterator."""
    return self

  # the next method is the actual iterator:  it calls next_token and
  # repeats calling next_token if the special %skip token is returned.
  # it then raises a StopIteration if next_token returned None because
  # there are no sources to read, or just returns the token.

  def next(self):
    """Iterate through the tokens, skipping the special %skip tokens.  This relies on the next_token() method raising StopIteration when called after end-of-file."""
    tok = self.next_token()
    while tok is not None and tok.token == u'%skip':
      tok = self.next_token()
    if tok is None:
      raise StopIteration("No source exists from which to read tokens.")
    return tok

#
# The module's test progream just creates the lexer and calls it until
# it stops iterating, printing out each token that gets returned.

if __name__ == '__main__':

  l = flgLexer()
  for tok in l:
    print str(tok)
