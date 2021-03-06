#!/bin/false -- # do not execute!
#
# foxLanguages.py - used to separate the language-specific output from
# the rest of the lexer/parser generation.
#
# This module imports all of the foxLanguages* modules, and defines
# a single "foxLanguages" dictionary that maps language names to the
# classes that implement that language.
#
# processed via the Makefile to include all foxLanguages*.py files.
#

#
# Each language class must define the following attributes:
#
#   language -> the language name
#
#   comment -> either a single string for comment-line-start, or a
#       tuple of ( comment-block-start, comment-block-end )
#
#   extension -> the source file extension for the language
#
#   templates -> a mapping of template name to actual template.
#       This must include templates for each program supported;
#       at a minimum, templates[u'flg'] must be defined for the flg
#       lexer class template, and templates[u'fpg'] must be defined
#       for the fpg parser class template.
#
#       The templates are the file content that will be produced
#       to generate the file appropriate for the given program name;
#       for example, the u'flg' template will produce the lexer class
#       for the flg program.  Each template can have template directives
#       surrounded by %'s; for example, %flg_tables%, %!pythonpath% or %?debug%.
#       %% will be replaced by a single %.
#       See foxLanguagesBase.writeFile() for more details.
#
#       The well-defined variables for templates are:
#           pythonexec -> the path to the python executable.
#           name -> The name of the lexer (generally, this is the
#               name of the class to generate).
#           debug -> If set to any true value, the lexer will include
#               some minimal debugging hooks that a subclass can
#               define.
#           VERSION -> The version number of flg, in tuple format: for
#               example, flg version 3.0.0a would have an FLGVERSION
#               value of (3,0,0,'a')
#           VERSION_STR -> The version number of flg, in string format.
#           flg_tables -> the lexer tables produced by flg.  See the
#               flg documentation for details.
#           fpg_tables -> the parser tables produced by fpg.  See the
#               fpg documentation for details.
#
# Plus one method:
#
#   convert(name, value) -> a python function to convert `value'
#       to a source string appropriate for the language.  The name
#       is provided so that values can be transformed in a
#       context-sensitive manner.
#

#-_-#from foxLanguages* import *
from foxLanguagesPython import *

# generate the foxLanguages mapping of language name to language class

import sys
foxLanguages = dict(tuple([(langClass.language, langClass) for langClass in [eval(langClassName) for langClassName in dir(sys.modules[__name__]) if langClassName.startswith('foxLanguages')] if issubclass(langClass, foxLanguagesBase) and langClass.language is not None]))

if __name__ == '__main__':
  import pprint
  pprint.pprint(foxLanguages)
