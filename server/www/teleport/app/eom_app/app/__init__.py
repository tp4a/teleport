# -*- coding: utf-8 -*-

from .core import SwxCore
from eom_common.eomcore.logger import *

__all__ = ['run']


def run(options):
    log.initialize()
    # log.set_attribute(min_level=LOG_VERBOSE, log_datetime=False, trace_error=TRACE_ERROR_NONE)
    # log.set_attribute(min_level=LOG_VERBOSE, trace_error=TRACE_ERROR_NONE)
    # log.set_attribute(min_level=LOG_DEBUG, trace_error=TRACE_ERROR_FULL)

    _app = SwxCore()
    if not _app.init(options):
        return 1

    log.i('\n')
    log.i('###############################################################\n')
    log.i('Teleport Web Server starting ...\n')

    return _app.run()
