"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        btn_refresh_session: $('#btn-refresh-session'),
        chkbox_session_select_all: $('#table-session-select-all'),
        btn_kill_sessions: $('#btn-kill-sessions')
    };

    cb_stack.add($app.create_controls);
    cb_stack.exec();
};

//===================================
// 创建页面控件对象
//===================================
$app.create_controls = function (cb_stack) {

    //-------------------------------
    // 资产列表表格
    //-------------------------------
    var table_session_options = {
        dom_id: 'table-session',
        data_source: {
            type: 'ajax-post',
            url: '/audit/get-records',
            restrict: {'state': [TP_SESS_STAT_RUNNING, TP_SESS_STAT_STARTED]}
        },
        column_default: {sort: false, align: 'left'},
        columns: [
            {
                // title: '<input type="checkbox" id="user-list-select-all" value="">',
                title: '',
                key: 'chkbox',
                //sort: false,
                width: 36,
                align: 'center',
                render: 'make_check_box',
                fields: {id: 'id'}
            },
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
                sort: true,
                sort_asc: false,
                fields: {sid: 'sid'}
            },
            {
                title: '用户',
                key: 'user',
                //sort: true,
                //header_render: 'filter_search_host',
                render: 'user',
                fields: {user_username: 'user_username', user_surname: 'user_surname'}
            },
            {
                title: '来源',
                key: 'client_ip',
                //sort: true,
                //header_render: 'filter_search_host',
                //render: 'host_info',
                fields: {client_ip: 'client_ip'}
            },
            {
                title: '远程连接',
                key: 'remote',
                //sort: true,
                //header_render: 'filter_search_host',
                render: 'remote',
                fields: {acc_username: 'acc_username', host_ip: 'host_ip', conn_ip: 'conn_ip', conn_port: 'conn_port'}
            },
            {
                title: '远程协议',
                key: 'protocol_type',
                align: 'center',
                width: 80,
                // align: 'center',
                // width: 36,
                //sort: true
                // header_render: 'filter_os',
                render: 'protocol',
                fields: {protocol_type: 'protocol_type', protocol_sub_type: 'protocol_sub_type'}
            },
            {
                title: '开始时间',
                key: 'time_begin',
                //sort: true,
                //sort_asc: false,
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
        ],

        // 重载回调函数
        on_header_created: $app.on_table_session_header_created,
        on_render_created: $app.on_table_session_render_created,
        on_cell_created: $app.on_table_session_cell_created
    };

    $app.table_session = $tp.create_table(table_session_options);
    cb_stack
        .add($app.table_session.load_data)
        .add($app.table_session.init);

    //-------------------------------
    // 用户列表相关过滤器
    //-------------------------------
    $tp.create_table_header_filter_search($app.table_session, {
        name: 'search_host',
        place_holder: '搜索：主机IP/名称/描述/资产编号/等等...'
    });
    // 从cookie中读取用户分页限制的选择
    $tp.create_table_paging($app.table_session, 'table-session-paging',
        {
            per_page: Cookies.get($app.page_id('ops_session') + '_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('ops_session') + '_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_session, 'table-session-pagination');

    //-------------------------------
    // 页面控件事件绑定
    //-------------------------------
    $app.dom.btn_refresh_session.click(function () {
        $app.table_session.load_data();
    });
    $app.dom.chkbox_session_select_all.click(function () {
        var _objects = $('#' + $app.table_session.dom_id + ' tbody').find('[data-check-box]');
        if ($(this).is(':checked')) {
            $.each(_objects, function (i, _obj) {
                $(_obj).prop('checked', true);
            });
        } else {
            $.each(_objects, function (i, _obj) {
                $(_obj).prop('checked', false);
            });
        }
    });
    $app.dom.btn_kill_sessions.click($app.on_btn_kill_sessions_click);

    cb_stack.exec();
};

$app.on_table_session_cell_created = function (tbl, row_id, col_key, cell_obj) {
    if (col_key === 'chkbox') {
        cell_obj.find('[data-check-box]').click(function () {
            // 同步相同会话ID的选中状态
            var _obj = $(this);
            var checked = _obj.is(':checked');
            var _row_data = tbl.get_row(_obj);
            var _objs = $('#' + $app.table_session.dom_id + ' tbody').find('[data-check-box]');
            $.each(_objs, function (i, _o) {
                var _rd = tbl.get_row(_o);
                if (_row_data.sid === _rd.sid) {
                    $(_o).prop('checked', checked);
                }
            });


            $app.check_host_all_selected();
        });
    }
};

$app.check_host_all_selected = function (cb_stack) {
    var _all_checked = true;
    var _objs = $('#' + $app.table_session.dom_id + ' tbody').find('[data-check-box]');
    if (_objs.length === 0) {
        _all_checked = false;
    } else {
        $.each(_objs, function (i, _obj) {
            if (!$(_obj).is(':checked')) {
                _all_checked = false;
                return false;
            }
        });
    }

    if (_all_checked) {
        $app.dom.chkbox_session_select_all.prop('checked', true);
    } else {
        $app.dom.chkbox_session_select_all.prop('checked', false);
    }

    if (cb_stack)
        cb_stack.exec();
};

$app.on_table_session_render_created = function (render) {
    // render.filter_host_state = function (header, title, col) {
    //     var _ret = ['<div class="tp-table-filter tp-table-filter-' + col.cell_align + '">'];
    //     _ret.push('<div class="tp-table-filter-inner">');
    //     _ret.push('<div class="search-title">' + title + '</div>');
    //
    //     // 表格内嵌过滤器的DOM实体在这时生成
    //     var filter_ctrl = header._table_ctrl.get_filter_ctrl('host_state');
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
    //     var filter_ctrl = header._table_ctrl.get_filter_ctrl('search_host');
    //     _ret.push(filter_ctrl.render());
    //
    //     _ret.push('</div></div>');
    //
    //     return _ret.join('');
    // };

    render.make_check_box = function (row_id, fields) {
        return '<span><input type="checkbox" data-check-box="' + fields.id + '" data-row-id="' + row_id + '"></span>';
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

    render.protocol = function (row_id, fields) {
        switch (fields.protocol_sub_type) {
            case 100:
                return '<span class="label label-primary">RDP</span>';
            case 200:
                return '<span class="label label-success">SSH</span>';
            case 201:
                return '<span class="label label-success">SFTP</span>';
            case 300:
                return '<span class="label label-success">TELNET</span>';
            default:
                return '<span class="label label-danger">未知</span>';
        }
    };

    render.time_begin = function (row_id, fields) {
        return tp_format_datetime(tp_utc2local(fields.time_begin), 'MM-dd HH:mm:ss');
    };

    render.time_cost = function (row_id, fields) {
        if (fields.time_end === 0) {
            var _style = 'info';
            if (fields.state === TP_SESS_STAT_RUNNING)
                _style = 'warning';
            else if (fields.state === TP_SESS_STAT_STARTED)
                _style = 'primary';
            return '<span class="label label-' + _style + '"><i class="fa fa-cog fa-spin"></i> ' + tp_second2str(tp_local2utc() - fields.time_begin) + '</span>';
        } else {
            return tp_second2str(fields.time_end - fields.time_begin);
        }
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
            default:
                msg = '未知状态 [' + fields.state + ']';
        }

        return '<span class="label label-danger">' + msg + '</span>';
    };

    render.record_action = function (row_id, fields) {
        return '';
        // var ret = [];
        //
        // if (fields.state >= TP_SESS_STAT_STARTED) {
        //     if (fields.time_end === 0) {
        //         ret.push('<a href="javascript:;" class="btn btn-sm btn-warning" data-action="sync" data-record-id="' + fields.id + '"><i class="fa fa-clone fa-fw"></i> 同步</a>&nbsp');
        //     } else {
        //         ret.push('<a href="javascript:;" class="btn btn-sm btn-primary" data-action="play" data-record-id="' + fields.id + '"><i class="fas fa-caret-square-right fa-fw"></i> 播放</a>&nbsp');
        //     }
        //     if (fields.protocol_sub_type !== TP_PROTOCOL_TYPE_RDP_DESKTOP) {
        //         ret.push('<a href="javascript:;" class="btn btn-sm btn-info" data-action="cmd" data-record-id="' + fields.id + '"><i class="far fa-file-alt fa-fw"></i> 日志</a>&nbsp');
        //     }
        // }
        //
        // return ret.join('');
    };
};

$app.on_table_session_header_created = function (header) {
    // $app.dom.btn_table_host_reset_filter = $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]');
    // $app.dom.btn_table_host_reset_filter.click(function () {
    //     CALLBACK_STACK.create()
    //         .add(header._table_ctrl.load_data)
    //         .add(header._table_ctrl.reset_filters)
    //         .exec();
    // });

    // TODO: 当过滤器不是默认值时，让“重置过滤器按钮”有呼吸效果，避免用户混淆 - 实验性质
    // var t1 = function(){
    //     $app.dom.btn_table_host_reset_filter.fadeTo(1000, 1.0, function(){
    //         $app.dom.btn_table_host_reset_filter.fadeTo(1000, 0.2, t1);
    //     });
    // };
    // $app.dom.btn_table_host_reset_filter.fadeTo(1000, 0.2, t1);

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    //header._table_ctrl.get_filter_ctrl('search_host').on_created();
    // header._table_ctrl.get_filter_ctrl('role').on_created();
    //header._table_ctrl.get_filter_ctrl('host_state').on_created();
};

$app.get_selected_sessions = function (tbl) {
    var records = [];
    var _objs = $('#' + $app.table_session.dom_id + ' tbody tr td input[data-check-box]');
    $.each(_objs, function (i, _obj) {
        if ($(_obj).is(':checked')) {
            var _row_data = tbl.get_row(_obj);
            records.push(_row_data.sid);
        }
    });
    return records;
};

$app.on_btn_kill_sessions_click = function () {
    var sessions = $app.get_selected_sessions($app.table_session);
    console.log(sessions);
    if (sessions.length === 0) {
        $tp.notify_error('请选择要强行终止的会话！');
        return;
    }

    var _fn_sure = function (cb_stack, cb_args) {
        $tp.ajax_post_json('/ops/kill', {sessions: sessions},
            function (ret) {
                if (ret.code === TPE_OK) {
                    setTimeout(function () {
                        var _cb = CALLBACK_STACK.create();
                        _cb.add($app.check_host_all_selected)
                            .add($app.table_session.load_data)
                            .exec();

                        $tp.notify_success('强行终止会话操作成功！');
                    }, 1500);
                } else {
                    $tp.notify_error('强行终止会话失败：' + tp_error_msg(ret.code, ret.message));
                }

                cb_stack.exec();
            },
            function () {
                $tp.notify_error('网络故障，强行终止会话操作失败！');
                cb_stack.exec();
            }
        );
    };

    var cb_stack = CALLBACK_STACK.create();
    $tp.dlg_confirm(cb_stack, {
        msg: '您确定要强行终止这些会话吗？',
        fn_yes: _fn_sure
    });
};
