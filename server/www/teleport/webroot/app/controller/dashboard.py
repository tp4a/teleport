# -*- coding: utf-8 -*-

# import tornado.ioloop
from app.base.controller import TPBaseHandler


class IndexHandler(TPBaseHandler):
    def get(self):
        self.render('dashboard/index.mako')
