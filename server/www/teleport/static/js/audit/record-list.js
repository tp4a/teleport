"use strict";

const FILTER_TIME_TYPE_ALL = 0;
const FILTER_TIME_TYPE_TODAY = 1;
const FILTER_TIME_TYPE_WEEK = 2;
const FILTER_TIME_TYPE_MONTH = 3;
const FILTER_TIME_TYPE_CUSTOMER = 4;

$app.on_init = function (cb_stack) {
    $app.dom = {
        storage_info: $('#storage-info'),
        btn_refresh_record: $('#btn-refresh-record'),
        btn_toggle_filter: $('#btn-toggle-filter'),

        filter_area: $('#filter-area'),
        filter_time_customer_area: $('#filter-time-customer-area'),
        filter_time_all: $('#filter-btn-time-all'),
        filter_time_today: $('#filter-btn-time-today'),
        filter_time_week: $('#filter-btn-time-week'),
        filter_time_month: $('#filter-btn-time-month'),
        filter_time_customer: $('#filter-btn-time-customer'),
        filter_time_from: $('#filter-time-from'),
        filter_time_to: $('#filter-time-to'),

        filter_protocol: $('#filter-protocol-type'),
        filter_session_id: $('#filter-session-id'),
        filter_remote_host_addr: $('#filter-remote-host-addr'),
        filter_remote_acc: $('#filter-remote-acc'),
        filter_client_ip: $('#filter-client-ip'),
        filter_tp_user: $('#filter-tp-user'),

        btn_search: $('#btn-search'),
        btn_reset_filter: $('#btn-reset-filter')
    };

    $app.dom.storage_info.html('总 ' + tp_size2str($app.options.total_size, 2) + '，' + '可用 ' + tp_size2str($app.options.free_size, 2));

    $app.filter_shown = false;
    $app.filter_time_type = FILTER_TIME_TYPE_ALL;

    cb_stack
        .add($app.create_controls)
        .add($app.load_role_list);

    cb_stack.exec();
};

$app.create_table_record_filter = function (tbl) {
    let _tblf = {};
    _tblf._table_ctrl = tbl;

    _tblf._table_ctrl.add_filter_ctrl('record_filter', _tblf);

    // _tblf.init = function (cb_stack) {
    //     cb_stack.exec();
    // };

    _tblf.get_filter = function () {
        let ret = {};
        ret['time_type'] = $app.filter_time_type;

        if ($app.filter_time_type === FILTER_TIME_TYPE_ALL) {
            // no filter for time.
        } else if ($app.filter_time_type === FILTER_TIME_TYPE_TODAY) {
            ret['time_from'] = Math.floor(new Date((new Date().setHours(0, 0, 0, 0))).getTime() / 1000);
            ret['time_to'] = Math.floor(new Date((new Date().setHours(23, 59, 59, 999))).getTime() / 1000);
        } else if ($app.filter_time_type === FILTER_TIME_TYPE_WEEK) {
            let now = new Date();
            let thisYear = now.getFullYear();
            let thisMonth = now.getMonth();
            let thisDay = now.getDate();
            let thisDayOfWeek = now.getDay();
            let weekStart = new Date(thisYear, thisMonth, thisDay - thisDayOfWeek + 1);
            let weekEnd = new Date(thisYear, thisMonth, thisDay + (7 - thisDayOfWeek), 23, 59, 59, 999);
            ret['time_from'] = Math.floor(weekStart.getTime() / 1000);
            ret['time_to'] = Math.floor(weekEnd.getTime() / 1000);
        } else if ($app.filter_time_type === FILTER_TIME_TYPE_MONTH) {
            let now = new Date();
            let thisYear = now.getFullYear();
            let thisMonth = now.getMonth();
            let monthStart = new Date(thisYear, thisMonth, 1);
            let nextMonthStart = new Date(thisYear, thisMonth + 1, 1);
            let days = (nextMonthStart - monthStart) / (1000 * 60 * 60 * 24);
            let monthEnd = new Date(thisYear, thisMonth, days, 23, 59, 59, 999);
            ret['time_from'] = Math.floor(monthStart.getTime() / 1000);
            ret['time_to'] = Math.floor(monthEnd.getTime() / 1000);
        } else if ($app.filter_time_type === FILTER_TIME_TYPE_CUSTOMER) {
            let start_time = $app.dom.filter_time_from.find('input').val();
            let end_time = $app.dom.filter_time_to.find('input').val();
            if (start_time.length > 0)
                ret['time_from'] = Math.floor(new Date(start_time).getTime() / 1000);
            if (end_time.length > 0)
                ret['time_to'] = Math.floor(new Date(end_time).getTime() / 1000);
        }

        ret['protocol'] = parseInt($app.dom.filter_protocol.val());

        let client_ip = $app.dom.filter_client_ip.val().trim();
        let remote_addr = $app.dom.filter_remote_host_addr.val().trim();
        let session_id = $app.dom.filter_session_id.val().trim();
        let remote_acc = $app.dom.filter_remote_acc.val().trim();
        let tp_user = $app.dom.filter_tp_user.val().trim();

        if (client_ip.length > 0)
            ret['client_ip'] = client_ip;
        if (remote_addr.length > 0)
            ret['remote_addr'] = remote_addr;
        if (session_id.length > 0)
            ret['sid'] = session_id;
        if (remote_acc.length > 0)
            ret['remote_acc'] = remote_acc;
        if (tp_user.length > 0)
            ret['user_name'] = tp_user;

        console.log('get-filter:', ret);
        return ret;
    };
};


