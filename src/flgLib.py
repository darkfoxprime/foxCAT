#!/usr/bin/python
# flgLib - library of classes used by flg

import sys
import traceback

class State(object):
  """A State describes one state that a state machine can be in.  Each State
has an optional token that is accepted at that state, and a list of 0
or more Transitions to other states."""
  __statenum = 0

  def __init__(self):
    self.accepts = None
    self.nexttable = None
    self.transitions = []
    State.__statenum += 1
    self.__statenum = State.__statenum

  def __hash__(self):
    hval = int(reduce(lambda a,b:a+hash(b), self.transitions, hash(self.accepts))) % 2**32
    return hval

  def __str__(self):
    acc = ""
    if self.accepts is not None:
      acc = "(%s)" % (str(self.accepts),)
    trans = ""
    mytb = traceback.extract_stack(None, 1)[0]
    mytb = (mytb[0], mytb[1] + 3, mytb[2])
    if traceback.extract_stack(None,3)[0][0:3] != mytb:
      trans = ";".join(map(str, self.transitions))
    else:
      trans = "..."
    return "State#%d%s[%s]" % (self.__statenum, acc, trans)

  def __repr__(self):
    acc = ""
    if self.accepts is not None:
      acc = "(%s)" % (str(self.accepts),)
    nxt= ""
    if self.nexttable is not None:
      nxt = "@%s" % (str(self.nexttable),)
    return "State#%d%s%s" % (self.__statenum, acc, nxt)

  def __lt__(self,other):
    if isinstance(other,State):
      return self.__statenum < other.__statenum
    else:
      return id(self) < id(other)

  def __eq__(self,other):
    if isinstance(other,State):
      return self.accepts == other.accepts and sorted(self.transitions) == sorted(other.transitions)
    else:
      return id(self) == id(other)

  def transition(self, event, target):
    self.transitions.append(Transition(event,target))

class Transition(object):
  def __init__(self, event, target):
    self.event = event
    self.target = target

  def __str__(self):
    return "%s->%s" % (repr(self.event),str(self.target))

  def __repr__(self):
    return "Transition" + repr( (self.event, self.target) )

  def __hash__(self):
    return int(hash(self.event) + id(self.target)) % 2**32

  def __eq__(self,other):
    if isinstance(other,Transition):
      return self.event == other.event and id(self.target) == id(other.target)
    else:
      return id(self) == id(other)

class NFA2DFAException(Exception):
  pass

