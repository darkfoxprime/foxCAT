# To Do

Not necessarily in priority order...

* [ ] fpg: simplify parse tree
  * [ ] fpg: merge lookahead sets (LR->LALR) if no resulting conflict
  * [ ] fpg: remove lookahead sets (LALR->SLR) if no resulting conflict
* [ ] flg: Improve error handling in flg
  * [X] flg: get rid of assertions, replace with lexer exceptions that can be caught
  * [ ] flg: figure out best way to deal with a tokenizing error, if the caller asks for another token again
* [ ] fpg: Add error handling to fpg
* [ ] general: Improve internal documentation (comments)
* [ ] general: Create external documentation
* [ ] general: Add libraries for common tasks such as symbol table processing, quoted string processing, etc.
