"use strict";

ywl.on_init = function (cb_stack, cb_args) {
    console.log(ywl.page_options);

    var dom = {
        info: $('#info-kv'),
//        , btn_maintance: $('#btn_maintenance')
        btn_db_export: $('#btn-db-export'),
        btn_db_import: $('#btn-db-import'),
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

    dom.btn_db_export.click(function () {
        alert('not implement.');
        window.location.href = '/config/export-database'
    });
    dom.btn_db_import.click(function () {
        alert('not implement.');

        var _fn_sure = function (cb_stack, cb_args) {
            var html = '<input id="upload-file" type="file" name="sqlfile" class="hidden" value="" style="display: none;"/>';
            dom.btn_db_import.after($(html));
            var update_file = $("#upload-file");

            update_file.change(function () {
                var file_path = $(this).val();
                if (file_path === null || file_path === undefined || file_path === '') {
                    return;
                }
                ywl.do_upload_sql_file();
            });

            update_file.trigger('click');
        };

        var cb_stack = CALLBACK_STACK.create();
        ywl.dlg_confirm(cb_stack, {
            msg: '<p><strong>注意：操作不可恢复！！</strong></p><p>您确定要清除所有现有数据，然后导入sql文件吗？</p>',
            fn_yes: _fn_sure
        });
    });

    cb_stack.exec();
};

ywl.do_upload_sql_file = function () {
    var param = {};
    $.ajaxFileUpload({
        url: "/config/import-database",// 需要链接到服务器地址
        secureuri: false,
        fileElementId: "upload-file", // 文件选择框的id属性
        dataType: 'text', // 服务器返回的格式，可以是json
        data: param,
        success: function (data) {
            $('#upload-file').remove();
            var ret = JSON.parse(data);
            if (ret.code === TPE_OK) {
//                g_host_table.reload();
                ywl.notify_success('导入sql成功！');
//                if (ret.data.msg.length > 0) {
//                    var html = [];
//                    html.push('<ul>');
//                    for (var i = 0, cnt = ret.data.msg.length; i < cnt; ++i) {
//                        html.push('<li>');
//                        html.push('<span style="font-weight:bold;color:#993333;">' + ret.data.msg[i].reason + '</span><br/>');
//                        html.push(ret.data.msg[i].line);
//                        html.push('</li>');
//                    }
//                    html.push('</ul>');
//
//                    // $('#batch_add_host_result').html(html.join(''));
////                    $('#dialog_batch_add_host').modal({backdrop: 'static'});
//                }
            } else {
                ywl.notify_error('导入sql失败！ 错误号：' + ret.code);
            }
        },
        error: function () {
            $('#upload-file').remove();
            ywl.notify_error('网络故障，导入sql失败！');
        }
    });
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
