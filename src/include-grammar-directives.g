(:  in flg, directives are processed as they are found to change the
    lexer behaviour, but are not otherwise recorded.

    in fpg, it is likely that future directives will need to be
    recorded.

    to accomodate this, the directive rule calls a processDirective
    function so that the directive can be handled immediately if
    needed, or can be returned in a form that can be added to the
    parse tree.  :)

directive                   <-  C_DIRECTIVE expression
                            ->  processDirective($1,$2)
                            ;

