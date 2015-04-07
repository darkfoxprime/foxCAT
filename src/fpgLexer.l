(:  the tokens list must be the same between the lexer and parser files.
    in addition, for convenience, we are keeping the C_ (common) tokens
    the same between the flg lexer generator and fpg parser generator.
    in order to do this, we use the %include facility to include the common
    tokens list first, then we include a specific token list for the app
    (flg/fpg) in question.  These have a ".g" suffix, but are used in both
    the lexer and parser files.  :)

%include "include-tokens-common.g"
%include "include-tokens-fpg.g"

%start normal

(:  we use a common include file between flg and fpg for the lexer
    definitions of the common tokens.  :)

%include "include-tokens-common.l"

%mode normal

(:  make sure we're in "normal" mode  :)

P_ALTERNATE /\|/
P_END_PRODUCTION /;/

%skip /[ \t\n]+/

