#!/usr/bin/python
#
# flg - FOX lexer generator.
#
# usage:
#   flg [ -l,--language=<outputlanguage> ] [ -n,--name=<name> ]
#       [ -o,--outputfile=<filename> ] [ -v,--showtables ] <inputfile>|-
#
# options:
#   -l,--language=<outputlanguage>
#     What language to output the lexer in.  Currently, only "python"
#     is supported.
#   -n,--name=<name>
#     The lexer class name.  Also used for default output filename.
#   -o,--outputfile=<filename>
#     The output filename.  Can be "-" for stdout.
#   -v,--showtables
#     After parsing, output the generated tables in a descriptive format
#     to stdout.
#     [[ currently does nothing! ]]
#


# python imports

import sys
import os

import optparse

# CAT imports that will be merged into the final flg file using the buildStandalone script

from version import *
from flgDrivers import *
from foxLanguages import *

########################################################################
##
##  set up options parser
##
########################################################################

PROG = u'flg'

optparser = optparse.OptionParser( prog = PROG, version = "%prog version " + VERSION_STR )

optparser.set_description('''The FOX Lexer Generator.  Given suitable flg source file, this generates lexer code capable of recognizing and tokenizing an input stream into the tokens defined by the flg source file.''')

optparser.set_usage('''%prog [<options>...] <inputfile> | -''')

optparser.disable_interspersed_args()

languages = [x + ',' for x in sorted(foxLanguages.keys())]
languages[-1] = languages[-1][:-1]
if len(languages) == 2:
  languages[0] = languages[0][:-1]
if len(languages) > 1:
  languages[-1] = 'and ' + languages[-1]
if len(languages) == 1:
  languages = 'The choice currently available is: ' + languages[0]
else:
  languages = 'Possible choices are: ' + ' '.join(languages)

optparser.add_option(
  '-l', '--language',
  metavar = '<outputlanguage>',
  dest = 'language',
  type = 'choice',
  choices = foxLanguages.keys(),
  default = 'python',
  help = '''The language for which the lexer code will be generated.  ''' + languages
)

optparser.add_option(
  '-D', '--debugging',
  dest = 'debugging',
  action = 'store_true',
  default = False,
  help = '''Enable the use of debugging hooks from the lexer.'''
)

optparser.add_option(
  '-n', '--name',
  metavar = '<name>',
  dest = 'name',
  type = 'string',
  help = '''Required: The lexer class name.'''
)

optparser.add_option(
  '-o', '--outputfile',
  metavar = '<filename>',
  dest = 'outputfile',
  type = 'string',
  help = '''The filename to generate.  Defaults to the lexer <name> (see --name) with a language-approprate extension.  If no "." appears in <filename>, then a language-appropriate extension will be added.  If <filename> is "-" (a single dash), then the generated lexer will be displayed on standard output.'''
)

optparser.add_option(
  '-v', '--showtables',
  dest = 'showtables',
  action = 'store_true',
  default = False,
  help = '''After creating the lexer tables, output the generated tables in descriptive format to standard output.  [[Not currently implemented]]'''
)

# don't display the --version and --help options in the usage
opt = optparser.get_option('--help')
if opt is not None:
  opt.help = optparse.SUPPRESS_HELP
opt = optparser.get_option('--version')
if opt is not None:
  opt.help = optparse.SUPPRESS_HELP

########################################################################
##
##  parse and process the options and command line
##
########################################################################

(options, args) = optparser.parse_args(sys.argv[1:])

if len(args) == 0:
  optparser.print_help()
  sys.exit(0)

if len(args) > 1:
  optparser.print_usage(sys.stderr)
  sys.exit(22)

if options.showtables:
  optparser.error('--showtables option is not yet implemented.')

if options.name is None:
  optparser.error('''option --name must be specified''')

langClass = foxLanguages[options.language]

infilename = args[0]
if infilename == '-':
  infile = sys.stdin
else:
  try:
    infile = open(infilename, 'r')
  except IOError,e:
    optparser.error('Unable to open %s for reading: %s' % (infilename, e.strerror))

########################################################################
##
##  parse the input file and generate the lexer tables
##
########################################################################

lexer = flgLexerDriver(source=infile, filename=infilename)
parser = flgParserDriver()

lexer_tables = parser.parse(lexer)

########################################################################
##
##  generate the output file
##
########################################################################

if options.outputfile == '-':
  outputfile = sys.stdout
else:
  if options.outputfile is None:
    options.outputfile = options.name
  if options.outputfile != '-' and '.' not in options.outputfile.rsplit('/',1)[-1]:
    options.outputfile += langClass.extension
  try:
    outputfile = open(options.outputfile, 'w')
  except IOError,e:
    optparser.error('Unable to open %s for writing: %s' % (options.outputfile, e.strerror))

vars = {
  'VERSION': VERSION,
  'VERSION_STR': VERSION_STR,
  'name': options.name,
  'debug': options.debugging,
  'flg_tables': lexer_tables,
  'pythonexec': sys.executable,
}

langClass.writeFile(outputfile, langClass.templates[PROG], vars)
