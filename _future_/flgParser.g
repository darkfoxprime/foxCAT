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

(:  the regular expression rules are somewhat complex, but make use of
    the bottom-up parsing rules to form the regular expressions a bit
    at a time and join them together as they're built:

    each rxMake* function call returns the beginning and ending states
    of an NFA (non-deterministic finite automaton - i.e. one that allows
    multiple transitions on the same input symbols or allows transitions
    on no input symbols at all).

    the rxMakeAtom and rxMakeCharClass create NFAs that recognize a single
    character in the input stream, whether it's to match a specific
    character or a character class from the RE.  rxMakeCharClass uses
    the initial sequence of the character class and a list of character
    sequences returned from the rxCCCharRange function to build its
    recognizer.

    all other rxMake* functions take the return from other rxMake*
    functions and manipulate and/or join them to get the desired
    recognition pattern.

    finally, the rxAddToRecognizer function takes a token, a complete
    regular expression NFA, and an optional action, and adds it to the
    overall recognizer table for the current lexer mode.  :)

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
                            ->  rxMakeGroup($2)
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
