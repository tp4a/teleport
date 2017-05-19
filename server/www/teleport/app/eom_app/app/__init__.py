# -*- coding: utf-8 -*-

from .core import WebServerCore
from eom_common.eomcore.logger import *

__all__ = ['run']


def run(options):
    _app = WebServerCore()

    if not _app.init(options):
        return 1

    log.i('\n')
    log.i('###############################################################\n')
    log.i('Teleport Web Server starting ...\n')

    return _app.run()
