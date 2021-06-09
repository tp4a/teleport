# -*- coding: utf-8 -*-

import os
import sys
import signal

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'webroot'))

g_web_app = None


def signal_handler(signum, frame):
    global g_web_app
    if g_web_app is None:
        return

    print('got signal: signum={}'.format(signum))
    print('stopping...')
    g_web_app.stop()


def main():
    global g_web_app

    from app.app_env import PATH_APP_ROOT, PATH_DATA
    from app.base.webapp import tp_web_app
    g_web_app = tp_web_app()
    if not g_web_app.init(PATH_APP_ROOT, PATH_DATA):
        return 1

    signal.signal(signal.SIGINT, signal_handler)  # Ctrl-C
    signal.signal(signal.SIGHUP, signal_handler)  # 发送给具有Terminal的Controlling Process，当terminal 被disconnect时候发送
    signal.signal(signal.SIGTERM, signal_handler)  # kill

    ret = g_web_app.run()
    g_web_app.finalize()
    return ret


if __name__ == '__main__':
    sys.exit(main())
