# -*- coding: utf-8 -*-

import os
import sys
from eom_env import *
import eom_app.app as app
from eom_common.eomcore.logger import *

log.set_attribute(min_level=LOG_DEBUG, trace_error=TRACE_ERROR_FULL)


def main():
    options = {
        # app_path 网站程序代码路径，用于内部合成controller和model的路径，必须指定
        'app_path': PATH_APP_ROOT,

        # cfg_path 网站配置文件路径，如未指定，默认为 $_root_path$/conf
        'cfg_path': PATH_CONF,

        # log_path 网站运行时日志文件路径，如未指定，默认为 $_root_path$/log
        'log_path': PATH_LOG,

        # static_path 网站静态文件路径，如未指定，默认为 $_root_path$/static
        'static_path': os.path.join(PATH_APP_ROOT, 'static'),

        # data_path 网站数据文件路径，如未指定，默认为 $_root_path$/data
        'data_path': PATH_DATA,

        # template_path 网站模板文件路径，如未指定，默认为 $_root_path$/template
        'template_path': os.path.join(PATH_APP_ROOT, 'view'),

        # res_path 网站资源文件路径，例如字体文件等，默认为 $_root_path$/res
        'res_path': os.path.join(PATH_APP_ROOT, 'res'),

        'dev_mode': DEV_MODE,
    }

    return app.run(options)


if __name__ == '__main__':
    sys.exit(main())
