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
    the processing has already taken place in the directive or production
    actions, so we allow the parser to use the default action, which is
    to return $1.  :)

file                        <-  line
                            |   file line
                            ;

line                        <-  directive
                            |   production
                            ;

(:  the directive and expression parsers are common to flg and fpg, so
    we include them from a common file.  :)

%include "include-grammar-directives.g"
%include "include-grammar-expressions.g"

(:  the production rules are fairly simple.  most of the work happens in
    the fpgAddToGrammar function call in the production rule's action.  :)

production                  <-  C_TOKEN C_DERIVES productionAlternatives P_END_PRODUCTION
                            ->  fpgAddToGrammar($1,$2)
                            ;

productionAlternatives      <-  productionRule
                            ->  ($1)
                            |   productionAlternatives P_ALTERNATE productionRule
                            ->  $1 + ($3)
                            ;

productionRule              <-  productionList
                            ->  ($1)
                            |   productionList C_ACTION expression
                            ->  ($1,$3)
                            ;

productionList              <-  C_TOKEN
                            ->  ($1)
                            |   productionList C_TOKEN
                            ->  $1 + ($2)
                            ;
