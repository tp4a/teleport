# -*- coding: utf-8 -*-

from .base import SwxAuthHandler


class IndexHandler(SwxAuthHandler):
    def get(self):
        self.render('pwd/index.mako')
