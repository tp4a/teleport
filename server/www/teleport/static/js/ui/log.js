"use strict";

ywl.on_init = function (cb_stack, cb_args) {
    var dom_id = '#ywl_log_list';

    //===================================
    // 创建页面控件对象
    //===================================
    // 表格数据
    var disk_rate = 0;
    if(0 == ywl.page_options.total_size) {
        $('#disk-status').text('未能连接到核心服务，无法获取操作日志路径');
    } else {
        disk_rate = parseInt(ywl.page_options.free_size * 100 / ywl.page_options.total_size);
        $('#disk-status').text('日志磁盘大小：' + size2str(ywl.page_options.total_size, 2) + '，剩余空间：' + size2str(ywl.page_options.free_size, 2) + '，空闲' + disk_rate + '%');
    }
    if (disk_rate < 10) {
        $('#disk-status').removeClass().addClass('badge badge-danger');
    } else if (disk_rate < 30) {
        $('#disk-status').removeClass().addClass('badge badge-warning');
    } else {
        $('#disk-status').removeClass().addClass('badge badge-ignore');
    }

    var host_table_options = {
        selector: dom_id + " [ywl-table='log-list']",
        data_source: {
            type: 'ajax-post',
            url: '/log/list'
        },
        column_default: {sort: false, header_align: 'center', cell_align: 'center'},
        columns: [
            {
                title: '<input type="checkbox" id="host-select-all" value="">',
                key: 'select_all',
                sort: false,
                width: 24,
                render: 'make_check_box',
                fields: {id: 'id'}
            },
            {title: "ID", key: "id"},
            {title: "操作者", key: "account_name"},
            {title: "系统用户", key: "user_name"},
            {title: "协议", key: "protocol", render: 'protocol', fields: {protocol: 'protocol'}},
            {title: "系统", key: "sys_type", width: 40, render: 'sys_type', fields: {sys_type: 'sys_type'}},
            {title: "远程主机地址", key: "host_ip", render: 'server_info', fields: {host_ip: 'host_ip', host_port: 'host_port'}},
            {title: "开始时间", key: "begin_time", width: 160, render: 'begin_time', fields: {begin_time: 'begin_time'}},
            {title: "耗时", key: "cost_time", render: 'cost_time', fields: {cost_time: 'cost_time', ret_code: 'ret_code'}},
            {title: "状态", key: "ret_code", render: 'ret_code', fields: {ret_code: 'ret_code'}},
            {
                title: "操作",
                key: "action",
                width: 160,
                header_align: 'left', cell_align: 'left',
                render: 'make_action_btn',
                fields: {ID: 'id', ret_code: 'ret_code', sys_type: 'sys_type', cost_time: 'cost_time', protocol: 'protocol'}
            }
        ],
        paging: {selector: dom_id + " [ywl-paging='log-list']", per_page: paging_normal},

        // 可用的属性设置
        //have_header: true or false

        // 可用的回调函数
        on_created: ywl.on_host_table_created,
        on_header_created: ywl.on_host_table_header_created

        // 可重载的函数（在on_created回调函数中重载）
        // on_render_created
        // on_header_created
        // on_paging_created
        // on_data_loaded
        // on_row_rendered
        // on_table_rendered
        // on_cell_created
        // on_begin_load
        // on_after_load

        // 可用的函数
        // load_data
        // cancel_load
        // set_data
        // add_row
        // remove_row
        // get_row
        // update_row
        // clear
        // reset_filter
    };

    var host_table = ywl.create_table(host_table_options);

    $(dom_id + " [ywl-filter='reload']").click(host_table.reload);

    $("#delete-log").click(function () {
        var log_list = [];
        var _objs = $(host_table.selector + " tbody tr td [data-check-box]");
        $.each(_objs, function (i, _obj) {
            if ($(_obj).is(':checked')) {
                var _row_data = host_table.get_row(_obj);
                log_list.push(_row_data.id);
            }
        });

        if (log_list.length === 0) {
            ywl.notify_error('请选择要批量删除的日志！');
            return;
        }

        var _fn_sure = function (cb_stack, cb_args) {
            ywl.ajax_post_json_time_out('/log/delete-log', {log_list: log_list}, 1000 * 30,
                function (ret) {
                    if (ret.code === TPE_OK) {
                        host_table.reload();
                        ywl.notify_success('删除日志成功！');
                    } else {
                        ywl.notify_error('删除日志失败！');
                    }
                },
                function () {
                    ywl.notify_error('网络故障，删除日志失败！');
                }
            );
        };
        var cb_stack = CALLBACK_STACK.create();

        ywl.dlg_confirm(cb_stack, {
            msg: '<p>您确定要删除选定的日志吗？此操作不可恢复！！</p>',
            fn_yes: _fn_sure
        });
    });

    ywl.create_table_filter_user_list(host_table, dom_id + " [ywl-filter='user-name']");

    ywl.create_table_filter_search_box(host_table, dom_id + " [ywl-filter='search']");

    cb_stack
        .add(host_table.load_data)
        .add(host_table.init)
        .exec();
};
ywl.on_host_table_header_created = function (tbl) {
    $('#host-select-all').click(function () {
        var _is_selected = $(this).is(':checked');
        $(tbl.selector + ' tbody').find('[data-check-box]').prop('checked', _is_selected);
    });
};
// 扩展/重载表格的功能
ywl.on_host_table_created = function (tbl) {

    tbl.on_cell_created = function (row_id, col_key, cell_obj) {
        if (col_key === 'select_all') {
            // 选择
            $('#host-select-' + row_id).click(function () {
                var _all_checked = true;
                var _objs = $(tbl.selector + ' tbody').find('[data-check-box]');
                $.each(_objs, function (i, _obj) {
                    if (!$(_obj).is(':checked')) {
                        _all_checked = false;
                        return false;
                    }
                });

                var select_all_dom = $('#host-select-all');
                if (_all_checked) {
                    select_all_dom.prop('checked', true);
                } else {
                    select_all_dom.prop('checked', false);
                }

                //ywl.update_add_to_batch_btn();
            });

        } else if (col_key === 'action') {
            var row_data = tbl.get_row(row_id);
            var protocol = parseInt(row_data.protocol);

            if (protocol === PROTOCOL_TYPE_RDP) {
                $(cell_obj).find('[ywl-btn-record]').click(function () {
                    var ip = window.location.hostname;
                    var port = parseInt(window.location.port);
                    var url = 'http://' + ip + ':' + port + '/log/replay/rdp/' + row_data.id;
                    var tail = 'log/replay/rdp/' + prefixInteger(row_data.id, 6);
                    var args = {};
                    args.id = parseInt(row_data.id);
                    args.host = ip;
                    args.port = port;
                    args.tail = tail;
                    args.url = url;
                    start_rdp_replay(args,
                        function () {
                            ywl.notify_success('RDP 录像播放器成功启动！');
                        },
                        function (code, msg) {
                            if (code === TPE_NO_ASSIST)
                                g_assist.alert_assist_not_found();
                            else {
                                ywl.notify_error(msg);
                                console.log('error:', msg)
                            }
                        });
                });
            }
            else if (protocol === PROTOCOL_TYPE_SSH) {
                $(cell_obj).find('[ywl-btn-record]').click(function () {
                    window.open('/log/record/' + parseInt(row_data.protocol) + '/' + row_data.id);
                });

                $(cell_obj).find('[ywl-btn-log]').click(function () {
                    window.open('/log/command-log/' + parseInt(row_data.protocol) + '/' + row_data.id);
                });
            }
        }
    };

    // 重载表格渲染器的部分渲染方式，加入本页面相关特殊操作f成功
    tbl.on_render_created = function (render) {
        render.ret_code = function (row_id, fields) {
            var msg = '';
            switch (fields.ret_code) {
                case 0:
                    return '<span class="badge badge-warning">使用中</span>'
                case 9999:
                    return '<span class="badge badge-success">成功</span>';
                case 1:
                    msg = '认证失败';
                    break;
                case 2:
                    msg = '连接失败';
                    break;
                case 3:
                    msg = '私钥错误';
                    break;
                case 4:
                    msg = '内部错误';
                    break;
                case 5:
                    msg = '协议不支持';
                    break;
                case 6:
                    msg = '通讯错误';
                    break;
                case 7:
                    msg = '错误重置';
                    break;
                default:
                    msg = fields.ret_code;
            }

            return '<span class="badge badge-danger">' + msg + '</span>';
        };
        render.begin_time = function (row_id, fields) {
            return '<span class="badge badge-primary mono">' + format_datetime(utc_to_local(fields.begin_time)) + ' </span>';
        };

        render.cost_time = function (row_id, fields) {
            if (fields.ret_code === 0) {
                return '<span class="badge badge-warning">使用中</span>';
            } else {
                return '<span class="badge badge-success">' + second2str(fields.cost_time) + '</span>';
            }
        };
        render.server_info = function (row_id, fields) {
            //return '<span class="badge badge-success mono">' + fields.host_ip + ':' + fields.host_port + '</span>';
            return '<span class="mono">' + fields.host_ip + ':' + fields.host_port + '</span>';
        };

        render.protocol = function (row_id, fields) {
            switch (fields.protocol) {
                case 1:
                    return '<span class="badge badge-primary">RDP</span>';
                case 2:
                    return '<span class="badge badge-success">SSH</span>';
                case 3:
                    return '<span class="badge badge-success">TELNET</span>';
                default:
                    return '<span class="badge badge-danger">未知</span>';
            }
        };

        render.make_check_box = function (row_id, fields) {
            return '<span><input type="checkbox" data-check-box="' + fields.id + '" id="host-select-' + row_id + '"></span>';
        };


        render.make_action_btn = function (row_id, fields) {
            var ret = [];
            if (fields.protocol === PROTOCOL_TYPE_RDP) {
                ret.push('<a href="javascript:;" class="btn btn-sm btn-primary" protocol=' + fields.protocol + ' ywl-btn-record="' + fields.ID + '">录像查看</a>&nbsp');
            } else if (fields.protocol === PROTOCOL_TYPE_SSH) {
                if (fields.ret_code === 9999 && fields.cost_time > 0) {
                    ret.push('<a href="javascript:;" class="btn btn-sm btn-primary" protocol=' + fields.protocol + ' ywl-btn-record="' + fields.ID + '">录像查看</a>&nbsp');
                    ret.push('<a href="javascript:;" class="btn btn-sm btn-success" protocol=' + fields.protocol + ' ywl-btn-log="' + fields.ID + '">日志查看</a>&nbsp');
                }
            }

            return ret.join('');
        }
    };
};

