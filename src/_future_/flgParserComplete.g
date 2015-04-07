
%tokens (
  C_TOKEN,
  C_DIRECTIVE,
  C_EQUALS,
  C_NUMBER,
  C_POS_PARAM,
  C_QUOTEDSTR,
  C_PAREN_OPEN,
  C_PAREN_CLOSE,
  C_COMMA,
  C_PLUS,
  C_MINUS,
  C_TIMES,
  C_DIVIDE,
  C_MODULO,
  C_DERIVES,
  C_ACTION,
)
%tokens (
  L_RX_START,
  L_RX_END,
  L_RX_ALTERNATE,
  L_RX_PLUS,
  L_RX_QUESTION,
  L_RX_STAR,
  L_RX_ATOM,
  L_RX_CHARCLASS,
  L_RX_CC_CHAR,
  L_RX_CC_END,
  L_RX_CC_RANGE,
  L_RX_GRP_CLOSE,
  L_RX_GRP_OPEN,
)

%start file


file                        <-  line
                            |   file line
                            ;

line                        <-  directive
                            |   lexer_rule
                            ;



directive                   <-  C_DIRECTIVE expression
                            ->  processDirective($1,$2)
                            ;


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
