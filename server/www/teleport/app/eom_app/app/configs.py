# -*- coding: utf-8 -*-

import os
import sys

from eom_common.eomcore.logger import log

__all__ = ['app_cfg']


class SwxDict(dict):
    """
    可以像属性一样访问字典的 Key，var.key 等同于 var['key']
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            # print(self.__class__.__name__)
            raise

    def __setattr__(self, name, val):
        self[name] = val


def swx_dict(obj):
    """
    将一个对象中的dict转变为EomDict类型
    """
    if isinstance(obj, dict):
        ret = SwxDict()
        for k in obj:
            # ret[k] = obj[k]
            if isinstance(obj[k], dict):
                ret[k] = swx_dict(obj[k])
            else:
                ret[k] = obj[k]
    else:
        ret = obj
    return ret


class ConfigFile(SwxDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.__file_name = None
        # self.__save_indent = 0
        # self.__loaded = False

    def load_str(self, module, code):
        m = type(sys)(module)
        m.__module_class__ = type(sys)
        m.__file__ = module

        try:
            exec(compile(code, module, 'exec'), m.__dict__)
        except Exception as e:
            log.e('%s\n' % str(e))
            # print(str(e))
            # if eom_dev_conf.debug:
            #     raise
            return False

        for y in m.__dict__:
            if '__' == y[:2]:
                continue
            if isinstance(m.__dict__[y], dict):
                self[y] = SwxDict()
                self._assign_dict(m.__dict__[y], self[y])
            else:
                self[y] = m.__dict__[y]

        return True

    def load(self, full_path, must_exists=True):
        try:
            f = open(full_path, encoding='utf8')
            code = f.read()
            f.close()
            self.__loaded = True
        except IOError:
            if must_exists:
                log.e('Can not load config file: %s\n' % full_path)
            return False

        module = os.path.basename(full_path)
        if not self.load_str(module, code):
            return False

        self.__file_name = full_path
        return True

    """
    def save(self, filename=None):
        if filename is None and not self.__loaded:
            # log.w('Can not save config file without file name.\n')
            return False
        _file_name = filename
        if _file_name is None:
            _file_name = self.__file_name
        if _file_name is None:
            log.e('Do not known which file to save to.\n')
            return False

        # 排序后保存
        m = [(k, self[k]) for k in sorted(self.keys())]

        self.__save_indent = 0
        s = self._save(m)

        # 尝试加载生成的要保存的配置字符串，如果加载成功，则保存到文件，否则报错
        x = ConfigFile()
        if not x.load_str('_eom_tmp_cfg_data_', s):
            log.e('Cannot generate config for save.\n')
            return False

        f = open(_file_name, 'w')
        f.write('# -*- coding: utf-8 -*-\n\n')
        f.write(s)
        f.close()
        return True

    def _save(self, var):
        s = ''
        for (k, v) in var:
            if self.__save_indent == 0 and k.find('_ConfigFile__') == 0:
                # 本类的成员变量不用保存
                continue

            if isinstance(v, dict):
                if self.__save_indent > 0:
                    s += "\n%s'%s' : {\n" % ('\t' * self.__save_indent, k)
                else:
                    s += "\n%s%s = {\n" % ('\t' * self.__save_indent, k)

                self.__save_indent += 1
                m = [(x, v[x]) for x in sorted(v.keys())]
                s += self._save(m)
                self.__save_indent -= 1
                if self.__save_indent > 0:
                    s += "%s},\n\n" % ('\t' * self.__save_indent)
                else:
                    s += "%s}\n\n" % ('\t' * self.__save_indent)

            else:
                if isinstance(v, str):
                    val = "'%s'" % v.replace("'", "\\'")
                else:
                    val = v

                if self.__save_indent > 0:
                    s += "%s'%s' : %s,\n" % ('\t' * self.__save_indent, k, val)
                else:
                    s += "%s%s = %s\n" % ('\t' * self.__save_indent, k, val)
        return s
    """

    def _assign_dict(self, _from, _to):
        for y in _from:
            if isinstance(_from[y], dict):
                _to[y] = SwxDict()
                self._assign_dict(_from[y], _to[y])
            else:
                _to[y] = _from[y]


_cfg = ConfigFile()
del ConfigFile


def app_cfg():
    global _cfg
    return _cfg


if __name__ == '__main__':
    cfg = ConfigFile()
