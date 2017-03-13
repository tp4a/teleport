# -*- coding: utf-8 -*-

from .base import TPBaseUserAuthHandler, TPBaseAdminAuthHandler
from eom_app.app.db import get_db


class IndexHandler(TPBaseUserAuthHandler):
    def get(self):
        self.render('maintenance/index.mako')


class InstallHandler(TPBaseAdminAuthHandler):
    def get(self):
        if get_db().need_upgrade:
            return self.redirect('/maintenance/upgrade')

        self.render('maintenance/install.mako')


class UpgradeHandler(TPBaseAdminAuthHandler):
    def get(self):
        if get_db().need_create:
            return self.redirect('/maintenance/install')

        self.render('maintenance/upgrade.mako')