class StateMachine(object):

  def __init__(self, startState=None):
    if startState is None:
      startState = State()
    self.start = startState

  def _stateMap(self, start=None):
    if start is None:
      start = self.start
    stateMap = {}
    pending = [start]
    while len(pending) > 0:
      s = pending.pop()
      stateMap[s] = len(stateMap)
      for t in s.transitions:
        if t.target not in stateMap and t.target not in pending:
          pending.append(t.target)
    return stateMap

  def _asDict(self, start=None):
    if start is None:
      start = self.start
    return dict(((None, start),) + tuple([(state,tuple(state.transitions)) for state in self._stateMap(start).keys()]))

  def startState(self):
    return self.start

  def acceptStates(self):
    states = self._stateMap()
    statesThatAccept = [state for state in states.keys() if state.accepts is not None]
    return statesThatAccept

  def toTable(self, start=None):
    states = self._stateMap(start)
    stateTable = [None] * len(states)
    for (state,num) in states.items():
      transitions = {}
      for t in state.transitions:
        if t.event not in transitions:
          transitions[t.event] = ()
        transitions[t.event] += (states[t.target],)
      if state.accepts is None:
        acc = None
      elif state.nexttable is None:
        acc = state.accepts
      else:
        acc = (state.accepts, state.nexttable)
      stateTable[num] = (acc, tuple(sorted(transitions.items())))
    # if all stateTable item transitions only have a single target, un-tuplify the target lists
    maxTargets = 0
    for s in range(len(stateTable)):
      for (event,targets) in stateTable[s][1]:
        if len(targets) > maxTargets:
          maxTargets = len(targets)
    if maxTargets == 1:
      stateTable = [(acc,tuple([(event,targets[0]) for (event,targets) in transitions])) for (acc,transitions) in stateTable]
    return stateTable

  # some convenience functions

  @staticmethod
  def makeNFACharClass(*symRanges):
    """Returns a 2ple of (State, State) where the two states are the start and end state, respectively, of the character class recognizer NFA"""
    s1 = State()
    s2 = State()
    for sr in symRanges:
      s1.transitions.append(Transition(sr, s2))
    return (s1, s2)

  @staticmethod
  def makeNFAStar(nfa):
    """Returns a 2ple of (State, State) where the two states are the start and end state, respectively, of the '*' recognizer for the passed-in nfa"""
    s1 = State()
    s2 = State()
    s1.transitions.append(Transition(None, s2))
    s1.transitions.append(Transition(None, nfa[0]))
    s2.transitions.append(Transition(None, s1))
    nfa[1].transitions.append(Transition(None, s2))
    return (s1, s2)

  @staticmethod
  def makeNFAPlus(nfa):
    """Returns a 2ple of (State, State) where the two states are the start and end state, respectively, of the '+' recognizer for the passed-in nfa"""
    s1 = State()
    s2 = State()
    s1.transitions.append(Transition(None, nfa[0]))
    s2.transitions.append(Transition(None, s1))
    nfa[1].transitions.append(Transition(None, s2))
    return (s1, s2)

  @staticmethod
  def makeNFAQuestion(nfa):
    """Returns a 2ple of (State, State) where the two states are the start and end state, respectively, of the '?' recognizer for the passed-in nfa"""
    s1 = State()
    s2 = State()
    s1.transitions.append(Transition(None, s2))
    s1.transitions.append(Transition(None, nfa[0]))
    nfa[1].transitions.append(Transition(None, s2))
    return (s1, s2)

  @staticmethod
  def makeNFAGroup(nfa):
    """Returns a 2ple of (State, State) where the two states are the start and end state, respectively, of the grouping recognizer for the passed-in nfa"""
    s1 = State()
    s2 = State()
    s1.transitions.append(Transition(None, nfa[0]))
    nfa[1].transitions.append(Transition(None, s2))
    return (s1,s2)

  @staticmethod
  def makeNFASequence(*nfas):
    """Returns a 2ple of (State, State) where the two states are the start and end state, respectively, of the joined sequence recognizer for the passed-in nfas"""
    (s1,s2) = nfas[0]
    for i in range(1,len(nfas)):
      s2.transitions.append(Transition(None, nfas[i][0]))
      s2 = nfas[i][1]
    return (s1,s2)

  @staticmethod
  def makeNFAAlternates(*nfas):
    """Returns a 2ple of (State, State) where the two states are the start and end state, respectively, of the set-of-alternates recognizer for the passed-in nfas"""
    s1 = State()
    s2 = State()
    for asm in nfas:
      s1.transitions.append(Transition(None, asm[0]))
      asm[1].transitions.append(Transition(None, s2))
    return (s1,s2)

  @staticmethod
  def makeNFAAcceptor(token, nfa, nexttable=None):
    """Returns a 2ple of (State, State) where the two states are the start and end state, respectively, of the token acceptor for the passed-in nfa"""
    s1 = State()
    s2 = State()
    s2.accepts = token
    s2.nexttable = nexttable
    s1.transitions.append(Transition(None, nfa[0]))
    nfa[1].transitions.append(Transition(None, s2))
    return (s1,s2)


# return the closure of a set of states.
#
# the closure for a set of states is a list of states that includes the
# original set of states, and every state that can be reached from one of
# those states by only epsilon transitions.
  @staticmethod
  def _nfa2dfa_closure(states):
    states = list(states)
    newstates = []
    while len(states) > 0:
      s = states.pop()
      newstates.append(s)
      states.extend([t.target for t in s.transitions if t.event is None and t.target not in states and t.target not in newstates])
    return tuple(sorted(newstates))

# return the token that is accepted by a set of states.
# Raise an NFA2DFAException if more than one accepted token is found.
  @staticmethod
  def _nfa2dfa_accepts(states):
    astates = filter(lambda s:s.accepts is not None, states)
    if len(astates) > 1:
      raise NFA2DFAException("%d accept states (more than 1) found in state set %s" % (len(astates), repr(states)))
    if len(astates) == 0:
      return None
    if astates[0].nexttable is not None:
      return (astates[0].accepts, astates[0].nexttable)
    return astates[0].accepts