ywl.create_table_filter_user_list = function (tbl, selector, on_created) {
    var _tblf_st = {};

    // 此表格绑定的DOM对象的ID，用于JQuery的选择器
    _tblf_st.selector = selector;
    // 此过滤器绑定的表格控件
    _tblf_st._table_ctrl = tbl;
    _tblf_st._table_ctrl.append_filter_ctrl(_tblf_st);

    // 过滤器内容
    _tblf_st.filter_name = 'user_name';
    _tblf_st.filter_default = '全部';
    _tblf_st.filter_value = '';

    _tblf_st.get_filter = function () {
        var _ret = {};
        _ret[_tblf_st.filter_name] = _tblf_st.filter_value;
        return _ret;
    };

    _tblf_st.reset = function (cb_stack, cb_args) {
        if (_tblf_st.filter_value === _tblf_st.filter_default) {
            cb_stack.exec();
            return;
        }

        cb_stack
            .add(function (cb_stack) {
                _tblf_st.filter_value = _tblf_st.filter_default;
                $(_tblf_st.selector + ' button span:first').html(_tblf_st.filter_value);
                cb_stack.exec();
            });
    };

    _tblf_st.init = function (cb_stack) {
        var node = '';
        var user_list = ywl.page_options.user_list;
        node += '<li><a href="javascript:;" ywl-user-id="0">全部</a></li>';
        node += '<li role="separator" class="divider"></li>';
        $.each(user_list, function (i, g) {
            node += '<li><a href="javascript:;" ywl-user-id="' + g.user_id + '">' + g.user_name + '</a></li>';
        });

        _tblf_st.filter_value = _tblf_st.filter_default;
        $(_tblf_st.selector + ' button span:first').html(_tblf_st.filter_value);
        $(_tblf_st.selector + ' ul').empty().append($(node));

        // 点击事件绑定
        $(_tblf_st.selector + ' ul [ywl-user-id]').click(_tblf_st._on_select);

        if (_.isFunction(on_created)) {
            on_created(_tblf_st);
        }

        cb_stack.exec();
    };

    _tblf_st._on_select = function () {
        var user_name = $(this).html();

        var cb_stack = CALLBACK_STACK.create();
        cb_stack
            .add(_tblf_st._table_ctrl.load_data)
            .add(function (cb_stack) {
                _tblf_st.filter_value = user_name;
                $(_tblf_st.selector + ' button span:first').html(user_name);
                cb_stack.exec();
            });
        cb_stack.exec();
    };

    return _tblf_st;
};
