# -*- coding: utf-8 -*-

import os
import json
from app.base.configs import tp_cfg
from app.base.logger import log


class ExtSrvCfg(object):

    def __init__(self):
        super().__init__()

        import builtins
        if '__ext_srv_cfg__' in builtins.__dict__:
            raise RuntimeError('ExtSrvCfg object exists, you can not create more than one instance.')

        # session表，session_id为索引，每个项为一个字典，包括 v(value), t(last access), e(expire seconds)
        self._cfg = dict()

    def init(self):
        cfg = tp_cfg()
        cfg_file = os.path.join(cfg.cfg_path, 'extsrv.json')
        # 如果配置文件不存在，则不支持第三方服务调用TP-API
        if not os.path.exists(cfg_file):
            return True

        log.i('Loading external server configuration...\n')
        with open(cfg_file, encoding='utf_8') as f:
            c = f.read()
            try:
                sc = json.loads(c)
            except:
                return False

        if 'version' not in sc:
            return False
        if 'ext_srv' not in sc:
            return False

        srv = sc['ext_srv']

        try:
            for i in range(len(srv)):
                srv_name = srv[i]['name']
                srv_desc = srv[i]['desc']
                for j in range(len(srv[i]['access'])):
                    key = srv[i]['access'][j]['key']
                    secret = srv[i]['access'][j]['secret']
                    privilege = int(srv[i]['access'][j]['privilege'])

                    if key in self._cfg:
                        log.e('Invalid extsrv.json, duplicated key: {}\n'.format(key))
                        return False

                    self._cfg[key] = {
                        'name': srv_name,
                        'desc': srv_desc,
                        'secret': secret,
                        'privilege': privilege
                    }
        except:
            log.e('Invalid extsrv.json\n')
            return False

        return True

    def get_secret_info(self, key):
        if key not in self._cfg:
            return None
        return self._cfg[key]


def tp_ext_srv_cfg():
    """
    :rtype : ExtSrvCfg
    """

    import builtins
    if '__ext_srv_cfg__' not in builtins.__dict__:
        builtins.__dict__['__ext_srv_cfg__'] = ExtSrvCfg()
    return builtins.__dict__['__ext_srv_cfg__']
