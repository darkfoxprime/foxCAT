(:  these are the common grammar productions for "expressions"
    between fpg and flg.  flg only wants a couple types of these -
    an expression list, or a single token, but fpg will need the
    entire gamut in order to allow flexible action definitions.  :)

expression                  <-  exp_factor
                            ->  $1
                            |   expression C_TIMES exp_factor
                            ->  ($2) + $1 + ($3)
                            |   expression C_DIVIDE exp_factor
                            ->  ($2) + $1 + ($3)
                            |   expression C_MODULO exp_factor
                            ->  ($2) + $1 + ($3)
                            ;

exp_factor                  <-  exp_term
                            ->  $1
                            |   exp_factor C_PLUS exp_term
                            ->  ($2) + $1 + ($3)
                            |   exp_factor C_MINUS exp_term
                            ->  ($2) + $1 + ($3)
                            ;

exp_term                    <-  C_TOKEN
                            ->  $1
                            |   C_TOKEN C_EQUALS expression
                            ->  ($2, $1, $3)
                            |   C_QUOTEDSTR
                            ->  $1
                            |   C_NUMBER
                            ->  $1
                            |   C_POS_PARAM
                            ->  $1
                            |   C_PAREN_OPEN expression_list_with_comma C_PAREN_CLOSE
                            ->  ($3) + $2
                            |   C_TOKEN C_PAREN_OPEN C_PAREN_CLOSE
                            ->  ($2, $1)
                            |   C_TOKEN C_PAREN_OPEN expression_list_with_comma C_PAREN_CLOSE
                            ->  ($2, $1) + $3
                            ;

expression_list_with_comma  <-  expression_list
                            ->  $1
                            |   expression_list C_COMMA
                            ->  $1
                            ;

expression_list             <-  expression
                            ->  ($1)
                            |   expression_list C_COMMA expression
                            ->  $1 + ($3)
                            ;

