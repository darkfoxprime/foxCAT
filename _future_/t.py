
from foxLanguagesPython import *

# generate the foxLanguages mapping of language name to language class

import sys
foxLanguages = dict(tuple([(langClass.language, langClass) for langClass in [eval(langClassName) for langClassName in dir(sys.modules[__name__]) if langClassName.startswith('foxLanguages')] if issubclass(langClass, foxLanguagesBase) and langClass.language is not None]))

