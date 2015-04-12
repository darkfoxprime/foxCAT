(:  these are the common grammar productions for "expressions"
    between fpg and flg.  flg only wants a couple types of these -
    an expression list, or a single token, but fpg will need the
    entire gamut in order to allow flexible action definitions.       :)

(:  expression types are lists, strings, and numbers.  lists may
    contain other expression or meta types.

    meta-types are tuples, and are processed to become expression
    types.

    meta-types consist of:

      (u'$', number) -> a positional parameter

      (u'(', token, [list]) -> a function call, with [list] as its
      arguments.

      (oper, value, value) -> an operator (+,-,*,/,%,=) with two values.
      Values may be meta-types.

    so:
      exprValue($1) -> (u'(',u'exprValue',[(u'$',1)])
      exprFuncCall($1,$3) -> (u'(',u'exprFuncCall',[(u'$',1),(u'$',3)])
      $1 + ($3) -> ('+',(u'$',1),[(u'$',3)])                          :)

expression                  <-  exp_plusminus
                            ->  $1
                            |   C_TOKEN C_EQUALS exp_plusminus
                            ->  exprOper($2, $1, $3)
                            ;

exp_plusminus               <-  exp_timesdivide
                            ->  $1
                            |   exp_plusminus C_PLUS exp_timesdivide
                            ->  exprOper($2,$1,$3)
                            |   exp_plusminus C_MINUS exp_timesdivide
                            ->  exprOper($2,$1,$3)
                            ;

exp_timesdivide             <-  exp_term
                            ->  $1
                            |   exp_timesdivide C_TIMES exp_term
                            ->  exprOper($2,$1,$3)
                            |   exp_timesdivide C_DIVIDE exp_term
                            ->  exprOper($2,$1,$3)
                            |   exp_timesdivide C_MODULO exp_term
                            ->  exprOper($2,$1,$3)
                            ;

exp_term                    <-  C_TOKEN
                            ->  exprToken($1)
                            |   C_QUOTEDSTR
                            ->  exprString($1)
                            |   C_NUMBER
                            ->  exprNumber($1)
                            |   C_POS_PARAM
                            ->  exprPosParam($1)
                            |   C_PAREN_OPEN C_PAREN_CLOSE
                            ->  ()
                            |   C_PAREN_OPEN expression_list_with_comma C_PAREN_CLOSE
                            ->  $2
                            |   C_TOKEN C_PAREN_OPEN C_PAREN_CLOSE
                            ->  exprFuncCall(exprToken($1), ())
                            |   C_TOKEN C_PAREN_OPEN expression_list_with_comma C_PAREN_CLOSE
                            ->  exprFuncCall(exprToken($1), $3)
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

