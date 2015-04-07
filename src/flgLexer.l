(:  the tokens list must be the same between the lexer and parser
    files.  in addition, for convenience, we are keeping the C_
    (common) tokens the same between the flg lexer generator and
    fpg parser generator.  in order to do this, we use the %include
    facility to include the common tokens list first, then we include a
    specific token list for the app (flg/fpg) in question.  These have
    a ".g" suffix, but are used in both the lexer and parser files. :)

%include "include-tokens-common.g"
%include "include-tokens-flg.g"

%start normal

%mode normal

(:  we use a common include file between flg and fpg for the lexer
    definitions of the common tokens.  :)

%include "include-tokens-common.l"

(:  make sure we're back at "normal" mode  :)

%mode normal

L_RX_START /\// -> regexp

%skip /[ \t\n]+/

%mode regexp

L_RX_END /\// -> normal

L_RX_CHARCLASS /\[^?\]?-?/ -> charclass
L_RX_ATOM /(\\(x[0-9a-fA-F][0-9a-fA-F]|[0-7][0-7][0-7]|u[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]|U[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]|[^x0-7uU]))|[^/\\\[|*?+()]/
L_RX_ALTERNATE /\|/
L_RX_STAR /\*/
L_RX_QUESTION /\?/
L_RX_PLUS /\+/
L_RX_GRP_OPEN /\(/
L_RX_GRP_CLOSE /\)/

%mode charclass

L_RX_CC_CHAR /(\\(x[0-9a-fA-F][0-9a-fA-F]|[0-7][0-7][0-7]|u[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]|U[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]|[^x0-7uU]))|[^\\\-\]]/
L_RX_CC_RANGE /-/
L_RX_CC_END /]/ -> regexp

