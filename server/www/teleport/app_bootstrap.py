# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'webroot'))


def main():
    from app.app_env import PATH_APP_ROOT, PATH_DATA
    from app.base.webapp import tp_web_app
    _web_app = tp_web_app()
    if not _web_app.init(PATH_APP_ROOT, PATH_DATA):
        return 1

    return _web_app.run()


if __name__ == '__main__':
    sys.exit(main())
