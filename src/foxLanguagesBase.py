#!/bin/false -- # do not execute!
#
# foxLanguagesBase.py - base class for foxLanguages classes.
#

class foxLanguagesBase(object):

  #
  # define the names that all foxLanguages* classes must define:
  #
  #   comment -> either a single string for comment-line-start,
  #       or a tuple of ( comment-block-start, comment-block-end )
  #
  #   convert(var, value) -> a python function to convert `value' to a
  #       source string appropriate for the language.
  #
  #   extension -> the source file extension for the language
  #
  #   language -> the language name
  #
  #   lexerOutput -> the template for the lexer output file.  see
  #       parserOutput for description.
  #
  #   parserOutput -> the template for the parser output file.  any string
  #       of the form %XYZ% will be replaced by the variable XYZ,
  #       converted for the language.  any string of the form %!XYZ% will
  #       be replaced by the variable XYZ exactly.  %% will be replaced
  #       by a single %.
  #
  comment = None
  extension = None
  language = None
  lexerOutput = None
  parserOutput = None

  # the default convert function just returns the value
  @classmethod
  def convert(var, value):
    return value

  @classmethod
  def processTemplate(self, template, vars):
    stream = StringIO.StringIO()
    self.writeFile(stream, template, vars)
    tmpl = stream.getvalue()
    stream.close()
    return tmpl

  #
  # the writeFile method accepts an output stream, a template and a set
  # of variables and processes the template against those variables,
  # outputting the result on its output stream.
  #
  # template tags are indicated by % signs:
  #   %%       = a % sign in the output
  #
  #   %<var>%   = the content of variable <var>, after being converted
  #
  #   %!<var>%  = the content of variable <var>, *not* converted.
  #
  #   %?<var>%  = the beginning of a conditional block.  After this 
  #               tag, text will only be included if <var> evaluates
  #               to true (non-empty string, a number != 0, etc.)
  #
  #   %?!<var>% = the beginning of a conditional block.  After this
  #               tag, text will only be included if <var> evaluates
  #               to false (empty string, the number 0, None, etc.)
  #
  #   %?%       = This ends the most recent conditional block.
  #
  #   %?!%      = This negates the most recent conditional block
  #               (think "else" in an if-then-else statement).
  #
  # As is implied above, conditional blocks can be nested.  Text
  # and variable expansions will be added to the output only if
  # all the conditional blocks that surround them evaluate to true.
  #               
  #

  @classmethod
  def writeFile(self, stream, template, vars):
    tlist = template.split(u'%')
    # keep track of nested conditional states.
    # start in True state.
    conditional = []
    for i in range(0,len(tlist)):
      cond = reduce(lambda a,b:a and b, conditional, True)
      if (i%2 == 0):
        # text block
        if cond: stream.write( tlist[i] )
      elif (len(tlist[i]) == 0):
        # %% block
        if cond: stream.write( u'%' )
      elif (tlist[i][0] == u'!'):
        # raw (%!...%) block
        var = tlist[i][1:]
        if cond: stream.write( str(vars[var]) )
      elif (tlist[i][0] == u'?'):
        # conditional block:
        # either %?...% or %?!...% to start a conditional,
        # %?!? to reverse the conditional, or %?% to end the conditional
        if tlist[i] == u'?':
          # %?%: end the conditional
          conditional.pop(0)
        elif tlist[i] == u'?!':
          # %?!%: reverse the conditional
          conditional[0] = not conditional[0]
        else:
          # %?...% or %?!...%: start the conditional
          var = tlist[i][1:]
          if var[0] == '!':
            cond = not bool(vars[var[1:]])
          else:
            cond = bool(vars[var])
          conditional.insert(0, cond)
      else:
        # %...% block
        var = tlist[i]
        if cond: stream.write( self.convert(var, vars[var]) )