# return the minimal list of distinct symbol ranges and target states
# that cover all symbol ranges found in the closure.
# each distinct symbol range will be paired with the closure of the list
# of target states reachable by that symbol range.
# this covers the "goto" function in the original nfa->dfa algorithm.
  @staticmethod
  def _nfa2dfa_ranges(states):
    # ranges will be a list of ( (symfirst,symlast), [targets])
    # ranges will be kept in sorted order such that each symfirst is
    # greater than the symlast of the previous range, and each symlast is
    # less than the symfirst of the next range.
    ranges = []
    for s in states:
      for ((symfirst,symlast),target) in [(t.event,t.target) for t in s.transitions if t.event is not None]:
        i = 0
        while symfirst is not None and i < len(ranges):
          # if symlast is less than symfirst of ranges[i],
          # then this is where we insert this new range
          if symlast < ranges[i][0][0]:
            ranges.insert(i, ((symfirst, symlast), [target]))
            # set symfirst to None to mark that we're done
            symfirst = None
            # and break out of the loop
            break

          # if symfirst is <= symfirst of ranges[i], then we need to split
          # the first part of our range off and insert it
          if symfirst < ranges[i][0][0]:
            ranges.insert(i, ((symfirst, ranges[i][0][0]-1), [target]))
            symfirst = ranges[i+1][0][0]
            # shift to the newly split range
            i += 1

          # if symfirst is <= symlast of ranges[i], then we overlap this range.
          if symfirst <= ranges[i][0][1]:
            # handle the overlap in four phases:

            # first, split ranges[i] before symfirst, if symfirst is
            # greater than symfirst of ranges[i].  if we do this,
            # immediately increment i.
            # make sure to use a _copy_ of the list of targets in the split
            # range, not just the list reference.
            if symfirst > ranges[i][0]:
              ranges.insert(i+1, ( (symfirst, ranges[i][0][1]), ranges[i][1][:]))
              ranges[i] = ((ranges[i][0][0], symfirst-1), ranges[i][1])
              i += 1

            # second, split ranges[i] after symlast, if symlast is less
            # than symlast of ranges[i].
            # make sure to use a _copy_ of the list of targets in the split
            # range, not just the list reference.
            if symlast < ranges[i][0][1]:
              ranges.insert(i+1, ( (symlast+1, ranges[i][0][1]), ranges[i][1][:]))
              ranges[i] = ((symfirst, symlast), ranges[i][1])

            # third, add our target to the current range target
            ranges[i][1].append(target)

            # finally, either split our symrange, if symlast is greater than
            # symlast of ranges[i], or mark our symrange as None.
            if symlast > ranges[i][0][1]:
              symfirst = ranges[i][0][0] + 1
            else:
              symfirst = None

          # increment i for the while loop
          i += 1

        # if symfirst is still not None, then we need to add our range to
        # end of the range list.
        if symfirst is not None:
          ranges.append( ((symfirst, symlast), [target]) )
    
    ranges = tuple( [ ((symfirst,symlast),StateMachine._nfa2dfa_closure(targets)) for ((symfirst,symlast),targets) in ranges ] )
    return ranges


  @staticmethod
  def _nfa2dfa_process(states, closures={}):
    states = StateMachine._nfa2dfa_closure(states)
    if states not in closures:
      state = State()
      closures[states] = state
      state.accepts = StateMachine._nfa2dfa_accepts(states)
      for ((symfirst,symlast),targets) in StateMachine._nfa2dfa_ranges(states):
        target_state = StateMachine._nfa2dfa_process(targets, closures)
        state.transitions.append(Transition( (symfirst, symlast), target_state ))
    return closures[states]

  def toDFA(self, start=None):
    """returns a DFA that is equivalent to this state machine.  This means:  All epsilon (None) transitions are eliminated, and no state has two transitions that both match the same symbol."""
    if start is None:
      start = self.start
    return StateMachine(self._nfa2dfa_process( (start,) )).compact(start)

  def compact(self, start=None):
    """Compacts a DFA state machine to remove duplicate states (identical acceptances and transitions).  DO NOT run this on an NFA, as it will corrupt the NFA."""
    seen_ids = []
    seen = {}
    replacements ={}
    if start is None:
      start = self.start
    pending = [start]
    while len(pending):
      s = pending.pop()
      if id(s) not in seen_ids:
        seen_ids.append(id(s))
        if s in seen:
          replacements[s] = seen[s]
        else:
          seen[s] = s
          for t in s.transitions:
            pending.append(t.target)
    for (orig,replacement) in replacements.items():
      for state in seen.keys():
        for t in state.transitions:
          if id(t.target) == id(orig):
            t.target = replacement
    return self

