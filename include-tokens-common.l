(:  these token and table definitions are common between flg and fpg.  :)

C_TOKEN /[A-Za-z_][A-Za-z0-9_]*/
C_DIRECTIVE /%[a-z]+/
C_EQUALS /=/ -> push(expression)
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

%mode comment

%skip /:\)/ -> pop(comment)
%skip /.|\n/

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
