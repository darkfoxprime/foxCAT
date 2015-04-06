# foxCAT
The foxCAT set of Compiler Automation Tools - basically, my versions of yacc and lex written in python.

Current version:  1.0.0-alpha1

## tools available
* `flg` - the fox lexer generator.  This accepts a file describing a set of tokens that the lexer will recognize.  Tokens can be grouped into separate "modes", with certain tokens acting to switch modes when they are recognized.  To provide additional context control, switching modes can also be done in a "stack" behaviour, `push`ing into a mode and `pop`ing back out to the previous mode.
* `fpg` - the fox parser generator.  *[Not yet implemented - but soon!]*  This accepts a file describing a set of grammar rules that the parser will recognize as a complete file.  Each grammar rule can have a specific action associated with it, to build lists out of the input tokens and/or to call user-provided functions to process the tokens more thoroughly.

## Features
* The entire set of tools is written in _(hopefully well-documented)_ python as a fairly straightforward implementation of the algorithms presented by Aho, Sethi, and Ullman in the so-called "Dragon" book, _Compilers, principles, techniques, and tools_.
* Common file format and common directives used for both `flg` and `fpg`