if __name__ == '__main__':

#####

  tokens = (u'%eof', u'C_TOKEN', u'C_DIRECTIVE', u'C_EQUALS', u'C_NUMBER', u'C_POS_PARAM', u'C_QUOTEDSTR', u'C_PAREN_OPEN', u'C_PAREN_CLOSE', u'C_COMMA', u'C_PLUS', u'C_MINUS', u'C_TIMES', u'C_DIVIDE', u'C_MODULO', u'C_DERIVES', u'C_ACTION', u'L_RX_START', u'L_RX_END', u'L_RX_ALTERNATE', u'L_RX_PLUS', u'L_RX_QUESTION', u'L_RX_STAR', u'L_RX_ATOM', u'L_RX_CHARCLASS', u'L_RX_CC_CHAR', u'L_RX_CC_END', u'L_RX_CC_RANGE', u'L_RX_GRP_CLOSE', u'L_RX_GRP_OPEN',)
  tokenmap = dict(tuple([(tokens[i],i) for i in range(len(tokens))]))

  tables = {}

#####

  sm = StateMachine()
  smsst = sm.startState().transitions

# %skip /:\)/ -> pop(comment)

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'%skip',u'%skip'),
    StateMachine.makeNFASequence(
      StateMachine.makeNFACharClass( (58,58) ),
      StateMachine.makeNFACharClass( (41,41) ),
    ),
    nexttable = (u'(', u'pop', (u'comment',))
  )
  smsst.append(Transition(None, rule[0]))

# %skip /./

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'%skip',u'%skip'),
    StateMachine.makeNFACharClass( (0,9), (11,2097151) ),
  )
  smsst.append(Transition(None, rule[0]))

# %skip /\n/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'%skip',u'%skip'),
    StateMachine.makeNFACharClass( (10,10) ),
  )
  smsst.append(Transition(None, rule[0]))

#####

  tables[u'comment'] = sm.toDFA().toTable()

#####

  sm = StateMachine()
  smsst = sm.startState().transitions

# C_TOKEN /[A-Za-z_][A-Za-z0-9_]*/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_TOKEN',u'C_TOKEN'),
    StateMachine.makeNFASequence(
      StateMachine.makeNFACharClass( (65,90), (95,95), (97,122) ),
      StateMachine.makeNFAStar(
        StateMachine.makeNFACharClass( (48,57), (65,90), (95,95), (97,122) ),
      ),
    ),
  )
  smsst.append(Transition(None, rule[0]))

# C_DIRECTIVE /%[a-z]+/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_DIRECTIVE',u'C_DIRECTIVE'),
    StateMachine.makeNFASequence(
      StateMachine.makeNFACharClass( (37,37) ),
      StateMachine.makeNFAPlus(
        StateMachine.makeNFACharClass( (97,122) ),
      ),
    ),
  )
  smsst.append(Transition(None, rule[0]))

# C_EQUALS /=/ -> push(expression)

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_EQUALS',u'C_EQUALS'),
    StateMachine.makeNFACharClass( (61,61) ),
  )
  smsst.append(Transition(None, rule[0]))

# C_NUMBER /[-+]?[0-9]+/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_NUMBER',u'C_NUMBER'),
    StateMachine.makeNFASequence(
      StateMachine.makeNFAStar(
        StateMachine.makeNFACharClass( (43,43), (45,45) ),
      ),
      StateMachine.makeNFAPlus(
        StateMachine.makeNFACharClass( (48,57) ),
      ),
    ),
  )
  smsst.append(Transition(None, rule[0]))

