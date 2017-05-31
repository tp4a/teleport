# -*- coding: utf-8 -*-

import os
import time
import json
import tornado.gen
import tornado.httpclient

from eom_ver import *
from eom_app.app.db import get_db
from eom_app.app.configs import app_cfg
from eom_app.app.util import *
from eom_common.eomcore.logger import log
from .base import TPBaseAdminAuthHandler, TPBaseAdminAuthJsonHandler

cfg = app_cfg()


class IndexHandler(TPBaseAdminAuthHandler):
    @tornado.gen.coroutine
    def get(self):
        core_detected = False
        req = {'method': 'get_config', 'param': []}
        _yr = async_post_http(req)
        return_data = yield _yr
        if return_data is not None:
            if 'code' in return_data:
                _code = return_data['code']
                if _code == 0:
                    cfg.update_core(return_data['data'])
                    core_detected = True

        if not core_detected:
            cfg.update_core(None)

        _db = get_db()

        db = {'type': _db.db_type}
        if _db.db_type == _db.DB_TYPE_SQLITE:
            db['sqlite_file'] = _db.sqlite_file
        elif _db.db_type == _db.DB_TYPE_MYSQL:
            db['mysql_host'] = _db.mysql_host
            db['mysql_port'] = _db.mysql_port
            db['mysql_db'] = _db.mysql_db
            db['mysql_user'] = _db.mysql_user

        param = {
            'core': cfg.core,
            'web': {
                'version': TS_VER,
                'core_server_rpc': cfg.common.core_server_rpc,
                'db': db
            }
        }
        self.render('config/index.mako', page_param=json.dumps(param))


class ExportDatabaseHandler(TPBaseAdminAuthHandler):
    def get(self):
        now = time.localtime(time.time())
        dt = '{:04d}{:02d}{:02d}-{:02d}{:02d}{:02d}'.format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)

        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=teleport-database-export-{}.sql'.format(dt))

        sql = get_db().export_to_sql()

        # self.write("分组ID, 操作系统, IP地址, 端口, 协议, 状态, 描述, 系统用户, 系统密码, 是否加密, 附加参数, 密钥ID, 认证类型\n".encode('gbk'))
        self.write(sql)
        self.finish()


class ImportDatabaseHandler(TPBaseAdminAuthHandler):
    # TODO: 导入操作可能会比较耗时，应该分离导入和获取导入状态两个过程，在页面上可以呈现导入进度，并列出导出成功/失败的项

    @tornado.gen.coroutine
    def post(self):
        """
        sql导入规则：
        以事务方式执行sql语句
        """
        ret = dict()
        ret['code'] = 0
        ret['message'] = ''
        # ret['data'] = {}
        # ret['data']['msg'] = list()  # 记录跳过的行（格式不正确，或者数据重复等）
        sql_filename = ''

        try:
            upload_path = os.path.join(cfg.data_path, 'tmp')  # 文件的暂存路径
            if not os.path.exists(upload_path):
                os.mkdir(upload_path)
            file_metas = self.request.files['sqlfile']  # 提取表单中‘name’为‘file’的文件元数据
            for meta in file_metas:
                now = time.localtime(time.time())
                tmp_name = 'upload-{:04d}{:02d}{:02d}{:02d}{:02d}{:02d}.sql'.format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
                sql_filename = os.path.join(upload_path, tmp_name)
                with open(sql_filename, 'wb') as f:
                    f.write(meta['body'])

            # file encode maybe utf8 or gbk... check it out.
            file_encode = None
            with open(sql_filename, encoding='utf8') as f:
                try:
                    f.readlines()
                    file_encode = 'utf8'
                except:
                    pass

            if file_encode is None:
                os.remove(sql_filename)
                log.e('file `{}` unknown encode, neither GBK nor UTF8.\n'.format(sql_filename))
                ret['code'] = -2
                ret['message'] = 'upload sql file is not utf8 encode.'
                return self.write(json.dumps(ret).encode('utf8'))

            with open(sql_filename, encoding=file_encode) as f:
                db = get_db()
                sql = []
                lines = f.readlines()
                for line in lines:
                    line = line.strip('\r\n')
                    if line .startswith('TRUNCATE TABLE '):
                        x = line.split(' ', 2)
                        _table_name = '`{}{}`'.format(get_db().table_prefix, x[2][1:-2])
                        if db.db_type == db.DB_TYPE_MYSQL:
                            x[2] = _table_name
                            line = ' '.join(x)
                            line += ';'
                            sql.append(line)
                        elif db.db_type == db.DB_TYPE_SQLITE:
                            #delete from TableName;  //清空数据
                            # update sqlite_sequence SET seq = 0 where name ='TableName';//自增长ID为0
                            sql.append('DELETE FROM {};'.format(_table_name))
                            sql.append('UPDATE `sqlite_sequence` SET `seq`=0 WHERE `name`="{}";'.format(_table_name[1:-1]))

                    if line.startswith('INSERT INTO '):
                        x = line.split(' ', 3)
                        _table_name = '`{}{}`'.format(db.table_prefix, x[2][1:-1])
                        x[2] = _table_name
                        line = ' '.join(x)
                        # print(line)
                        sql.append(line)

                for line in sql:
                    db_ret = get_db().exec(line)
                    if not db_ret:
                        ret['code'] = -1
                        ret['message'] = 'SQL语句执行出错: {}'.format(line)
                        return self.write(json.dumps(ret).encode('utf8'))

            ret['code'] = 0
            return self.write(json.dumps(ret).encode('utf8'))
        except:
            log.e('error\n')
            ret['code'] = -6
            ret['message'] = '发生异常.'
            return self.write(json.dumps(ret).encode('utf8'))

        finally:
            if os.path.exists(sql_filename):
                os.remove(sql_filename)