//===================================
// 创建页面控件对象
//===================================
$app.create_controls = function (cb_stack) {

    //-------------------------------
    // 资产列表表格
    //-------------------------------
    let table_record_options = {
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
    $app.create_table_record_filter($app.table_record);
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

    // 切换过滤器显示
    $app.dom.btn_toggle_filter.click(function () {
        if ($app.filter_shown) {
            $app.dom.filter_area.hide('fast', function () {
                $app.filter_shown = false;
                $app.dom.btn_toggle_filter.text('显示过滤器');
            });
        } else {
            $app.dom.filter_area.show('fast', function () {
                $app.filter_shown = true;
                $app.dom.btn_toggle_filter.text('隐藏过滤器');
            });
        }
    });

    // 时间选择按钮
    $app._switch_filter_time_type = function (dom, filter_type) {
        console.log(dom, filter_type);
        $app.dom.filter_time_all.removeClass('btn-info').addClass('btn-default');
        $app.dom.filter_time_today.removeClass('btn-info').addClass('btn-default');
        $app.dom.filter_time_week.removeClass('btn-info').addClass('btn-default');
        $app.dom.filter_time_month.removeClass('btn-info').addClass('btn-default');
        $app.dom.filter_time_customer.removeClass('btn-info').addClass('btn-default');

        dom.removeClass('btn-default').addClass('btn-info');
        $app.filter_time_type = filter_type;

        if (filter_type === FILTER_TIME_TYPE_CUSTOMER)
            $app.dom.filter_time_customer_area.show('fast');
        else
            $app.dom.filter_time_customer_area.hide('fast');
    };
    $app.dom.filter_time_all.click(function () {
        $app._switch_filter_time_type($(this), FILTER_TIME_TYPE_ALL);
    });
    $app.dom.filter_time_today.click(function () {
        $app._switch_filter_time_type($(this), FILTER_TIME_TYPE_TODAY);
    });
    $app.dom.filter_time_week.click(function () {
        $app._switch_filter_time_type($(this), FILTER_TIME_TYPE_WEEK);
    });
    $app.dom.filter_time_month.click(function () {
        $app._switch_filter_time_type($(this), FILTER_TIME_TYPE_MONTH);
    });
    $app.dom.filter_time_customer.click(function () {
        $app._switch_filter_time_type($(this), FILTER_TIME_TYPE_CUSTOMER);
    });

    // 时间选择框
    $app.dom.filter_time_from.datetimepicker({format: "yyyy-mm-dd hh:ii", autoclose: true, todayHighlight: true, todayBtn: true, language: "zh-CN"});
    $app.dom.filter_time_to.datetimepicker({format: "yyyy-mm-dd hh:ii", autoclose: true, todayHighlight: true, todayBtn: true, language: "zh-CN"});
    $app._on_filter_time_changed = function () {
        let start_time = $app.dom.filter_time_from.find('input').val();
        let end_time = $app.dom.filter_time_to.find('input').val();

        if (start_time === '')
            $app.dom.filter_time_to.datetimepicker('setStartDate', '1970-01-01 00:00');
        else
            $app.dom.filter_time_to.datetimepicker('setStartDate', start_time);

        if (end_time === '')
            $app.dom.filter_time_from.datetimepicker('setEndDate', '9999-12-30 23:59');
        else
            $app.dom.filter_time_from.datetimepicker('setEndDate', end_time);

        // if (start_time !== '' && end_time !== '')
        //     $app._switch_filter_time_type(null, FILTER_TIME_TYPE_CUSTOMER);

    };
    $app.dom.filter_time_from.on('changeDate', function (ev) {
        $app._on_filter_time_changed();
    });
    $app.dom.filter_time_to.on('changeDate', function (ev) {
        $app._on_filter_time_changed();
    });

    // 查询
    $app.dom.btn_search.click(function () {
        $app.table_record.load_data(CALLBACK_STACK.create(), {});
    });
    // 重置过滤器
    $app.dom.btn_reset_filter.click(function () {
        $app._switch_filter_time_type($app.dom.filter_time_all, FILTER_TIME_TYPE_ALL);
        $app.dom.filter_protocol.val(0);
        $app.dom.filter_client_ip.val('');
        $app.dom.filter_remote_host_addr.val('');
        $app.dom.filter_session_id.val('');
        $app.dom.filter_remote_acc.val('');
        $app.dom.filter_tp_user.val('');

        $app.table_record.load_data(CALLBACK_STACK.create(), {});
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

            let row_data = tbl.get_row(row_id);
            // console.log('---', row_data);
            let action = $(this).attr('data-action');

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
        return tp_format_datetime(fields.time_begin, 'MM-dd HH:mm:ss');
    };

    render.time_cost = function (row_id, fields) {
        if (fields.state === TP_SESS_STAT_RUNNING || fields.state === TP_SESS_STAT_STARTED) {
            let _style = 'info';
            if (fields.state === TP_SESS_STAT_RUNNING)
                _style = 'warning';
            else if (fields.state === TP_SESS_STAT_STARTED)
                _style = 'primary';
            return '<span class="label label-' + _style + '"><i class="fa fa-cog fa-spin"></i> ' + tp_second2str(tp_timestamp_sec() - fields.time_begin) + '</span>';
        } else {
            if (fields.time_end === 0) {
                return '<span class="label label-danger"><i class="far fa-clock fa-fw"></i> 未知</span>';
            } else {
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
        //     return '<span class="label label-' + _style + '"><i class="fa fa-cog fa-spin"></i> ' + tp_second2str(tp_timestamp_sec() - fields.time_begin) + '</span>';
        // } else {
        //     return tp_second2str(fields.time_end - fields.time_begin);
        // }
    };

    render.state = function (row_id, fields) {
        let msg = '';
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
            case TP_SESS_STAT_ERR_CREATE_CHANNEL:
                msg = '无法创建数据通道';
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

        let ret = [];

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
    if (!$app.options.core_running) {
        $tp.notify_error(tp_error_msg(TPE_NO_CORE_SERVER), '无法播放。');
        return;
    }

    // if(!$assist.check())
    //     return;

    $assist.do_rdp_replay(
        record_id
        , function () {
            // func_success
        }
        , function (code, message) {
            if (code === TPE_NO_ASSIST) {
                $assist.alert_assist_not_found(code);
            } else
                $tp.notify_error('播放RDP操作录像失败：' + tp_error_msg(code, message));
        }
    );
};