# C_POS_PARAM /\$[0-9]+/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_POS_PARAM',u'C_POS_PARAM'),
    StateMachine.makeNFASequence(
      StateMachine.makeNFACharClass( (36,36) ),
      StateMachine.makeNFAPlus(
        StateMachine.makeNFACharClass( (48,57) ),
      ),
    ),
  )
  smsst.append(Transition(None, rule[0]))

# C_QUOTEDSTR /(("(\\.|[^"\\])*")|('(\\.|[^'\\])*'))+/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_QUOTEDSTR',u'C_QUOTEDSTR'),
    StateMachine.makeNFAPlus(
      StateMachine.makeNFAGroup(
        StateMachine.makeNFAAlternates(
          StateMachine.makeNFAGroup(
            StateMachine.makeNFASequence(
              StateMachine.makeNFACharClass( (34,34) ),
              StateMachine.makeNFAStar(
                StateMachine.makeNFAGroup(
                  StateMachine.makeNFAAlternates(
                    StateMachine.makeNFASequence(
                      StateMachine.makeNFACharClass( (92,92) ),
                      StateMachine.makeNFACharClass( (0,9), (11,2097151) ),
                    ),
                    StateMachine.makeNFACharClass( (0,33), (35,91), (93,2097151) ),
                  ),
                ),
              ),
              StateMachine.makeNFACharClass( (34,34) ),
            ),
          ),
          StateMachine.makeNFAGroup(
            StateMachine.makeNFASequence(
              StateMachine.makeNFACharClass( (39,39) ),
              StateMachine.makeNFAStar(
                StateMachine.makeNFAGroup(
                  StateMachine.makeNFAAlternates(
                    StateMachine.makeNFASequence(
                      StateMachine.makeNFACharClass( (92,92) ),
                      StateMachine.makeNFACharClass( (0,9), (11,2097151) ),
                    ),
                    StateMachine.makeNFACharClass( (0,38), (40,91), (93,2097151) ),
                  ),
                ),
              ),
              StateMachine.makeNFACharClass( (39,39) ),
            ),
          ),
        ),
      ),
    ),
  )
  smsst.append(Transition(None, rule[0]))

# C_PAREN_OPEN /\(/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_PAREN_OPEN',u'C_PAREN_OPEN'),
    StateMachine.makeNFACharClass( (40,40) ),
  )
  smsst.append(Transition(None, rule[0]))

# C_PAREN_CLOSE /\)/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_PAREN_CLOSE',u'C_PAREN_CLOSE'),
    StateMachine.makeNFACharClass( (41,41) ),
  )
  smsst.append(Transition(None, rule[0]))

# C_COMMA /,/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_COMMA',u'C_COMMA'),
    StateMachine.makeNFACharClass( (44,44) ),
  )
  smsst.append(Transition(None, rule[0]))

# C_DERIVES /<-/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_DERIVES',u'C_DERIVES'),
    StateMachine.makeNFASequence(
      StateMachine.makeNFACharClass( (60,60) ),
      StateMachine.makeNFACharClass( (45,45) ),
    ),
  )
  smsst.append(Transition(None, rule[0]))

# C_ACTION /->/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_ACTION',u'C_ACTION'),
    StateMachine.makeNFASequence(
      StateMachine.makeNFACharClass( (45,45) ),
      StateMachine.makeNFACharClass( (62,62) ),
    ),
    nexttable=(u'(', u'push', (u'expression',))
  )
  smsst.append(Transition(None, rule[0]))

# %skip /\(:/ -> push(comment)

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'%skip',u'%skip'),
    StateMachine.makeNFASequence(
      StateMachine.makeNFACharClass( (40,40) ),
      StateMachine.makeNFACharClass( (58,58) ),
    ),
    nexttable=(u'(', u'push', (u'comment',))
  )
  smsst.append(Transition(None, rule[0]))

# L_RX_START /\// -> regexp

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'L_RX_START',u'L_RX_START'),
    StateMachine.makeNFACharClass( (47,47) ),
    nexttable=u'regexp'
  )
  smsst.append(Transition(None, rule[0]))

# _skip_ /[ \t\n]+/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'%skip',u'%skip'),
    StateMachine.makeNFAPlus(
      StateMachine.makeNFACharClass( (9,10), (32,32) ),
    ),
  )
  smsst.append(Transition(None, rule[0]))

