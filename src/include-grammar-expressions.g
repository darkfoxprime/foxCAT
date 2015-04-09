(:  these are the common grammar productions for "expressions"
    between fpg and flg.  flg only wants a couple types of these -
    an expression list, or a single token, but fpg will need the
    entire gamut in order to allow flexible action definitions.  :)

expression                  <-  exp_plusminus
                            ->  $1
                            |   C_TOKEN C_EQUALS exp_plusminus
                            ->  ($2, $1, $3)
                            ;

exp_plusminus               <-  exp_timesdivide
                            ->  $1
                            |   exp_plusminus C_PLUS exp_timesdivide
                            ->  ($2) + $1 + ($3)
                            |   exp_plusminus C_MINUS exp_timesdivide
                            ->  ($2) + $1 + ($3)
                            ;

exp_timesdivide             <-  exp_term
                            ->  $1
                            |   exp_timesdivide C_TIMES exp_term
                            ->  ($2) + $1 + ($3)
                            |   exp_timesdivide C_DIVIDE exp_term
                            ->  ($2) + $1 + ($3)
                            |   exp_timesdivide C_MODULO exp_term
                            ->  ($2) + $1 + ($3)
                            ;

exp_term                    <-  C_TOKEN
                            ->  convertValue($1)
                            |   C_QUOTEDSTR
                            ->  convertValue($1)
                            |   C_NUMBER
                            ->  convertValue($1)
                            |   C_POS_PARAM
                            ->  convertValue($1)
                            |   C_PAREN_OPEN expression_list_with_comma C_PAREN_CLOSE
                            ->  $2
                            |   C_TOKEN C_PAREN_OPEN C_PAREN_CLOSE
                            ->  ($2, convertValue($1))
                            |   C_TOKEN C_PAREN_OPEN expression_list_with_comma C_PAREN_CLOSE
                            ->  ($2, convertValue($1)) + $3
                            ;

expression_list_with_comma  <-  expression_list
                            ->  $1
                            |   expression_list C_COMMA
                            ->  $1
                            ;

expression_list             <-  expression
                            ->  (")", $1)
                            |   expression_list C_COMMA expression
                            ->  $1 + ($3)
                            ;

