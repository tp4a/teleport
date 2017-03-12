# -*- coding: utf-8 -*-

from .base import TPBaseHandler


class IndexHandler(TPBaseHandler):
    def get(self):
        self.render('maintenance/index.mako')