#####

  tables[u'normal'] = sm.toDFA().toTable()

#####

  sm = StateMachine()
  smsst = sm.startState().transitions

# C_PLUS /\+/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_PLUS',u'C_PLUS'),
    StateMachine.makeNFACharClass( (43,43) ),
  )
  smsst.append(Transition(None, rule[0]))

# C_MINUS /-/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_MINUS',u'C_MINUS'),
    StateMachine.makeNFACharClass( (45,45) ),
  )
  smsst.append(Transition(None, rule[0]))

# C_TIMES /\*/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_TIMES',u'C_TIMES'),
    StateMachine.makeNFACharClass( (42,42) ),
  )
  smsst.append(Transition(None, rule[0]))

# C_DIVIDE /\//

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_DIVIDE',u'C_DIVIDE'),
    StateMachine.makeNFACharClass( (47,47) ),
  )
  smsst.append(Transition(None, rule[0]))

# C_MODULO /\%/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_MODULO',u'C_MODULO'),
    StateMachine.makeNFACharClass( (37,37) ),
  )
  smsst.append(Transition(None, rule[0]))

# C_TOKEN /[A-Za-z_][A-Za-z0-9_]*/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_TOKEN',u'C_TOKEN'),
    StateMachine.makeNFASequence(
      StateMachine.makeNFACharClass( (65,90), (95,95), (97,122) ),
      StateMachine.makeNFAStar(
        StateMachine.makeNFACharClass( (48,57), (65,90), (95,95), (97,122) ),
      ),
    ),
  )
  smsst.append(Transition(None, rule[0]))

# C_EQUALS /=/ -> push(expression)

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_EQUALS',u'C_EQUALS'),
    StateMachine.makeNFACharClass( (61,61) ),
  )
  smsst.append(Transition(None, rule[0]))

# C_NUMBER /[-+]?[0-9]+/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_NUMBER',u'C_NUMBER'),
    StateMachine.makeNFASequence(
      StateMachine.makeNFAStar(
        StateMachine.makeNFACharClass( (43,43), (45,45) ),
      ),
      StateMachine.makeNFAPlus(
        StateMachine.makeNFACharClass( (48,57) ),
      ),
    ),
  )
  smsst.append(Transition(None, rule[0]))

# C_POS_PARAM /\$[0-9]+/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_POS_PARAM',u'C_POS_PARAM'),
    StateMachine.makeNFASequence(
      StateMachine.makeNFACharClass( (36,36) ),
      StateMachine.makeNFAPlus(
        StateMachine.makeNFACharClass( (48,57) ),
      ),
    ),
  )
  smsst.append(Transition(None, rule[0]))

# C_QUOTEDSTR /(("(\\.|[^"])*")|('(\\.|[^'])*'))+/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_QUOTEDSTR',u'C_QUOTEDSTR'),
    StateMachine.makeNFAPlus(
      StateMachine.makeNFAGroup(
        StateMachine.makeNFAAlternates(
          StateMachine.makeNFAGroup(
            StateMachine.makeNFASequence(
              StateMachine.makeNFACharClass( (34,34) ),
              StateMachine.makeNFAStar(
                StateMachine.makeNFAGroup(
                  StateMachine.makeNFAAlternates(
                    StateMachine.makeNFASequence(
                      StateMachine.makeNFACharClass( (92,92) ),
                      StateMachine.makeNFACharClass( (0,9), (11,2097151) ),
                    ),
                    StateMachine.makeNFACharClass( (0,33), (35,91), (93,2097151) ),
                  ),
                ),
              ),
              StateMachine.makeNFACharClass( (34,34) ),
            ),
          ),
          StateMachine.makeNFAGroup(
            StateMachine.makeNFASequence(
              StateMachine.makeNFACharClass( (39,39) ),
              StateMachine.makeNFAStar(
                StateMachine.makeNFAGroup(
                  StateMachine.makeNFAAlternates(
                    StateMachine.makeNFASequence(
                      StateMachine.makeNFACharClass( (92,92) ),
                      StateMachine.makeNFACharClass( (0,9), (11,2097151) ),
                    ),
                    StateMachine.makeNFACharClass( (0,38), (40,91), (93,2097151) ),
                  ),
                ),
              ),
              StateMachine.makeNFACharClass( (39,39) ),
            ),
          ),
        ),
      ),
    ),
  )
  smsst.append(Transition(None, rule[0]))

