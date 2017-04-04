# -*- coding: utf-8 -*-

from .base import TPBaseUserAuthHandler


class IndexHandler(TPBaseUserAuthHandler):
    def get(self):
        self.render('pwd/index.mako')
