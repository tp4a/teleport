"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        storage_info: $('#storage-info'),
        btn_refresh_record: $('#btn-refresh-record')
    };

    $app.dom.storage_info.html('总 ' + tp_size2str($app.options.total_size, 2) + '，' + '可用 ' + tp_size2str($app.options.free_size, 2));

    cb_stack
        .add($app.create_controls)
        .add($app.load_role_list);

    cb_stack.exec();
};

//===================================
// 创建页面控件对象
//===================================
$app.create_controls = function (cb_stack) {

    //-------------------------------
    // 资产列表表格
    //-------------------------------
    var table_record_options = {
        dom_id: 'table-record',
        data_source: {
            type: 'ajax-post'
            , url: '/audit/get-records'
            //exclude: {'state': [TP_SESS_STAT_RUNNING, TP_SESS_STAT_STARTED]}
        },
        column_default: {sort: false, align: 'left'},
        columns: [
            {
                title: 'ID',
                key: 'id',
                sort: true,
                sort_asc: false,
                fields: {id: 'id'}
            },
            {
                title: '会话ID',
                key: 'sid',
                render: 'sid',
                width: 60,
                fields: {sid: 'sid'}
            },
            {
                title: '用户',
                key: 'user',
                render: 'user',
                fields: {user_username: 'user_username', user_surname: 'user_surname'}
            },
            {
                title: '来源',
                key: 'client_ip',
                fields: {client_ip: 'client_ip'}
            },
            {
                title: '远程连接',
                key: 'remote',
                render: 'remote',
                fields: {acc_username: 'acc_username', host_ip: 'host_ip', conn_ip: 'conn_ip', conn_port: 'conn_port'}
            },
            {
                title: '远程协议',
                key: 'protocol_type',
                align: 'center',
                width: 80,
                render: 'protocol',
                fields: {protocol_type: 'protocol_type', protocol_sub_type: 'protocol_sub_type'}
            },
            {
                title: '开始时间',
                key: 'time_begin',
                // sort: true,
                // sort_asc: false,
                render: 'time_begin',
                fields: {time_begin: 'time_begin'}
            },
            {
                title: '时长',
                key: 'time_cost',
                render: 'time_cost',
                fields: {time_begin: 'time_begin', time_end: 'time_end', state: 'state'}
            },
            {
                title: "状态",
                key: "state",
                //sort: true,
                width: 90,
                align: 'center',
                //header_render: 'filter_host_state',
                render: 'state',
                fields: {state: 'state'}
            },
            {
                title: '',
                key: 'action',
                //sort: false,
                //align: 'center',
                width: 160,
                render: 'record_action',
                fields: {id: 'id', state: 'state', time_end: 'time_end', protocol_sub_type: 'protocol_sub_type'}
            }
        ]

        // 重载回调函数
        //,on_header_created: $app.on_table_host_header_created
        , on_render_created: $app.on_table_host_render_created
        , on_cell_created: $app.on_table_host_cell_created
    };

    $app.table_record = $tp.create_table(table_record_options);
    cb_stack
        .add($app.table_record.load_data)
        .add($app.table_record.init);

    //-------------------------------
    // 用户列表相关过滤器
    //-------------------------------
    // $tp.create_table_header_filter_search($app.table_record, {
    //     name: 'search',
    //     place_holder: '搜索：主机IP/名称/描述/资产编号/等等...'
    // });
    // $app.table_record_role_filter = $tp.create_table_filter_role($app.table_record, $app.role_list);
    // $tp.create_table_header_filter_state($app.table_record, 'state', $app.obj_states, [TP_STATE_LOCKED]);
    // 从cookie中读取用户分页限制的选择
    $tp.create_table_paging($app.table_record, 'table-record-paging',
        {
            per_page: Cookies.get($app.page_id('audit_record') + '_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('audit_record') + '_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_record, 'table-record-pagination');

    //-------------------------------
    // 页面控件事件绑定
    //-------------------------------
    $app.dom.btn_refresh_record.click(function () {
        $app.table_record.load_data();
    });

    cb_stack.exec();
};

$app.on_table_host_cell_created = function (tbl, row_id, col_key, cell_obj) {
    // if (col_key === 'chkbox') {
    //     cell_obj.find('[data-check-box]').click(function () {
    //         $app.check_host_all_selected();
    //     });
    // } else
    if (col_key === 'action') {
        // 绑定系统选择框事件
        cell_obj.find('[data-action]').click(function () {

            var row_data = tbl.get_row(row_id);
            console.log('---', row_data);
            var action = $(this).attr('data-action');

            if (action === 'replay') {
                if (row_data.protocol_type === TP_PROTOCOL_TYPE_RDP) {
                    $app.do_replay_rdp(row_data.id, row_data.user_username, row_data.acc_username, row_data.host_ip, row_data.time_begin);
                    // window.open('/audit/replay/' + row_data.protocol_type + '/' + row_data.id);
                } else if (row_data.protocol_type === TP_PROTOCOL_TYPE_SSH) {
                    window.open('/audit/replay/' + row_data.protocol_type + '/' + row_data.id);
                } else if (row_data.protocol_type === TP_PROTOCOL_TYPE_TELNET) {
                    window.open('/audit/replay/' + row_data.protocol_type + '/' + row_data.id);
                }
            } else if (action === 'cmd') {
                //$app.dlg_accounts.show(row_id);
                window.open('/audit/command-log/' + row_data.protocol_type + '/' + row_data.id);
            }
        });
    } else if (col_key === 'ip') {
        cell_obj.find('[data-toggle="popover"]').popover({trigger: 'hover'});
        // } else if (col_key === 'account') {
        //     cell_obj.find('[data-action="add-account"]').click(function () {
        //         $app.dlg_accounts.show(row_id);
        //     });
    } else if (col_key === 'account_count') {
        cell_obj.find('[data-action="edit-account"]').click(function () {
            $app.dlg_accounts.show(row_id);
        });
    }
};

$app.on_table_host_render_created = function (render) {
    // render.filter_host_state = function (header, title, col) {
    //     var _ret = ['<div class="tp-table-filter tp-table-filter-' + col.cell_align + '">'];
    //     _ret.push('<div class="tp-table-filter-inner">');
    //     _ret.push('<div class="search-title">' + title + '</div>');
    //
    //     // 表格内嵌过滤器的DOM实体在这时生成
    //     var filter_ctrl = header._table_ctrl.get_filter_ctrl('state');
    //     _ret.push(filter_ctrl.render());
    //
    //     _ret.push('</div></div>');
    //
    //     return _ret.join('');
    // };
    //
    // render.filter_search_host = function (header, title, col) {
    //     var _ret = ['<div class="tp-table-filter tp-table-filter-input">'];
    //     _ret.push('<div class="tp-table-filter-inner">');
    //     _ret.push('<div class="search-title">' + title + '</div>');
    //
    //     // 表格内嵌过滤器的DOM实体在这时生成
    //     var filter_ctrl = header._table_ctrl.get_filter_ctrl('search');
    //     _ret.push(filter_ctrl.render());
    //
    //     _ret.push('</div></div>');
    //
    //     return _ret.join('');
    // };

    render.sid = function (row_id, fields) {
        return '<span class="mono">' + fields.sid + '</span>';
    };

    render.user = function (row_id, fields) {
        if (_.isNull(fields.user_surname) || fields.user_surname.length === 0 || fields.user_username === fields.user_surname) {
            return fields.user_username;
        } else {
            return fields.user_username + ' (' + fields.user_surname + ')';
        }
    };

    render.remote = function (row_id, fields) {
        if (fields.host_ip === fields.conn_ip)
            return fields.acc_username + '@' + fields.host_ip + ':' + fields.conn_port;
        else
            return '<div title="由' + fields.conn_ip + ':' + fields.conn_port + '路由">' + fields.acc_username + '@' + fields.host_ip + '</div>';
    };

    // fields: {protocol_type: 'protocol_type', protocol_sub_type: 'protocol_sub_type'}
    render.protocol = function (row_id, fields) {
        switch (fields.protocol_sub_type) {
            case 100:
                return '<span class="label label-primary">RDP</span>';
            case 200:
                return '<span class="label label-success">SSH</span>';
            case 201:
                return '<span class="label label-info">SFTP</span>';
            case 300:
                return '<span class="label label-warning">TELNET</span>';
            default:
                return '<span class="label label-danger">未知</span>';
        }
    };

    render.time_begin = function (row_id, fields) {
        return tp_format_datetime(tp_utc2local(fields.time_begin), 'MM-dd HH:mm:ss');
    };

    render.time_cost = function (row_id, fields) {
        if (fields.state === TP_SESS_STAT_RUNNING || fields.state === TP_SESS_STAT_STARTED) {
            var _style = 'info';
            if (fields.state === TP_SESS_STAT_RUNNING)
                _style = 'warning';
            else if (fields.state === TP_SESS_STAT_STARTED)
                _style = 'primary';
            return '<span class="label label-' + _style + '"><i class="fa fa-cog fa-spin"></i> ' + tp_second2str(tp_local2utc() - fields.time_begin) + '</span>';
        } else {
            if (fields.time_end === 0) {
                return '<span class="label label-danger"><i class="far fa-clock fa-fw"></i> 未知</span>';
            }
            else {
                if (fields.state === TP_SESS_STAT_ERR_START_RESET) {
                    return '<span class="label label-info"><i class="fa fa-exclamation-circle fa-fw"></i> ' + tp_second2str(fields.time_end - fields.time_begin) + '</span>';
                } else {
                    return tp_second2str(fields.time_end - fields.time_begin);
                }
            }
        }

        // if (fields.time_end === 0) {
        //     var _style = 'info';
        //     if (fields.state === TP_SESS_STAT_RUNNING)
        //         _style = 'warning';
        //     else if (fields.state === TP_SESS_STAT_STARTED)
        //         _style = 'primary';
        //     return '<span class="label label-' + _style + '"><i class="fa fa-cog fa-spin"></i> ' + tp_second2str(tp_local2utc() - fields.time_begin) + '</span>';
        // } else {
        //     return tp_second2str(fields.time_end - fields.time_begin);
        // }
    };

    render.state = function (row_id, fields) {
        var msg = '';
        switch (fields.state) {
            case TP_SESS_STAT_RUNNING:
                return '<span class="label label-warning">正在连接</span>';
            case TP_SESS_STAT_STARTED:
                return '<span class="label label-success">使用中</span>';
            case TP_SESS_STAT_END:
                return '<span class="label label-ignore">已结束</span>';
            case TP_SESS_STAT_ERR_AUTH_DENIED:
                msg = '认证失败';
                break;
            case TP_SESS_STAT_ERR_CONNECT:
                msg = '连接失败';
                break;
            case TP_SESS_STAT_ERR_BAD_SSH_KEY:
                msg = '私钥错误';
                break;
            case TP_SESS_STAT_ERR_START_INTERNAL:
            case TP_SESS_STAT_ERR_INTERNAL:
                msg = '内部错误';
                break;
            case TP_SESS_STAT_ERR_UNSUPPORT_PROTOCOL:
                msg = '协议不支持';
                break;
            case TP_SESS_STAT_ERR_BAD_PKG:
            case TP_SESS_STAT_ERR_START_BAD_PKG:
                msg = '数据格式错误';
                break;
            case TP_SESS_STAT_ERR_RESET:
            case TP_SESS_STAT_ERR_START_RESET:
                msg = '核心服务重置';
                break;
            case TP_SESS_STAT_ERR_IO:
            case TP_SESS_STAT_ERR_START_IO:
                msg = '网络通讯故障';
                break;
            case TP_SESS_STAT_ERR_SESSION:
                msg = '无效会话';
                break;
            case TP_SESS_STAT_ERR_AUTH_TYPE:
                msg = '无效认证方式';
                break;
            default:
                msg = '未知状态 [' + fields.state + ']';
        }

        return '<span class="label label-danger">' + msg + '</span>';
    };

    render.record_action = function (row_id, fields) {
        if (fields.state === TP_SESS_STAT_RUNNING || fields.state === TP_SESS_STAT_STARTED)
            return '';

        var ret = [];

        if (fields.state >= TP_SESS_STAT_STARTED || fields.state === TP_SESS_STAT_ERR_RESET) {
            if (fields.state === TP_SESS_STAT_STARTED) {
                //ret.push('<a href="javascript:;" class="btn btn-sm btn-warning" data-action="sync" data-record-id="' + fields.id + '"><i class="fa fa-clone fa-fw"></i> 同步</a>&nbsp');
            } else {
                if (fields.protocol_sub_type !== TP_PROTOCOL_TYPE_SSH_SFTP)
                    ret.push('<a href="javascript:;" class="btn btn-sm btn-primary" data-action="replay" data-record-id="' + fields.id + '"><i class="fa fas fas fa-caret-square-right fa-fw"></i> 回放</a>&nbsp');
            }
            if (fields.protocol_sub_type === TP_PROTOCOL_TYPE_SSH_SHELL
                || fields.protocol_sub_type === TP_PROTOCOL_TYPE_SSH_SFTP
            ) {
                ret.push('<a href="javascript:;" class="btn btn-sm btn-info" data-action="cmd" data-record-id="' + fields.id + '"><i class="fa fa-list-alt fa-fw"></i> 日志</a>&nbsp');
            }
        }

        return ret.join('');
    };
};

$app.do_replay_rdp = function (record_id, user_username, acc_username, host_ip, time_begin) {
    $assist.do_rdp_replay(
        {
            rid: record_id
            // , web: $tp.web_server // + '/audit/get_rdp_record/' + record_id // 'http://' + ip + ':' + port + '/log/replay/rdp/' + record_id;
            // , sid: Cookies.get('_sid')
            , user: user_username
            , acc: acc_username
            , host: host_ip
            , start: time_begin//tp_format_datetime(tp_utc2local(time_begin), 'yyyyMMdd-HHmmss')
        }
        , function () {
            // func_success
        }
        , function (code, message) {
            if (code === TPE_NO_ASSIST)
                $assist.alert_assist_not_found();
            else
                $tp.notify_error('播放RDP操作录像失败：' + tp_error_msg(code, message));
        }
    );
};


// $app.on_table_host_header_created = function (header) {
//     $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
//         CALLBACK_STACK.create()
//             .add(header._table_ctrl.load_data)
//             .add(header._table_ctrl.reset_filters)
//             .exec();
//     });
//
//     // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
//     header._table_ctrl.get_filter_ctrl('search').on_created();
// };

// $app.get_selected_record = function (tbl) {
//     var records = [];
//     var _objs = $('#' + $app.table_record.dom_id + ' tbody tr td input[data-check-box]');
//     $.each(_objs, function (i, _obj) {
//         if ($(_obj).is(':checked')) {
//             var _row_data = tbl.get_row(_obj);
//             records.push(_row_data.id);
//         }
//     });
//     return records;
// };

// $app.on_btn_remove_record_click = function () {
//     var records = $app.get_selected_record($app.table_record);
//     if (records.length === 0) {
//         $tp.notify_error('请选择要删除的会话记录！');
//         return;
//     }
//
//     var _fn_sure = function (cb_stack, cb_args) {
//         $tp.ajax_post_json('/user/remove-user', {users: users},
//             function (ret) {
//                 if (ret.code === TPE_OK) {
//                     cb_stack.add($app.check_host_all_selected);
//                     cb_stack.add($app.table_record.load_data);
//                     $tp.notify_success('删除用户账号操作成功！');
//                 } else {
//                     $tp.notify_error('删除用户账号操作失败：' + tp_error_msg(ret.code, ret.message));
//                 }
//
//                 cb_stack.exec();
//             },
//             function () {
//                 $tp.notify_error('网络故障，删除用户账号操作失败！');
//                 cb_stack.exec();
//             }
//         );
//     };
//
//     var cb_stack = CALLBACK_STACK.create();
//     $tp.dlg_confirm(cb_stack, {
//         msg: '<div class="alert alert-danger"><p><strong>注意：删除操作不可恢复！！</strong></p><p>删除用户账号将同时将其从所在用户组中移除，并且删除所有分配给此用户的授权！</p></div><p>如果您希望禁止某个用户登录本系统，可对其进行“禁用”操作！</p><p>您确定要移除所有选定的 <strong>' + user_list.length + '个</strong> 用户账号吗？</p>',
//         fn_yes: _fn_sure
//     });
// };
