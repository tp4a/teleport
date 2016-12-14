import json
import urllib
import gzip
import os
# from .configs import app_cfg
from eom_app.app.configs import app_cfg
from eom_app.module import host
from .base import SwxJsonHandler, SwxAuthHandler

cfg = app_cfg()


class IndexHandler(SwxAuthHandler):
    def get(self):
        self.render('pwd/index.mako')