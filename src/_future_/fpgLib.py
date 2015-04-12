#!/usr/bin/python

import sys

grammar_source = u"""
B <- begin L end
L <- S
L <- S semicolon L
S <- I
S <- E
I <- if E then B
I <- if E then B else B
E <- id
"""

grammar_rules = [(nonterm, tuple(rule.split(' ')), (((action and [eval(action)]) or [None])[0])) for (nonterm, rule, action) in [(nonterm,)+tuple((rule + ' -> ').split(' -> '))[0:2] for (nonterm,rule) in [tuple(rule.split(' <- ')) for rule in grammar_source.split('\n') if len(rule)]]]
grammar_rules = [('%start', (grammar_rules[0][0],), '',)] + grammar_rules

nonterms = [rule[0] for rule in grammar_rules]
nonterms = reduce(lambda a,b:(((b not in a) and (a+(b,))) or (a)), nonterms, ())
tokens = (u'begin', u'end', u'semicolon', u'if', u'then', u'else', u'id')
all_syms = reduce(lambda a,b:a+b, [rule[1] for rule in grammar_rules])
all_syms = reduce(lambda a,b:(((b not in a) and (a+(b,))) or (a)), all_syms, ())
all_syms = tuple(sorted(all_syms, reverse=True))
unused_tokens = [token for token in tokens if token not in all_syms]
unused_syms = [sym for sym in all_syms if sym not in tokens+nonterms]
#print >> sys.stderr, "unused_tokens=" + repr(unused_tokens)
#print >> sys.stderr, "unused_syms  =" + repr(unused_syms  )

# use up token#0 as the special %eof token
tokens = ('%eof',) + tokens

symmap = [(nonterms[i],i) for i in xrange(len(nonterms))] + [(tokens[i],-i) for i in xrange(len(tokens))]
symmap = symmap + [(y,x) for (x,y) in symmap]
symmap = dict(symmap)

grammar_rules = tuple([(symmap[rule[0]],tuple([symmap[s] for s in rule[1]]),rule[2]) for rule in grammar_rules])
nonterm_rules = {}
for i in xrange(len(grammar_rules)):
  nt = grammar_rules[i][0]
  if nt in nonterm_rules:
    nonterm_rules[nt].append(i)
  else:
    nonterm_rules[nt] = [i]

first = {}
for sym in xrange(-len(tokens), len(nonterms)):
  if sym < 0:
    first[sym] = (sym,)
  else:
    first_syms = set()
    rulelist = list(nonterm_rules[sym])
    i = 0
    while i < len(rulelist):
      rule = rulelist[i]
      rsym = grammar_rules[rule][1][0]
      if rsym < 0:
        first_syms.add(rsym)
      else:
        for addrule in nonterm_rules[rsym]:
          if addrule not in rulelist:
            rulelist.append(addrule)
      i += 1
    first[sym] = tuple(first_syms)

def grammar_rule_display( rule ):
  assert (not isinstance(rule,tuple)) or 1 <= len(rule) <= 3
  if not isinstance(rule, tuple):
    rulenum = rule
    dot = None
    lookahead = None
  elif len(rule) == 1:
    rulenum = rule[0]
    dot = None
    lookahead = None
  elif len(rule) == 2:
    (rulenum,dot) = rule
    lookahead = None
  elif len(rule) == 3:
    (rulenum, dot, lookahead) = rule
  (nonterm, rule, action) = grammar_rules[rulenum]
  if lookahead is None:
    lookahead = ""
  else:
    lookahead = "  [%s]" % (",".join(map(lambda s:(((s>0) and nonterms[s]) or tokens[-s]), lookahead)),)
  return "[%d] %s %s%s" % (rulenum, nonterms[nonterm], " ".join(
    ["->" + (((dot==0) and " .") or "")] +
    [
      (
        (((rule[i] > 0) and nonterms[rule[i]]) or tokens[-rule[i]])
        + (((dot == (i+1)) and " .") or "")
      )
      for i in range(0,len(rule))
    ]
    ), lookahead)

states = []
state_map = {}

# the closure of a kernel consists of the kernel, plus, for every kernel item (rule,pos,lookahead) where rule[pos] is a nonterm, a new item for each grammar rule that produces rule[pos], with new dot position 0 and a new lookahead of FIRST(rule[pos+1]) if such exists, or lookahead if not.
def closure(k):
  items = dict( map(lambda (r,d,l):(r,d), k) )
  c = list(k)
  i = 0
  while (i < len(c)):
    (rule,pos,lookahead) = c[i]
    # this could also be > 0, since the start symbol will never appear to the right of a dot
    if pos < len(grammar_rules[rule][1]) and grammar_rules[rule][1][pos] >= 0:
      if pos+1 < len(grammar_rules[rule][1]):
        lookahead = tuple(first[grammar_rules[rule][1][pos+1]])
      for r in nonterm_rules[grammar_rules[rule][1][pos]]:
        if (r,0) in items:
          prev_lookahead = list(c[items[(r,0)]][2])
          for sym in lookahead:
            if sym not in prev_lookahead:
              i = -1 # restart the scan if we add anything
              prev_lookahead.append(sym)
          c[items[(r,0)]] = (r,0,tuple(prev_lookahead))
        else:
          items[(r,0)] = len(c)
          c.append( (r,0,lookahead) )
    i += 1
  return tuple(c)