# C_PAREN_OPEN /\(/ -> push(expression)

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_PAREN_OPEN',u'C_PAREN_OPEN'),
    StateMachine.makeNFACharClass( (40,40) ),
  )
  smsst.append(Transition(None, rule[0]))

# C_PAREN_CLOSE /\)/ -> pop(expression)

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_PAREN_CLOSE',u'C_PAREN_CLOSE'),
    StateMachine.makeNFACharClass( (41,41) ),
  )
  smsst.append(Transition(None, rule[0]))

# C_COMMA /,/ -> pop(expression)

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'C_COMMA',u'C_COMMA'),
    StateMachine.makeNFACharClass( (44,44) ),
  )
  smsst.append(Transition(None, rule[0]))

# _skip_ /[ \t]+/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'%skip',u'%skip'),
    StateMachine.makeNFAPlus(
      StateMachine.makeNFACharClass( (9,9), (32,32) ),
    ),
  )
  smsst.append(Transition(None, rule[0]))

# _skip_ /\n/ -> pop(expression)

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'%skip',u'%skip'),
    StateMachine.makeNFAPlus(
      StateMachine.makeNFACharClass( (10,10) ),
    ),
    nexttable = (u'(',u'pop', (u'expression',))
  )
  smsst.append(Transition(None, rule[0]))

#####

  tables[u'expression'] = sm.toDFA().toTable()

#####

  sm = StateMachine()
  smsst = sm.startState().transitions

# L_RX_END /\// -> normal

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'L_RX_END',u'L_RX_END'),
    StateMachine.makeNFACharClass( (47,47) ),
    nexttable=u'normal'
  )
  smsst.append(Transition(None, rule[0]))

# L_RX_CHARCLASS /\[^?\]?-?/ -> charclass

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'L_RX_CHARCLASS',u'L_RX_CHARCLASS'),
    StateMachine.makeNFASequence(
      StateMachine.makeNFACharClass( (91,91) ),
      StateMachine.makeNFAQuestion(
        StateMachine.makeNFACharClass( (94,94) ),
      ),
      StateMachine.makeNFAQuestion(
        StateMachine.makeNFACharClass( (93,93) ),
      ),
      StateMachine.makeNFAQuestion(
        StateMachine.makeNFACharClass( (45,45) ),
      ),
    ),
    nexttable = u'charclass'
  )
  smsst.append(Transition(None, rule[0]))

# L_RX_ATOM /(\\(x[0-9a-fA-F][0-9a-fA-F]|[0-7][0-7][0-7]|u[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]|U[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]|[^x0-7uU]))|[^/\\\[|*?+()]/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'L_RX_ATOM',u'L_RX_ATOM'),
    StateMachine.makeNFAAlternates(
      StateMachine.makeNFAGroup(
        StateMachine.makeNFASequence(
          StateMachine.makeNFACharClass( (92,92) ),
          StateMachine.makeNFAGroup(
            StateMachine.makeNFAAlternates(
              StateMachine.makeNFASequence(
                StateMachine.makeNFACharClass( (48,55) ),
                StateMachine.makeNFACharClass( (48,55) ),
                StateMachine.makeNFACharClass( (48,55) ),
              ),
              StateMachine.makeNFASequence(
                StateMachine.makeNFACharClass( (117,117) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
              ),
              StateMachine.makeNFASequence(
                StateMachine.makeNFACharClass( (85,85) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
              ),
              StateMachine.makeNFACharClass( (0,47), (56,84), (86,116), (118,119), (121,0x1FFFFF) ),
            )
          )
        )
      ),
      StateMachine.makeNFACharClass( (0,39),(44,46),(48,62),(64,90),(93,123),(125,0x1FFFFF) ),
    )
  )
  smsst.append(Transition(None, rule[0]))

# L_RX_ALTERNATE /\|/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'L_RX_ALTERNATE',u'L_RX_ALTERNATE'),
    StateMachine.makeNFACharClass( (124,124) )
  )
  smsst.append(Transition(None, rule[0]))

