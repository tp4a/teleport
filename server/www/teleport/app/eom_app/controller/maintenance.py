# -*- coding: utf-8 -*-

from .base import SwxBaseHandler


class IndexHandler(SwxBaseHandler):
    def get(self):
        self.render('maintenance/index.mako')