# kernel is a list of items.
# an item is a tuple of (rule#, dot#, (syms...)), where (syms...) is lookahead set for the item.
def gen_parser_states( kernel ):
  state = len(states)
  state_map[kernel] = state
  states.append({'kernel':kernel})

  c = closure(kernel)
  #print >> sys.stderr, "Generating parser state %d for closure:\n%s" % (state, "\n".join(map(grammar_rule_display, c)))

  # generate gotos
  gotos = {}
  for (rule,pos,lookahead) in c:
    grule = grammar_rules[rule]
    if pos < len(grule[1]):
      # add to goto table
      if grule[1][pos] not in gotos:
        gotos[grule[1][pos]] = []
      gotos[grule[1][pos]].append( (rule,pos+1,lookahead) )

  # generate actions
  actions = {}
  states[state]['actions'] = actions
  # one reduce action for each lookeahead symbol in kernel item where dot is at the end...
  for (rule,pos,lookahead) in kernel:
    grule = grammar_rules[rule]
    if pos == len(grule[1]):
      for sym in lookahead:
        if sym not in actions:
          actions[sym] = []
        actions[sym].append(-rule) # reduce rule
  # one accept, shift, or goto action for each goto entry...
  for (sym,goto_kernel) in gotos.items():
    goto_kernel = tuple(goto_kernel)
    if goto_kernel in state_map:
      goto_state = state_map[goto_kernel]
    else:
      goto_state = gen_parser_states(goto_kernel)
    if sym not in actions:
      actions[sym] = []
    actions[sym].append(goto_state)

  return state

# generate the parser tables by starting with the initial state: rule 0 (%start <- [nonterm]) at position 0 with lookahead of %eof
init_state = gen_parser_states( ((0,0,(symmap['%eof'],)),) )

if len(sys.argv) == 1:
  sys.argv.append('tables')

for arg in sys.argv[1:]:
  if arg[0:2] == '--':
    arg = arg[2:]
  if arg.startswith('table'):

# dump the parser tables
# we include:
#   actionmap = map of (state,symbol) -> action
#   action is an integer as follows:
#       0 - accept and halt, we're done
#      >0 - a state to shift to
#      <0 - a negative rule number to reduce  (e.g. -5 means reduce rule [5])
#   actionmap[None] points to the initial state.
# for debugging, we also include:
#   tokens = the list of tokens represented by negative numbers in the rules list
#   nonterms = the list of nonterms represented by non-negative numbers in the rules list
#   rules = the list of rules, where each rule of the form "nonterm <- alpha beta gamma... -> action" is represented by (nonterm,(alpha,beta,gamma,...),(action...)) where nonterm,alpha,etc. are the numeric representations of the nonterms and tokens, and (action...) is the parse tree representation of the action expression.

    actions = {}

    for i in xrange(len(states)):
      state = states[i]
      for (sym,action) in state['actions'].items():
        actions[i,sym] = action[0]

    actions[None] = init_state

    def short_repr(foo):
      if isinstance(foo,dict):
        return '{' + ",".join(["%s:%s" % (short_repr(k),short_repr(v)) for (k,v) in foo.items()]) + '}'
      elif isinstance(foo,tuple):
        return '(' + ",".join([short_repr(v) for (v) in foo]) + (((len(foo)==1) and ',)') or ')')
      elif isinstance(foo,list):
        return '[' + ",".join([short_repr(v) for (v) in foo]) + ']'
      else:
        return repr(foo)

    print "  actions=" + short_repr(actions)
    print "  tokens=" + short_repr(tokens)
    print "  nonterms=" + short_repr(nonterms)
    print "  rules=" + short_repr(grammar_rules)

  elif arg.startswith('sed'):
    for i in range(1,len(tokens)):
      print "s/'%s'/%d/g" % (tokens[i],i)

  else:

    for i in xrange(len(states)):
      print ""
      state = states[i]
      c = closure(state['kernel'])
      print "State %d:" % (i,)
      for item in c:
        print "  %s" % (grammar_rule_display( item ),)
      print ""
      conflicts = []
      for (sym,action) in sorted(state['actions'].items()):
        if len(action) > 1:
          conflicts.append("/".join(map(lambda s:(((s<0) and "reduce") or "shift"), action)))
        action = action[0]
        if action < 0:
          action = "reduce [%d]" % (-action,)
        elif action == 0:
          action = "accept"
        elif sym < 0:
          action = "shift %d" % (action,)
        else:
          action = "goto %d" % (action,)
        if sym > 0:
          sym = nonterms[sym]
        else:
          sym = tokens[-sym]
        print "  %s %s" % (sym,action)
      if len(conflicts):
        print ""
        for conflict in conflicts:
          print "  %s conflict" % (conflict,)
