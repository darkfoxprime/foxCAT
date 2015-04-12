#!/usr/bin/python
#
# fpg - FOX parser generator.
#
# usage:
#   fpg [ -l,--language=<outputlanguage> ] [ -n,--name=<name> ]
#       [ -o,--outputfile=<filename> ] [ -v,--showtables ] <inputfile>|-
#
# options:
#   -l,--language=<outputlanguage>
#     What language to output the parser in.  Currently, only "python"
#     is supported.
#   -n,--name=<name>
#     The parser class name.  Also used for default output filename.
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

# CAT imports that will be merged into the final fpg file using the buildStandalone script

from version import *
from fpgDrivers import *
from foxLanguages import *

########################################################################
##
##  set up options parser
##
########################################################################

PROG = u'fpg'

optparser = optparse.OptionParser( prog = PROG, version = "%prog version " + VERSION_STR )

optparser.set_description('''The FOX Parser Generator.  Given suitable fpg source file, this generates parser code capable of recognizing and tokenizing an input stream into the tokens defined by the fpg source file.''')

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
  help = '''The language for which the parser code will be generated.  ''' + languages
)

optparser.add_option(
  '-D', '--debugging',
  dest = 'debugging',
  action = 'store_true',
  default = False,
  help = '''Enable the use of debugging hooks from the parser.'''
)

optparser.add_option(
  '-n', '--name',
  metavar = '<name>',
  dest = 'name',
  type = 'string',
  help = '''Required: The parser class name.'''
)

optparser.add_option(
  '-o', '--outputfile',
  metavar = '<filename>',
  dest = 'outputfile',
  type = 'string',
  help = '''The filename to generate.  Defaults to the parser <name> (see --name) with a language-approprate extension.  If no "." appears in <filename>, then a language-appropriate extension will be added.  If <filename> is "-" (a single dash), then the generated parser will be displayed on standard output.'''
)

optparser.add_option(
  '-v', '--showtables',
  dest = 'showtables',
  action = 'store_true',
  default = False,
  help = '''After creating the parser tables, output the generated tables in descriptive format to standard output.  [[Not currently implemented]]'''
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
##  parse the input file and generate the parser tables
##
########################################################################

lexer = fpgLexerDriver(source=infile, filename=infilename)
parser = fpgParserDriver()

parser_data = parser.parse(lexer)

parser_data['actions'][None] = 0

tables = {
  'actions' : parser_data['actions'],
  'tokens' : tuple(parser_data['tokens_list']),
  'nonterms' : tuple(parser_data['nonterms_list']),
  'rules' : parser_data['grammar'],
}

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
  'pythonexec': sys.executable,
  'VERSION': VERSION,
  'VERSION_STR': VERSION_STR,
  'name': options.name,
  'debug': options.debugging,
  'fpg_tables': tables,
}

langClass.writeFile(outputfile, langClass.templates[PROG], vars)
