"use strict";

ywl.on_init = function (cb_stack, cb_args) {
    console.log(ywl.page_options);

    var dom = {
        info: $('#info-kv')
//        , btn_maintance: $('#btn_maintenance')
    };

    var html = [];

    // 版本号
    html.push(ywl._make_info('WEB服务版本', ywl.page_options.web.version));
    if (!ywl.page_options.core.detected) {
        html.push(ywl._make_info('核心服务版本', '<span class="error">未能连接到核心服务</span>'));
    } else {
        html.push(ywl._make_info('核心服务版本', ywl.page_options.core.version));
    }

    if (ywl.page_options.web.db.type === DB_TYPE_SQLITE) {
        html.push(ywl._make_info('数据库类型', 'SQLite'));
        html.push(ywl._make_info('sqlite-file', ywl.page_options.web.db.sqlite_file));
    } else if (ywl.page_options.web.db.type === DB_TYPE_MYSQL) {
        html.push(ywl._make_info('数据库类型', 'MySQL'));
        html.push(ywl._make_info('mysql-host', ywl.page_options.web.db.mysql_host));
        html.push(ywl._make_info('mysql-port', ywl.page_options.web.db.mysql_port));
        html.push(ywl._make_info('mysql-db', ywl.page_options.web.db.mysql_db));
        html.push(ywl._make_info('mysql-user', ywl.page_options.web.db.mysql_user));
    } else {
        html.push(ywl._make_info('数据库类型', '未知'));
    }

    html.push(ywl._make_info('核心服务通讯地址', ywl.page_options.web.core_server_rpc));
    if (ywl.page_options.core.detected) {
        html.push(ywl._make_info('WEB服务通讯地址', ywl.page_options.core.web_server_rpc));
        html.push(ywl._make_protocol_info('RDP 端口', ywl.page_options.core.rdp));
        html.push(ywl._make_protocol_info('SSH 端口', ywl.page_options.core.ssh));
//        html.push(ywl._make_protocol_info('TELNET 端口', ywl.page_options.core.telnet));
        html.push(ywl._make_info('录像文件路径', ywl.page_options.core.replay_path));
    }

    dom.info.append(html.join(''));

//    dom.btn_maintance.click(function () {
//        var _fn_sure = function (cb_stack, cb_args) {
//            ywl.ajax_post_json('/maintenance/rpc', {cmd: 'enter_maintenance_mode'},
//                function (ret) {
//                    if (ret.code === TPE_OK) {
//                        window.location.href = '/maintenance/index';
//                    }
//                    else {
//                        ywl.notify_error('无法进入维护模式：' + ret.message);
//                    }
//                },
//                function () {
//                    ywl.notify_error('网络故障，无法进入维护模式！');
//                }
//            );
//        };
//        var cb_stack = CALLBACK_STACK.create();
//
//        ywl.dlg_confirm(cb_stack, {
//            msg: '<p>您确定要进入维护模式吗？！！</p>',
//            fn_yes: _fn_sure
//        });
//    });
//
    cb_stack.exec();
};

ywl._make_protocol_info = function (name, p) {
    if (_.isUndefined(p))
        return ywl._make_info(name, '未能检测到');
    // <tr><td class="key">RDP 端口：</td><td class="value">52089</td></tr>
    var val = p.port;
    if (!p.enable) {
        val = '<span class="disabled">' + val + '（未启用）</span>';
    }

    return ywl._make_info(name, val);
};

ywl._make_info = function (key, value) {
    if (_.isUndefined(value))
        value = '<span class="error">未能检测到</span>';
    return '<tr><td class="key">' + key + '：</td><td class="value">' + value + '</td></tr>';
};
