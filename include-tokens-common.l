(:  these token and table definitions are common between flg and fpg.  :)

(:  make sure we're in normal mode before we start  :)

%mode normal

C_TOKEN /[A-Za-z_][A-Za-z0-9_]*/
C_DIRECTIVE /%[a-z]+/
C_EQUALS /=/
C_NUMBER /[-+]?[0-9]+/
C_POS_PARAM /\$[0-9]+/
C_QUOTEDSTR /(("(\\.|[^\\"])*")|('(\\.|[^\\'])*'))+/
C_PAREN_OPEN /\(/
C_PAREN_CLOSE /\)/
C_COMMA /,/
C_DERIVES /<-/
C_ACTION /->/ -> push(expression)

%skip /\(:/ -> push(comment)
%skip /[ \n\t]/

(:  comment mode is special - any time we see the (: comment marker
    [outside of a regular expression] - even inside a comment - we
    `push` into comment mode.  When we find the :) end-comment marker,
    we `pop` back out to the previous mode.  this allows for nesting
    of comments.  :)

%mode comment

%skip /\(:/ -> push(comment)
%skip /:\)/ -> pop(comment)
%skip /.|\n/

(:  expression mode is only entered into after the C_ACTION token is
    recognized, and returns to normal mode at the first newline.
    but this allows for expressions in actions to use the full set of
    operators, whereas the regexp `/` marker prevents the recognition
    of the operators in normal mode.  :)

%mode expression

C_TOKEN /[A-Za-z_][A-Za-z0-9_]*/
C_EQUALS /=/
C_PLUS /\+/
C_MINUS /-/
C_TIMES /\*/
C_DIVIDE /\//
C_MODULO /\%/
C_NUMBER /[-+]?[0-9]+/
C_POS_PARAM /\$[0-9]+/
C_QUOTEDSTR /(("(\\.|[^\\"])*")|('(\\.|[^\\'])*'))+/
C_PAREN_OPEN /\(/
C_PAREN_CLOSE /\)/
C_COMMA /,/

%skip /[ \t]/
%skip /\n/ -> pop(expression)

%mode normal