# L_RX_STAR /\*/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'L_RX_STAR',u'L_RX_STAR'),
    StateMachine.makeNFACharClass( (42,42) )
  )
  smsst.append(Transition(None, rule[0]))

# L_RX_QUESTION /\?/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'L_RX_QUESTION',u'L_RX_QUESTION'),
    StateMachine.makeNFACharClass( (63,63) )
  )
  smsst.append(Transition(None, rule[0]))

# L_RX_PLUS /\+/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'L_RX_PLUS',u'L_RX_PLUS'),
    StateMachine.makeNFACharClass( (43,43) )
  )
  smsst.append(Transition(None, rule[0]))

# L_RX_GRP_OPEN /\(/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'L_RX_GRP_OPEN',u'L_RX_GRP_OPEN'),
    StateMachine.makeNFACharClass( (40,40) )
  )
  smsst.append(Transition(None, rule[0]))

# L_RX_GRP_CLOSE /\)/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'L_RX_GRP_CLOSE',u'L_RX_GRP_CLOSE'),
    StateMachine.makeNFACharClass( (41,41) )
  )
  smsst.append(Transition(None, rule[0]))

#####

  tables[u'regexp'] = sm.toDFA().toTable()

#####

  sm = StateMachine()
  smsst = sm.startState().transitions

# L_RX_CC_CHAR /(\\(x[0-9a-fA-F][0-9a-fA-F]|[0-7][0-7][0-7]|u[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]|U[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]|[^x0-7uU]))|[^\\-\]]/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'L_RX_CC_CHAR',u'L_RX_CC_CHAR'),
    StateMachine.makeNFAAlternates(
      StateMachine.makeNFAGroup(
        StateMachine.makeNFASequence(
          StateMachine.makeNFACharClass( (92,92) ),
          StateMachine.makeNFAGroup(
            StateMachine.makeNFAAlternates(
              StateMachine.makeNFASequence(
                StateMachine.makeNFACharClass( (48,55) ),
                StateMachine.makeNFACharClass( (48,55) ),
                StateMachine.makeNFACharClass( (48,55) ),
              ),
              StateMachine.makeNFASequence(
                StateMachine.makeNFACharClass( (117,117) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
              ),
              StateMachine.makeNFASequence(
                StateMachine.makeNFACharClass( (85,85) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
                StateMachine.makeNFACharClass( (48,57), (97,102), (65,70) ),
              ),
              StateMachine.makeNFACharClass( (0,47), (56,84), (86,116), (118,119), (121,0x1FFFFF) ),
            )
          )
        )
      ),
      StateMachine.makeNFACharClass( (0,44), (46,91), (94,0x1FFFFF) )
    )
  )
  smsst.append(Transition(None, rule[0]))

# L_RX_CC_RANGE /-/

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'L_RX_CC_RANGE',u'L_RX_CC_RANGE'),
    StateMachine.makeNFACharClass( (45,45) )
  )
  smsst.append(Transition(None, rule[0]))

# L_RX_CC_END /]/ -> regexp

  rule = StateMachine.makeNFAAcceptor(tokenmap.get(u'L_RX_CC_END',u'L_RX_CC_END'),
    StateMachine.makeNFACharClass( (93,93) ),
    nexttable=u'regexp'
  )
  smsst.append(Transition(None, rule[0]))

#####

  tables[u'charclass'] = sm.toDFA().toTable()

#####

  def short_repr(foo):
    if isinstance(foo,dict):
      return '{' + ",".join(["%s:%s" % (short_repr(k),short_repr(v)) for (k,v) in foo.items()]) + '}'
    elif isinstance(foo,tuple):
      return '(' + ",".join([short_repr(v) for (v) in foo]) + (((len(foo)==1) and ',)') or ')')
    elif isinstance(foo,list):
      return '[' + ",".join([short_repr(v) for (v) in foo]) + ']'
    else:
      return repr(foo)

  tables['%initial'] = 'normal'
  tables['%tokens'] = tokens
  tables['%tokenmap'] = tokenmap

  print "  tables={"
  for (key,val) in tables.items():
    print "    %s:%s," % (short_repr(key),short_repr(val))
  print "  }"


  sys.exit(0)
