# -*- coding: utf-8 -*-

import os
import sys
from eom_env import *
import eom_app.app as app


def main():
    options = {
        # app_path 网站程序根路径（应该是本文件所在目录的上一级目录）
        'app_path': PATH_APP_ROOT,

        # cfg_path 网站配置文件路径
        # 'cfg_path': PATH_CONF,

        # log_path 网站运行时日志文件路径
        # 'log_path': PATH_LOG,

        # static_path 网站静态文件路径
        'static_path': os.path.join(PATH_APP_ROOT, 'static'),

        # data_path 网站数据文件路径
        'data_path': PATH_DATA,

        # template_path 网站模板文件路径
        'template_path': os.path.join(PATH_APP_ROOT, 'view'),

        # res_path 网站资源文件路径
        'res_path': os.path.join(PATH_APP_ROOT, 'res')
    }

    return app.run(options)


if __name__ == '__main__':
    sys.exit(main())
