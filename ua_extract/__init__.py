__version__ = '1.3.1'
from .settings import *
from .parser import *
from .device_detector import *
from .update_regex import Regexes

import ua_extract.warnings

ua_extract.warnings.enable_colored_warnings()
