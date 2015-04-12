
import sys
from fpgLexer import *
from fpgParser import *
from commonLib import *

DEBUGGING_PARSER = False
DEBUGGING_LEXER = False

class fpgLexerDriver(fpgLexer):
  def processToken(self, token, table, nexttable):
    return token

  if DEBUGGING_LEXER:
    def debug(self, token, table, nexttable):
      print >> sys.stderr, "%s:%s.%s = %s(%s)" % (token.location[u'file'], token.location[u'line'], token.location[u'char'], token.token, token.value)
  else:
    def debug(self, token, table, nexttable):
      pass


class fpgParserDriver(fpgParser,commonLib):

  def _error_recovery(self, states, values, seen, lookahead):
    print >> sys.stderr, "*** Encountered parser error:"
    print >> sys.stderr, "* state stack = " + repr(states)
    print >> sys.stderr, "* values stack = " + repr(values)
    print >> sys.stderr, "* seen buffer = " + repr(seen)
    print >> sys.stderr, "* lookahead buffer = " + repr(lookahead)
    sys.exit(1)

  if DEBUGGING_PARSER:
    def debug_rule_text(self, rulenum):
      rule = self.tables['rules'][rulenum]
      return "[%d] %s <- %s" % (rulenum, self.tables['nonterms'][rule[0]], " ".join([(((sym > 0) and self.tables['nonterms'][sym]) or self.tables['tokens'][-sym]) for sym in rule[1]]))
    def debug(self, rule, states, values, lookahead, action):
      print >> sys.stderr, "Reducing rule %s\n> states=%s values=%s lookahead=%s action=%s" % (self.debug_rule_text(rule), "[" + ", ".join(map(str, states)) + "]", str(values), str(lookahead), str(action))
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
  allowed_directives = ( '%start', '%tokens', '%include' )

  ######################################################################
  # These are the functions invoked by the grammar actions

  # add a production (or set of productions) to the grammar
  # token is the nonterm of the production
  # produtions is a list of alternate derivations of that nonterm
  # each derivation is a 1- or 2- length list.  the first element is the list of symbols (tokens and nonterms) that the production derives, and the second, if it exists, is the action expression that is the value of the production.
  # if the augmented-start rule of the grammar is empty, and this token matches the start token -or- the start token is None, create the augmented-start rule of the grammar from this rule's token.

  def fpgAddToGrammar(self, nonterm, productions):
    if DEBUGGING_PARSER: print >> sys.stderr, "fpgAddToGrammer" + repr( (nonterm, productions) )
    for production in productions:
      syms = tuple(production[0])
      if len(production) > 1:
        action = production[1]
      else:
        action = None
      self.data['grammar'].append( (nonterm, syms, action) )
      if self.data['start'] is None:
        self.data['start'] = nonterm
    return nonterm

  def initializeParser(self):
    #
    # self.data holds the parser data that we build during the parsing
    # run, as well as during the finalizeParser() stage.
    #
    # self.data[u'grammar'] is the list of grammar rules, in the form:
    #   (nonterm, production, action)
    # nonterm is the non-terminal symbol that the rule is for.
    # production is a tuple of symbols (tokens and nonterms) that the
    #   rule produces.
    # action is the parsed, recursive expression tuple that will be
    #   evaluated for the "value" of the rule when it is reduced.
    #   If no action was given, then 'action' will be None and the
    #   default action (to copy the value of the first production
    #   symbol) will be taken.
    #   The grammar begins with a placeholder for the augmented %start
    #   rule (see the Terminology and Theory comments below)
    #
    # self.data[u'start'] holds the start symbol.  This starts out as
    #   None; if it has not been set by the %start directive when the
    #   parser finds the first grammar rule, then the start symbol will
    #   be set to the nonterm for that first grammar rule (although it
    #   can still be overridden by a later %start directive).
    #
    # self.data[u'tokens'] and self.data[u'tokens_list'] hold the token
    #   definitions; tokens is a map of token strings to values, while
    #   tokens_list is just the list of token strings.  During parsing,
    #   the tokens map is only modified when a %token or %tokens
    #   directive is processed, and the tokens list is never modified.
    #   Once parsing is complete, the grammar is scanned for any
    #   undefined tokens; they are added to the list at that point,
    #   with a warning presented to the user (since these arbitrary
    #   token values will probably not be the same as the token values
    #   assigned by the lexer).
    #
    # Similarly, self.data[u'nonterms'] and self.data[u'nonterms_list']
    #   hold the nonterm symbol definition mapping and list, respectively.
    #   These are generated just before the grammar is scanned for tokens
    #   as described above, by recording the nonterm associated with each
    #   rule.  At the same time, self.data[u'nonterm_rules'] is built,
    #   mapping each nonterm to a list of the rules which that nonterm
    #   produces.
    #

    self.data = {}
    self.data[u'grammar'] = [()]
    self.data[u'start'] = None
    self.data[u'tokens'] = {u'%eof':0}
    self.data[u'tokens_list'] = [u'%eof']
    self.data[u'nonterms'] = {}
    self.data[u'nonterms_list'] = []
    self.data[u'nonterm_rules'] = {}

  def finalizeParser(self, values):
    #
    # This is where the work of translating the grammar rules into an
    # LR(1) state machine actually happens.
    #

    #
    # WARNING:  The code to do this translation makes a lot of
    #   assumptions, the biggest being that there are NO empty
    #   productions in the grammar.  An empty production will break
    #   some things almost immediately, but will subtly break a lot
    #   of the logic as well.
    #

    #
    # First, to make things a bit more efficient, we set up local
    # references to each of the self.data[] entries (except u'start',
    # which is only used in a couple of places)
    #

    grammar = self.data[u'grammar']
    tokens = self.data[u'tokens']
    tokens_list = self.data[u'tokens_list']
    nonterms = self.data[u'nonterms']
    nonterms_list = self.data[u'nonterms_list']
    nonterm_rules = self.data[u'nonterm_rules']

    #
    # Augment the grammar with a special %start rule, which allows
    # us to recognize when we're finished parsing the input.
    #
    grammar[0] = (u'%start', (self.data['start'],), None)

    if DEBUGGING_PARSER:
      print >> sys.stderr, "initial grammar:"; import pprint; pprint.pprint(grammar, stream=sys.stderr)
      print >> sys.stderr, "initial nonterms map ="; import pprint; pprint.pprint(nonterms, stream=sys.stderr)
      print >> sys.stderr, "initial tokens map ="; import pprint; pprint.pprint(tokens, stream=sys.stderr)

    #
    # Next, we generate the nonterms mapping and list, and
    #   populate the nonterm_rules mapping.
    #
    # For each rule in the grammar, we look at the nonterm which
    #   produces that rule.  If that nonterm is not known yet,
    #   we add it to the nonterms mapping and list at the same
    #   time.
    #
    # We then either create or add to the nonterm_rules entry for
    #   that nonterm to ensure it includes the new rule number.
    #

    for rulenum in range(len(grammar)):
      nonterm = grammar[rulenum][0]
      if nonterm not in nonterms:
        nonterms[nonterm] = len(nonterms_list)
        nonterms_list.append(nonterm)
      nonterm_num = nonterms[nonterm]
      if nonterm_num in nonterm_rules:
        nonterm_rules[nonterm_num].append(rulenum)
      else:
        nonterm_rules[nonterm_num] = [rulenum]

    #
    # Determine the highest current token value; this will be used
    #   to define unrecognized tokens.  Also make sure that the
    #   tokens_list is long enough to hold (maxtoken+1) tokens.
    #

    maxtoken = max(tokens.values())
    tokens_list.extend( [None] * (maxtoken+1 - len(tokens_list)) )

    #
    # Now scan the grammar rule productions for tokens (defined as
    #   any symbol that is not a nonterm).  If they're not defined,
    #   add them to the tokens map and list with a warning to the user.
    #   Then replace all symbols in each production with the numeric
    #   value for that symbol (negative for tokens, positive for
    #   nonterms).  Finally, recreate the grammar rule with the new
    #   production and with the numeric value replacing the original
    #   nonterm.
    #

    for rulenum in range(len(grammar)):
      (nonterm, production, action) = grammar[rulenum]
      production = list(production)
      for i in range(len(production)):
        token = production[i]
        if token in tokens:
          tokens_list[tokens[token]] = token
          production[i] = -tokens[token]
        elif token in nonterms:
          production[i] = nonterms[token]
        else:
          maxtoken += 1
          print >> sys.stderr, "Warning: setting token %s to token value %d." % (token, maxtoken)
          tokens[token] = maxtoken
          tokens_list.append(token)
          production[i] = -maxtoken
      grammar[rulenum] = (nonterms[nonterm], tuple(production), action)

    if DEBUGGING_PARSER:
      print >> sys.stderr, "nonterms list ="; import pprint; pprint.pprint(nonterms_list, stream=sys.stderr)
      print >> sys.stderr, "tokens list ="; import pprint; pprint.pprint(tokens_list, stream=sys.stderr)

    #
    # To generate the closures described below, we need to know which
    #   token or tokens will start all phrases that can be represented
    #   by each symbol from the grammar (tokens and nonterms alike).
    #
    # By definition, the "first" mapping for a token is that token
    #   itself.
    #
    # The "first" mapping for a nonterm is the set of tokens that
    #   are the "first" mappings for the first symbol in each grammar
    #   rule produced by that nonterm.
    #
    # We generate the nonterm mappings iteratively in a couple
    #   of passes.
    #
    # We start by assigning an empty list to each nonterm in first{},
    #   and for each token, assigning a list consisting of that token.
    #
    # We then process each rule in the grammar and add to the first{}
    #   list for the rule's nonterm, a reference to the first{} list
    #   for the first symbol in that rule's production.
    #
    # Next, we loop through each item in each symbol's first{} list.
    #   If any item is a list, we remove it from the symbol's first{}
    #   list, then add the contents of that list back in to the
    #   symbol's first{} list.
    #
    # Finally, we convert each list to a set.  (This can be done as
    #   part of the previous pass)
    #

    first = {}

    #
    # pass 1:  create the first{} list for each symbol.  tokens get
    #   initialized with themselves; nonterms start with an empty list.
    #

    for sym in [-val for val in tokens.values()] + nonterms.values():
      first[sym] = list()
      if sym < 1:
        first[sym].append(sym)

    if DEBUGGING_PARSER:
      print >> sys.stderr, "after pass 1:  first ="; import pprint; pprint.pprint(first, stream=sys.stderr)

    #
    # pass 2:  for each rule in the grammar, add a reference to the
    #   first{} set for the first symbol in that rule's production
    #   to the first{} set for the rule's nonterm.
    #
    # Second attempt to word that, and it's still horribly awkward.
    #   Oh well.
    #

    for (nonterm, production, action) in grammar:
      if production[0] != nonterm and production[0] not in first[nonterm]:
        first[nonterm].append(first[production[0]])

    if DEBUGGING_PARSER:
      print >> sys.stderr, "after pass 2:  first ="; import pprint; pprint.pprint(first, stream=sys.stderr)

    #
    # pass 3:  Flatten each list, carefully so as not to alter any
    #   of the other lists.
    #

    for sym in first.keys():
      l = first[sym]
      i = 0
      while i < len(l):
        if isinstance(l[i],list):
          l[i:i+1] = l[i][:]
        else:
          i += 1
      first[sym] = set(l)

    if DEBUGGING_PARSER:
      print >> sys.stderr, "after pass 3:  first ="; import pprint; pprint.pprint(first, stream=sys.stderr)

    #
    # Terminology and Theory
    #
    # Now some terminology followed by some theory.  We use this
    # sample grammar for the examples:
    #       [1] B <- begin L end
    #       [2] L <- S
    #       [3] L <- S ; L
    #       [4] S <- E
    #       [5] S <- I
    #       [6] I <- if E then B
    #       [7] I <- if E then B else B
    #       [8] E <- id
    #
    # (Note that this is not considered a well-formed LR grammar,
    #   since it incorporates right-recursion in rule [3] - but
    #   it makes for nice examples of the process)
    #
    # The first thing we do is to "augment" the grammar by adding
    #   a special %start rule as rule number 0:
    #       [0] %start <- B
    #
    # This will allow us to recognize when parsing is complete.
    #   So the complete grammar for the examples is:
    #       [0] %start <- B
    #       [1] B <- begin L end
    #       [2] L <- S
    #       [3] L <- S ; L
    #       [4] S <- E
    #       [5] S <- I
    #       [6] I <- if E then B
    #       [7] I <- if E then B else B
    #       [8] E <- id
    #
    # Terminology:
    #
    # An "item" is a specific location within a rule along with the
    #   possible tokens that are expected when all the parts of the
    #   rule have been read from the input.  Items are represented
    #   in Python as: (rule,dot,lookahead):  rule is the rule number
    #   of the rule within the grammar, dot is the position within
    #   that rule, and lookahead is the list of token numbers that
    #   are valid at the time this rule is reduced.  For example,
    #   given the sample grammar above, the item (3,1,(u'end',))
    #   would represent the following rule:
    #       [3] L <- S . ; L             [[end]]
    #   That is: Rule number 3, with the dot position after the first
    #   symbol in the rule's production, with a lookahead set consisting
    #   only of the token "end".
    #
    # (In the python-format examples, we will always show unicode
    #   u'...' strings, since that's what the lexer and parser use
    #   and produce).
    #
    #
    # A "kernel" is a set of "items" where each "item" with a non-0 rule
    #   number also has a non-0 dot position.  For example:
    #       [2] L <- S .                   [[end]]
    #       [3] L <- S . ; L               [[end]]
    # This is a kernel that exists as one of the LR(1) states of the
    #   parser (as will be described below), and is represented as:
    #       (
    #         (2,1,(u'end',)),
    #         (3,1,(u'end',))
    #       )
    #
    #
    # The "closure" of a kernel is defined as the kernel itself plus,
    #   for every kernel item (rule,dot,lookahead) where dot is not
    #   at the end of the production and rule[dot] is a nonterm, a new
    #   item for each grammar rule that produces rule[dot], with a new
    #   dot position of 0 and a new lookahead of FIRST(rule[dot+1]) if
    #   there is a symbol at dot+1, or the original lookahead if not,
    #   plus a new item for each grammar rule that produces the first
    #   symbol of each of those additional items, recursively.
    #
    # Within the closure, any items that have the same rule and
    #   dot but different lookaheads are merged into a single item
    #   consisting of the rule and dot and merged lookahead lists.
    #
    # In the previous example, the described kernel is its own closure:
    #   there are no items in which the dot comes before a non-terminal.
    #   If we look at one of the possible kernels for rule 1, instead...
    #       [1] B <- begin . L end          [[%eof]]
    #   This is the kernel we would be at after reading a single "begin"
    #   token.  The closure of this kernel is generated as follows:
    #
    # First, we have a dot before the nonterm "L", so we are going to
    #   add items to the closure for each rule that is produced by "L".
    #   Because the "L" in item (1,1,(u'%eof',)) is followed by the "end" token, the new items
    #   in the closure will have a lookahead consisting only of the
    #   "end" token.  Those new items will be rules 2 and 3 with
    #   the dot at position 0 (since the dot of new items added to
    #   a closure is always 0):
    #
    #       [2] L <- . S                    [[end]]
    #       [3] L <- . S ; L                [[end]]
    #
    # Next, both of those items have the nonterm 'S' following the
    #   dot, but in one of the items, the S is at the end of the
    #   production, while in the other, it's followed by the ";" token.
    #   This means we'll add all the rules that are produced by S into
    #   the closure, but with two different lookahead sets that will
    #   be merged together:  The set [[end]] from item (2,0,(u'end',))
    #   above, and the set [[;]] from the ";" token that follows S
    #   in the item (3,0,(u'end',)).  So the new items to be added are:
    #
    #       [4] S <- . I                    [[end,;]]
    #       [5] S <- . E                    [[end,;]]
    #
    # Next up is the nonterm 'I' in rule 4.  Since it's the end of the
    #   production, we keep the same lookahead for its new items for
    #   rules 6 and 7:
    #
    #       [6] I <- . if E then B          [[end,;]]
    #       [7] I <- . if E then B else B   [[end,;]]
    #
    # Similarly for the nonterm 'E' in rule 5:
    #       [8] E <- . id               [[end,;]]
    #
    # Finally, we have rules 6, 7, and 8, where the dot is followed
    #   by a token; since that's not a nonterm, those items do not
    #   add anything new to the closure.
    #
    # So, the complete closure for the item (1,1,(u'%eof')) is:
    #       [1] S <- begin . L end          [[%eof]]
    #       [2] L <- . S                    [[end]]
    #       [3] L <- . S ; L                [[end]]
    #       [4] S <- . I                    [[end,;]]
    #       [5] S <- . E                    [[end,;]]
    #       [6] I <- . if E then B          [[end,;]]
    #       [7] I <- . if E then B else B   [[end,;]]
    #       [8] E <- . id                   [[end,;]]
    # which is represented as:
    #   (
    #     (1,1,(u'%eof',)),
    #     (2,0,(u'end',)),
    #     (3,0,(u'end',)),
    #     (4,0,(u'end',u';')),
    #     (5,0,(u'end',u';')),
    #     (6,0,(u'end',u';')),
    #     (7,0,(u'end',u';')),
    #     (8,0,(u'end',u';'))
    #   )
    #
    #
    # Theory time:
    #
    #
    # The LR parsing method is built around the concept of always
    #   knowing what (in the grammar) to expect next after having read
    #   some set of tokens.  In more general terms: given a valid
    #   "prefix" of a complete phrase of the language being parsed,
    #   the LR parsing method always knows exactly what is legal for
    #   the next token.  It implements this concept through a special
    #   kind of state machine, where each "state" represents all the
    #   places in the grammar that are reachable via some valid prefix
    #   of symbols (tokens and nonterms).
    #
    # For example, using our example grammar, after reading the tokens
    #   "begin" and "id" from the input, there is one particular
    #   set of grammar rules and locations within those rules -- in
    #   other words, one particular set of items, or one kernel --
    #   that is legal according to the grammar, and that's at the end
    #   of rule [8] E <- id.
    #
    # However, that rule says that the "id" at the end of the input
    #   can be replaced by the nonterm "E" (this is called reducing E
    #   <- id).  This presents a new set of grammar rules and locations
    #   for the input "begin" and "E" - the end of rule [5] S <- E.
    #
    # That rule says that E can now be reduced to S, which gives us
    #   yet another set of grammar rules and locations for the input
    #   "begin" and "S": either the end of rule 2, or rule 3 after
    #   the first symbol - which is the set of items shown in the
    #   "kernel" example above.
    #
    # Once we have the kernel of a state and we've determined the
    #   closure of that kernel, we can then figure out the state's
    #   transitions to other states.  An LR parser is one of a class
    #   of parsers called shift/reduce parsers, because there are two
    #   types of transitions between states - shifts and reductions.
    #
    # When an LR parser "shifts" to a new state, it is recognizing
    #   a new prefix by adding a new symbol to the end of its current
    #   prefix.  For example, if the current prefix is "if E" and the new
    #   symbol is "then", then the new prefix is now "if E then".
    #
    # When the parser "reduces" a rule to find a new state, it is
    #   *transforming* its prefix to a new prefix by replacing the
    #   rightmost symbols of its prefix that correspond with the rule
    #   being reduced by the rule's nonterm.  For example, with a
    #   prefix of "begin if E then B" and a lookahead symbol that
    #   does not allow a shift transition, the parser can instead
    #   transform that prefix to "begin S" - reducing rule 6 (if E
    #   then B) to its nonterm of S.
    #
    # The LR parser makes all decisions about shifting and reducing
    #   based both on its current prefix (its state) and on the *next*
    #   token waiting to be read.  (Technically, this token has
    #   already been read and is sitting in a lookahead buffer, but
    #   for the purposes of the theory, it's just about to be read).
    #
    # The parser will shift to a new state whenever the next token
    #   matches the token after the dot of any of the items in its
    #   kernel's closure.  In the first example given above...
    #       [2] L <- S .                   [[end]]
    #       [3] L <- S . ; L               [[end]]
    #   the parser will go to a new state when a semicolon is next
    #   to be read; that new state will be built out of the closure of:
    #       [3] L <- S ; . L               [[end]]
    #   That is: the new state will have as its kernel all the items
    #   from the closure of the original state where a semicolon is
    #   after the dot, with the dot moved after the semicolon in the
    #   new kernel.
    #
    # The parser will reduce a rule whenever the next token is in
    #   the lookahead set of any item in the state's kernel where the
    #   dot is at the end.  (Because we make the assumption that no
    #   rule will ever have an empty production, we can be sure that
    #   ever closure item that is not in the state's kernel will have
    #   at least one symbol after the dot).  Again, in the above
    #   example, the parser will reduce rule [2] L <- S whenever the
    #   next token to be red is u'end'.
    #
    # Now, there's no way to _directly_ know what the new state will be
    #   after doing that rule reduction, because that new state is based off of
    #   a different prefix:  In the example described in the text above,
    #   when the parser reduces from "begin if E then B" to "begin S",
    #   that's a brand new prefix.  That's where the "special" state
    #   machine comes in.
    #
    # An LR parser uses what's called a "push-down"
    #   automaton, which means that every state transition is accomplished
    #   by either pushing a new state onto a stack, or popping a bunch of
    #   states off the stack.  When the parser does a "shift" transition,
    #   it pushes the new state onto the stack.  The depth of the stack is
    #   always equal to the length of the language prefix that the parser
    #   has recognized so far.  In that example before, when the prefix is
    #   "begin if E then B", that means there are 5 states on the stack.
    #
    # When a rule is reduced, on the other hand, one state is popped
    #   off the stack for each symbol in the rule's production,
    #   and _then_ the parser does a shift based on the nonterm for
    #   that rule.  Again, in the if/then example, the parser starts
    #   by popping 4 states off the stack, one for each symbol in
    #   "if E then B".  The parser is then at the state where it
    #   had just read "begin", but now it knows that the "begin" was
    #   followed by the nonterm "S", and so it can shift from of the
    #   "begin" state to the new state for "begin S".
    #

    #
    # Okay, back to implementation time.
    #
    # First, here are some convenience functions to make things a bit
    # easier later.
    #
    # sym_string(sym, showStart=False):
    #   sym_string takes a symbol value (sym) and returns the token
    #   or nonterm string that value represents: if negative,
    #   it returns a token whose value is -sym; if positive, it
    #   returns the nonterm whose value is sym.  And yes, there is
    #   an ambiguous value there:  is 0 the nonterm value 0 (which is
    #   always %start) or the token value 0 (which is always %eof) ?
    #   The answer depends on the showStart flag:  If True, sym_string
    #   will return %start for a 0 value; if False (the default),
    #   sym_string will return %eof instead.
    #
    # action_string(action):
    #   action_string does something similar for actions -- it returns
    #   a shift, reduce, or accept action string based on the action
    #   value:  If negative, the action is a reduce action for rule#
    #   (-action).  If positive, the action is a shift action to
    #   state# action.  If 0, the action is accept.  Once again,
    #   there's abiguity here - except now it's that the "accept"
    #   action overrides a shift to state 0 or a reduction of state 0.
    #   In fact, there is no ambiguity there:  There can never be
    #   a shift to state 0 by definition, because state 0 is the
    #   special %start state, and %start can never appear as a token
    #   in a rule.  As for reducing rule 0, that is in fact what
    #   triggers the parser to go its accept state, so "reduce [0]"
    #   is exactly the same as "accept".
    #
    # Finally, rule_text(rulenum,dot=None,lookahead=None):
    #   rule_text takes a rule number, an optional dot position, and an
    #   optional lookahead set, and returns the textual representation
    #   of that rule, which you've already seen examples of above
    #   (albeit in a slightly nicer format).
    #       [3] L <- S . ; L  [[end]]
    #   The rule number in [brackets] followed by the rule's nonterm,
    #   the "<-" derives arrow, followed by each of the rule's
    #   production symbols.  If the dot position was given and is not
    #   None, then a "." will be placed before the appropriate symbol,
    #   or after the last symbol.  if lookahead was given and is not
    #   None, it will be added to the end of the rule text surrounded
    #   by [[double-brackets]].
    #

    def sym_string(sym, showStart=False):
      if sym > 0 or (sym == 0 and showStart):
        return nonterms_list[sym]
      return tokens_list[-sym]

    def action_string(action):
      if action < 0:
        return "reduce [%d]" % (-action,)
      if action > 0:
        return "shift %d" % (action,)
      return "accept"

    def rule_text(rulenum,dot=None,lookahead=None):
      (produces, production, action) = self.data[u'grammar'][rulenum]
      if lookahead is None:
        lookahead = ""
      else:
        lookahead = "  [%s]" % (repr([sym_string(sym) for sym in lookahead]),)
      produces = sym_string(produces, showStart=True)
      derives = (((dot == 0) and "<- .") or "<-")
      production = [
        (i,production[i])
          for i in range(len(production))
      ]
      production = [
        sym_string(sym, showStart=True) + ((((i+1) == dot) and " .") or "")
          for (i,sym) in production
      ]
      production = " ".join(production)
      dotstr = (((dot is not None) and ".%d" % (dot,)) or "")
      if action is None:
        action = ""
      else:
        action = "  -> %s" % (repr(action),)
      return "[%d]%s %s %s %s%s%s" % (
        rulenum,
        dotstr,
        produces,
        derives,
        production,
        lookahead,
        action
      )

    #
    # Now for the work-horses of the parser generation.
    #
    # First, the closure function.
    #
    # closure(k):
    #   As described above, this function generates a closure for
    #   kernel 'k' by recursively adding new items to the closure
    #   for every item (not already in the closure) in which the
    #   dot precedes a nonterm.  It propagates the lookahead sets
    #   for those items where the nonterm was at the end of item,
    #   and generates new lookahead sets for those items where the
    #   nonterm had another symbol following it.
    #
    # This is actually an iterative implementation, not recursive,
    #   but the idea is the same.
    #

    def closure(k):

      # closure_items is the closure we'll be returning.  Initialize it
      # as a list with the items from the kernel.

      closure_items = list(k)

      # it's possible for this procedure to change something it's
      # already processed, if it runs across a closure item that
      # duplicates a previous item with only a different lookahead.
      # when that happens, we need a way to loop through all the
      # rules again.  "something_has_changed" will keep track of
      # whether or not we've changed something that needs another pass.

      something_has_changed = True

      # closure_rules will keep track of (rule,dot) pairs that
      # are in the closure, without worrying about the lookaheads.
      # it's used to be able to retroactively add additional symbols
      # to the lookaheads when the same (rule,dot) pair is found with
      # a new lookahead.

      closure_rules = {}

      # keep looping through the set of closure items until nothing
      # changes.

      while something_has_changed:

        # reset something_has_changed to False so we'll not loop
        # again unless something changes something_has_changed. :)

        something_has_changed = False

        # loop through all the closure items to generate new items.
        i = 0
        while i < len(closure_items):
          (rule, dot, lookahead) = closure_items[i]

          # update our loop counter now, so we don't have it dangling
          # at the end of the loop.

          i += 1

          # cache a copy of the grammar production for this rule.

          production = self.data[u'grammar'][rule][1]

          # check if the dot in the production is before a nonterm

          if dot < len(production) and production[dot] > 0:

            # check if there are additional symbols beyond the first
            # following the dot.  if so, generate a new lookahead based
            # on the following symbol.

            if (dot+1) < len(production):
              lookahead = tuple(first[production[dot+1]])

            # add each rule that produces the nonterm at the dot into
            # the closure.

            for addrule in self.data[u'nonterm_rules'][production[dot]]:

              # check if we've already seen this new rule (with dot 0,
              # because all new items added to the closure have dot 0).

              if (addrule,0) not in closure_rules:

                # it's a new item; add it to the closure_rules mapping
                # and to the closure_items list.

                closure_rules[(addrule,0)] = len(closure_items)
                closure_items.append( (addrule, 0, lookahead) )

              else:

                # we've already seen this item, possibly with
                # different lookaheads.  append any of our symbols to
                # the lookahead for that item that are not already
                # there, then mark that something_has_changed.
                # since we can't directly modify the previous item,
                # we make a copy of the previous lookahead set,
                # modify that copy, then rebuild the previous item
                # to include the new lookaheads.

                prev_item = closure_rules[(addrule,0)]
                prev_lookahead = list(closure_items[prev_item][2])
                for sym in lookahead:
                  if sym not in prev_lookahead:
                    prev_lookahead.append(sym)
                    something_has_changed = True
                closure_items[prev_item] = (addrule, 0, tuple(prev_lookahead))

      return tuple(closure_items)

    #
    # Now we're going to actually build the parser states.  We start by
    # setting up a list to hold the states, and a mapping from kernel
    # to state number.  We also set up a list of kernels we've added
    # to the states list but not yet processed.  This allows us to
    # avoid recursion and process the grammar from top to bottom, which
    # helps with debugging the grammar later.
    #

    states = []
    state_map = {}
    kernels_to_process = []

    # allocare_lr_state(kernel):
    #   This helper function adds the kernel to the states list and
    #   returns the kernel again.  if the kernel was already in the
    #   states list, it raises a ValueException.

    def allocate_lr_state(kernel):
      kernel = tuple(sorted(kernel))
      if kernel in state_map:
        raise ValueError("Duplicate kernel: " + repr(kernel))
      state = len(states)
      state_map[kernel] = state
      states.append({u'kernel':kernel})
      return kernel

    #
    # Now we build the states.  We start with an initial kernel, passed
    #   in to the generate function, which becomes our first state.
    #   Each state is then processed iteratively by creating the
    #   closure of the kernel and generating the state transitions
    #   as described in the theory section above.  Each transition
    #   results in a new kernel which, if not already in the states
    #   map, gets a new state allocated and is added to the list of
    #   kernels to be processed.
    #

    def generate_lr_state(kernel):

      #
      # start our kernels_to_process list with the newly-allocated
      #   state for the initial kernel.
      #

      kernels_to_process = [allocate_lr_state(kernel)]

      #
      # keep processing as long as there are kernels to be processed.
      #

      while len(kernels_to_process) > 0:

        #
        # pop the kernel out of the processing queue, find the state
        # that was allocated for that kernel, then compute the closure
        # for the kernel.
        #

        kernel = kernels_to_process.pop(0)
        state = state_map[kernel]
        closure_items = closure(kernel)

        if DEBUGGING_PARSER:
          print >> sys.stderr, "\n\nState %d:\n    %s" % (state, "\n    ".join([rule_text(*item) for item in closure_items]))

        #
        # Now we need to determine the actions for this state and
        # keep track of any shift/reduce or reduce/reduce conflicts
        # that are generated.
        #

        actions = {}
        conflicts = {}

        #
        # First, we determine the shift actions by finding all the
        # kernels that can be reached by shifting a single token or
        # nonterm from this state.
        #

        for (rule,dot,lookahead) in closure_items:
          grammar_rule = self.data[u'grammar'][rule]
          if dot < len(grammar_rule[1]):
            sym = grammar_rule[1][dot]
            if sym in actions:
              actions[sym].append( (rule,dot+1,lookahead) )
            else:
              actions[sym] = [ (rule,dot+1,lookahead) ]

        #
        # Transform all the shift kernels found into actual shift
        # actions by allocating states for each.
        #
        # For vanity reasons, we do this for nonterms before tokens,
        # and do both in numeric order.  We have to be clever and skip
        # the first (sorted) token value, because we have a 0 in both
        # tokens and nonterms.
        #

        for sym in sorted(nonterms.values()) + [-val for val in tokens.values() if val > 0]:
          if sym in actions:
            k = tuple(sorted(actions[sym]))

            # try to allocate a new state for the kernel; if it fails,
            # ignore the exception (since it just means the kernel
            # is already in the state map).

            try:
              kernels_to_process.append( allocate_lr_state(k) )
            except ValueError,e:
              pass

            # Now re-assign the action to the state number for
            # the kernel

            actions[sym] = state_map[k]

            if DEBUGGING_PARSER:
              print >> sys.stderr, "%s => %s" % (
                sym_string(sym), action_string(actions[sym])
              )

        #
        # Next, we find the reduce actions by looking at each kernel
        # item whose dot is at the end of the production.  At this
        # point, we need to start recording conflicts.
        #

        for (rule,dot,lookahead) in closure_items:
          grammar_rule = self.data[u'grammar'][rule]
          if dot == len(grammar_rule[1]):

            # we're at the end of the production, so check each
            # lookahead symbol for reductions.  We need to convert
            # the positive lookahead token values to negative symbol
            # values to match those found in the production rules.

            for sym in lookahead:
              if sym in actions:

                # we have a conflict.  If we haven't recorded anything
                # yet, record the conflict with the already-determined
                # action.  if we have already recorded a conflict
                # for this sym in this state, then add a new conflict
                # between the previously-conflicting action and the
                # new action.

                if sym not in conflicts:
                  conflicts[sym] = [ (actions[sym],sym) ]
                else:
                  conflicts[sym].append( (conflicts[sym][-1][1],sym) )

                #
                # Print the conflict warning.  For shifts, just print
                # "shift", but for reductions use the action_string
                # to get the rule number for the reduce.
                #

                print >> sys.stderr, "Warning: %s/%s conflict on %s." % (
                  ((conflicts[sym][-1][0] >= 0) and "shift") or action_string(conflicts[sym][-1][0]),
                  action_string(conflicts[sym][-1][1]),
                  sym_string(sym)
                )

              else:
                # no conflict; record the reduce action.
                actions[sym] = -rule

                if DEBUGGING_PARSER:
                  print >> sys.stderr, "%s => %s" % (
                    sym_string(sym), action_string(actions[sym])
                  )

        #
        # record the actions and conflicts for the state.
        #

        states[state][u'actions'] = actions
        states[state][u'conflicts'] = conflicts

    #
    # Now we're ready to build the parser.
    #
    # First, using the generate_lr_state function, build the state
    # machine from the initial kernel of (0,0,(u'%eof',)).
    #

    generate_lr_state( ((0,0,(tokens[u'%eof'],)),) )

    #
    # Next, we generate the complete action map.  Rather than recording
    # each state as a row in a table, we just map (state,symbol) -> action
    # to save space.
    #

    actions = {}
    self.data[u'actions'] = actions

    for state_num in xrange(0,len(states)):
      for (sym,action) in states[state_num][u'actions'].items():
        actions[state_num,sym] = action

    #
    # And return all the data we've accumulated or generated so the main
    # fpg program can output the tables appropriately.
    #

    return self.data



if __name__ == '__main__':
  from fpgLexer import fpgLexer
  l = fpgLexerDriver()
  p = fpgParserDriver()
  result = p.parse(l)

  import pprint
  pprint.pprint(result)

 
