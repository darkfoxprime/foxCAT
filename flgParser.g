(:  the tokens list must be the same between the lexer and parser files.
    in addition, for convenience, we are keeping the C_ (common) tokens
    the same between the flg lexer generator and fpg parser generator.
    in order to do this, we use the %include facility to include the common
    tokens list first, then we include a specific token list for the app
    (flg/fpg) in question.  These have a ".g" suffix, but are used in both
    the lexer and parser files.  :)

%include "include-tokens-common.g"
%include "include-tokens-flg.g"

%start file

(:  we don't care what the return value for file or line are, since all
    the processing has already taken place in the directive or lexer_rule
    actions, so we allow the parser to use the default action, which is
    to return $1.  :)

file                        <-  line
                            |   file line
                            ;

line                        <-  directive
                            |   lexer_rule
                            ;

(:  the directive and expression parsers are common to flg and fpg, so
    we include them from a common file.  :)

%include "include-grammar-directives.g"
%include "include-grammar-expressions.g"

(:  The regular expression rules are somewhat complex, but make use
    of the bottom-up parsing rules to form the regular expressions
    a bit at a time and join them together as they're built.

    Theory of operation time:

    Regular expressions are built up as NFAs (non-deterministic
    finite automata).  These are state machines that may include both
    "epsilon" transitions (transitions that do not consume input)
    as well as multiple transitions from the same state on the same
    possible inputs.  These NFAs are joined together through various
    mechanisms as the regular expressions are built up, and then are
    manipulated one final time when the rule as a whole is added to
    the current mode's state machine table.  This process is called
    "Thompson's Construction", after Ken Thompson who invented it for
    the QED editor in 1968.  Functions provided by the parser driver
    class (a subclass of the generated parser class) do the actual
    work of creating the NFAs, as described here.

    At the lowest level, individual characters and character classes
    (`[]`) are created via the `rxMakeAtom` and `rxMakeCharClass`
    functions.  These functions each create a two-state NFA,
    with a transition from the first to the second on one specific
    character (for `rxMakeAtom`), or on a set of character ranges
    (for `rxMakeCharClass` and for rxMakeAtom on the `.` atom, which
    is really the same as `[^\n]`).  The "value" of the `RX_ATOM`
    token or `regexp_charclass` production, then, is the tuple of
    `(s1,s2)` where `s1` is the first state of the two-state NFA and
    `s2` is the second state.  These two make up two of the three
    productions for `regexp_atom`; the third, which is for any full
    regular expression surrounded by `(` and `)`, simply returns the
    full regular expression again.

    The rest of the regexp produtions all accept one or more 2ples
    of this format `(s1,s2)` and produce new `(s1,s2)` 2ples.
    For example, `rxMakeStar`, `rxMakePlus`, and `rxMakeQuestion`
    are the functions that are used by the `regexp_multi` productions
    to transform any regular expression NFA into `(RE)*`, `(RE)+`, or
    `(RE)?`: respectively, 0 or more copies of `RE`, 1 or more copies
    of `RE`, or 0 or 1 copy of `RE`.  They do this by generating a
    new NFA (call it states `s3` and `s4`) and creating "epsilon"
    transitions between the new states and the input states:  All
    create "epsilon" transitions from the new `s3` to the input
    `s1` and from the input `s2` to the new `s4`, making `(s3,s4)`
    recognize the same input as the original `(s1,s2)`.  `*` and `?`
    both add an additional "epsilon" transition from `s3` to `s4`
    directly, allowing the NFA to "bypass" the original `s1`->`s2`
    transition.  `*` and `+` both add another "epsilon" transition from
    `s4` to `s3`, creating a "loop" from the end of the NFA back to
    the beginning.  All three then return `(s3,s4)` as the new NFA.

    The longer of the two `regexp_concat` productions joins two NFAs
    into a single NFA that recognizes the first followed by the second.
    It does with the `rxMakeSequence` function, which accepts two NFAs
    (call them `(s1,s2)` and `(s3,s4)`) and adds a new "epsilon"
    transition from `s2` of the first NFA to `s3` of the second.
    It then returns the tuple `(s1,s4)` - in other words, the new
    NFA that starts at `s1` of the first input NFA and ends at `s4`
    of the second input NFA.

    The longer of the two `regexp_alt` productions joins two NFAs
    into a single NFA that will recognize _either_ the first _or_
    the second.  It does this with the `rxMakeAlternate` function,
    which accepts two NFAs (`(s1,s2)` and `(s3,s4)`).  It creates a
    new pair of states `s5` and `s6`.  `s5` gets linked to both `s1`
    and `s3` via "epsilon" transitions", and `s2` and `s4` both get
    linked to `s6` via "epsilon" transitions.  The new NFA `(s5,s6)`
    is then returned.

    Finally, the rxAddToRecognizer function takes a token, a complete
    regular expression NFA, and an optional action, and adds it
    (via another new "epsilon" transition) to the start state of the
    overall recognizer table for the current lexer mode.

    After the entire file has been processed, the final step (via the
    `finalizeParser()` method of the parser driver) is to convert
    each modes' state machine tables from NFAs to DFAs (deterministic
    finite automata), which have the more restrictive properties of
    not allowing either "epsilon" transitions nor multiple transitions
    from the same state on the same input.  The DFA state tables are
    then output as part of the generated lexer file.  :)

lexer_rule                  <-  TOKEN regexp
                            ->  rxAddToRecognizer($1, $2)
                            |   TOKEN regexp ACTION expression
                            ->  rxAddToRecognizer($1, $2, $4)
                            |   DIRECTIVE regexp
                            ->  rxAddToRecognizer($1, $2)
                            |   DIRECTIVE regexp ACTION expression
                            ->  rxAddToRecognizer($1, $2, $4)
                            ;

regexp                      <-  RX_START regexp_alt RX_END
                            ->  $2
                            ;

regexp_alt                  <-  regexp_concat
                            ->  $1
                            |   regexp_alt RX_ALTERNATE regexp_concat
                            ->  rxMakeAlternate( $1, $3 )
                            ;

regexp_concat               <-  regexp_multi
                            ->  $1
                            |   regexp_concats regexp_multi
                            ->  rxMakeSequence( $1, $2 )
                            ;

regexp_multi                <-  regexp_atom
                            ->  $1
                            |   regexp_atom RX_STAR
                            ->  rxMakeStar($1)
                            |   regexp_atom RX_QUESTION
                            ->  rxMakeQuestion($1)
                            |   regexp_atom RX_PLUS
                            ->  rxMakePlus($1)
                            ;

regexp_atom                 <-  RX_ATOM
                            ->  rxMakeAtom($1)
                            |   regexp_charclass
                            ->  $1
                            |   RX_GRP_OPEN regexp_alt RX_GRP_END
                            ->  $2
                            ;

regexp_charclass            <-  RX_CHARCLASS regexp_cc_parts CC_END
                            ->  rxMakeCharClass($1,$2)
                            ;

regexp_cc_parts             <-  regexp_cc_part
                            ->  $1
                            |   regexp_cc_parts regexp_cc_part
                            ->  rxCCJoin($1,$2)
                            ;

regexp_cc_part              <-  CC_CHAR
                            ->  rxCCCharRange($1,$1)
                            |   CC_CHAR CC_RANGE CC_CHAR
                            ->  rxCCCharRange($1,$3)
                            ;
