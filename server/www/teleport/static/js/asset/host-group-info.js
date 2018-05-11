"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        btn_refresh_members: $('#btn-refresh-members'),
        btn_add_members: $('#btn-add-members'),
        chkbox_members_select_all: $('#table-members-select-all'),
        btn_remove_members: $('#btn-remove-members'),

        chkbox_host_select_all: $('#table-host-select-all')
    };

    if ($app.options.group_id !== 0) {
        cb_stack.add($app.create_controls);
    }

    cb_stack.exec();
};

//===================================
// 创建页面控件对象
//===================================
$app.create_controls = function (cb_stack) {

    //-------------------------------
    // 成员列表表格
    //-------------------------------
    var table_members_options = {
        dom_id: 'table-members',
        data_source: {
            type: 'ajax-post',
            url: '/asset/get-hosts',
            restrict: {'group_id': $app.options.group_id}  // 限定仅包含指定的成员
            // exclude: {'user_id':[6]}  // 排除指定成员
        },
        column_default: {sort: false, align: 'left'},
        columns: [
            {
                // title: '<input type="checkbox" id="user-list-select-all" value="">',
                title: '<a href="javascript:;" data-reset-filter><i class="fa fa-undo fa-fw"></i></a>',
                key: 'chkbox',
                sort: false,
                width: 36,
                align: 'center',
                render: 'make_check_box',
                fields: {id: 'id'}
            },
            {
                title: "主机",
                key: "ip",
                sort: true,
                // width: 240,
                header_render: 'filter_search',
                render: 'host_info',
                fields: {id: 'id', ip: 'ip', name: 'name', router_ip: 'router_ip', router_port: 'router_port'}
            },
            {
                title: "系统",
                key: "os_type",
                width: 36,
                align: 'center',
                sort: true,
                render: 'os_type',
                fields: {os_type: 'os_type'}
            },
            {
                title: "资产编号",
                key: "cid",
                sort: true,
                // width: 80,
                // align: 'center',
                //render: 'auth_type',
                fields: {cid: 'cid'}
            },
            {
                title: "状态",
                key: "state",
                sort: true,
                width: 90,
                align: 'center',
                render: 'host_state',
                fields: {state: 'state'}
            }
        ],

        // 重载回调函数
        on_header_created: $app.on_table_members_header_created,
        on_render_created: $app.on_table_members_render_created,
        on_cell_created: $app.on_table_members_cell_created
    };

    $app.table_members = $tp.create_table(table_members_options);
    cb_stack
        .add($app.table_members.load_data)
        .add($app.table_members.init);

    //-------------------------------
    // 成员列表相关过滤器
    //-------------------------------
    $tp.create_table_header_filter_search($app.table_members, {
        name: 'search',
        place_holder: '搜索：主机名称/IP/等等...'
    });
    // 从cookie中读取用户分页限制的选择
    $tp.create_table_paging($app.table_members, 'table-members-paging',
        {
            per_page: Cookies.get($app.page_id('host_group_info') + '_member_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('host_group_info') + '_member_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_members, 'table-members-pagination');

    //-------------------------------
    // 选择成员表格
    //-------------------------------
    var table_host_options = {
        dom_id: 'table-host',
        data_source: {
            type: 'ajax-post',
            url: '/asset/get-hosts',
            exclude: {'group_id': $app.options.group_id}  // 排除指定成员
        },
        column_default: {sort: false, align: 'left'},
        columns: [
            {
                // title: '<input type="checkbox" id="user-list-select-all" value="">',
                title: '<a href="javascript:;" data-reset-filter><i class="fa fa-undo fa-fw"></i></a>',
                key: 'chkbox',
                sort: false,
                width: 36,
                align: 'center',
                render: 'make_check_box',
                fields: {id: 'id'}
            },
            {
                title: "主机",
                key: "ip",
                sort: true,
                // width: 240,
                header_render: 'filter_search',
                render: 'host_info',
                fields: {id: 'id', ip: 'ip', name: 'name', router_ip: 'router_ip', router_port: 'router_port'}
            },
            {
                title: "系统",
                key: "os_type",
                width: 36,
                align: 'center',
                sort: true,
                render: 'os_type',
                fields: {os_type: 'os_type'}
            },
            {
                title: "资产编号",
                key: "cid",
                sort: true,
                // width: 80,
                // align: 'center',
                //render: 'auth_type',
                fields: {cid: 'cid'}
            },
            {
                title: "状态",
                key: "state",
                sort: true,
                width: 90,
                align: 'center',
                render: 'host_state',
                fields: {state: 'state'}
            }
        ],

        // 重载回调函数
        on_header_created: $app.on_table_acc_header_created,
        on_render_created: $app.on_table_acc_render_created,
        on_cell_created: $app.on_table_acc_cell_created
    };

    $app.table_host = $tp.create_table(table_host_options);
    cb_stack
        .add($app.table_host.load_data)
        .add($app.table_host.init);

    //-------------------------------
    // 用户列表相关过滤器
    //-------------------------------
    $tp.create_table_header_filter_search($app.table_host, {
        name: 'search',
        place_holder: '搜索：主机名称/IP/等等...'
    });
    // 从cookie中读取用户分页限制的选择
    $tp.create_table_paging($app.table_host, 'table-host-paging',
        {
            per_page: Cookies.get($app.page_id('host_group_info') + '_sel_member_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('host_group_info') + '_sel_member_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_host, 'table-host-pagination');

    //-------------------------------
    // 对话框
    //-------------------------------
    $app.dlg_select_members = $app.create_dlg_select_members();
    cb_stack.add($app.dlg_select_members.init);

    //-------------------------------
    // 页面控件事件绑定
    //-------------------------------
    $app.dom.btn_add_members.click(function () {
        $app.dlg_select_members.show();
    });
    $app.dom.btn_refresh_members.click(function () {
        $app.table_members.load_data();
    });
    $app.dom.chkbox_members_select_all.click(function () {
        var _objects = $('#' + $app.table_members.dom_id + ' tbody').find('[data-check-box]');
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

    $app.dom.btn_remove_members.click(function () {
        $app.on_btn_remove_members_click();
    });

    $app.dom.chkbox_host_select_all.click(function () {
        var _objects = $('#' + $app.table_host.dom_id + ' tbody').find('[data-check-box]');
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

    cb_stack.exec();
};

$app.on_table_members_cell_created = function (tbl, row_id, col_key, cell_obj) {
    if (col_key === 'chkbox') {
        cell_obj.find('[data-check-box]').click(function () {
            $app.check_members_all_selected();
        });
    }
};

$app.check_members_all_selected = function (cb_stack) {
    var _all_checked = true;
    var _objs = $('#' + $app.table_members.dom_id + ' tbody').find('[data-check-box]');
    $.each(_objs, function (i, _obj) {
        if (!$(_obj).is(':checked')) {
            _all_checked = false;
            return false;
        }
    });

    if (_all_checked) {
        $app.dom.chkbox_members_select_all.prop('checked', true);
    } else {
        $app.dom.chkbox_members_select_all.prop('checked', false);
    }

    if (cb_stack)
        cb_stack.exec();
};

$app._add_common_render = function (render) {
    render.filter_search = function (header, title, col) {
        var _ret = ['<div class="tp-table-filter tp-table-filter-input">'];
        _ret.push('<div class="tp-table-filter-inner">');
        _ret.push('<div class="search-title">' + title + '</div>');

        // 表格内嵌过滤器的DOM实体在这时生成
        var filter_ctrl = header._table_ctrl.get_filter_ctrl('search');
        _ret.push(filter_ctrl.render());

        _ret.push('</div></div>');

        return _ret.join('');
    };

    render.make_check_box = function (row_id, fields) {
        return '<span><input type="checkbox" data-check-box="' + fields.id + '" data-row-id="' + row_id + '"></span>';
    };

    render.host_info = function (row_id, fields) {
        var ret = [];

        var name = fields.name;
        if (name.length === 0)
            name = fields.ip;
        var ip = fields.ip;
        ret.push('<span class="user-surname">' + name + '</span> <span class="mono">[' + ip + ']</span>');
        if (fields.router_ip.length > 0)
            ret.push(' <span class="user-account">由 ' + fields.router_ip + ':' + fields.router_port + ' 路由</span>');

        return ret.join('');
    };

    render.protocol = function (row_id, fields) {
        switch (fields.protocol_type) {
            case TP_PROTOCOL_TYPE_RDP:
                return '<span class="label label-success"><i class="fa fa-desktop fa-fw"></i> RDP</span>';
            case TP_PROTOCOL_TYPE_SSH:
                return '<span class="label label-primary"><i class="far fa-keyboard fa-fw"></i> SSH</span>';
            case TP_PROTOCOL_TYPE_TELNET:
                return '<span class="label label-info"><i class="far fa-keyboard fa-fw"></i> TELNET</span>';
            default:
                return '<span class="label label-ignore"><i class="far fa-question-circle fa-fw"></i> 未设置</span>';
        }
    };

    render.auth_type = function (row_id, fields) {
        switch (fields.auth_type) {
            case TP_AUTH_TYPE_NONE:
                return '<span class="label label-warning">无</span>';
            case TP_AUTH_TYPE_PASSWORD:
                return '<span class="label label-primary">密码</span>';
            case TP_AUTH_TYPE_PRIVATE_KEY:
                return '<span class="label label-success">私钥</span>';
            default:
                return '<span class="label label-ignore">未设置</span>';
        }
    };

    render.host_state = function (row_id, fields) {
        var _style, _state;

        for (var i = 0; i < $app.obj_states.length; ++i) {
            if ($app.obj_states[i].id === fields.state) {
                _style = $app.obj_states[i].style;
                _state = $app.obj_states[i].name;
                break;
            }
        }
        if (i === $app.obj_states.length) {
            _style = 'info';
            _state = '<i class="fa fa-question-circle"></i> 未知';
        }

        return '<span class="label label-sm label-' + _style + '">' + _state + '</span>'
    };
};

$app.on_table_members_render_created = function (render) {
    $app._add_common_render(render);
};

$app.on_table_members_header_created = function (header) {
    $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
        CALLBACK_STACK.create()
            .add(header._table_ctrl.load_data)
            .add(header._table_ctrl.reset_filters)
            .exec();
    });

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    header._table_ctrl.get_filter_ctrl('search').on_created();
    // header._table_ctrl.get_filter_ctrl('role').on_created();
    // header._table_ctrl.get_filter_ctrl('account_state').on_created();
};

$app.on_table_acc_cell_created = function (tbl, row_id, col_key, cell_obj) {
    if (col_key === 'chkbox') {
        cell_obj.find('[data-check-box]').click(function () {
            $app.check_users_all_selected();
        });
    }
};

$app.check_users_all_selected = function (cb_stack) {
    var _all_checked = true;
    var _objs = $('#' + $app.table_host.dom_id + ' tbody').find('[data-check-box]');
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
        $app.dom.chkbox_host_select_all.prop('checked', true);
    } else {
        $app.dom.chkbox_host_select_all.prop('checked', false);
    }

    if (cb_stack)
        cb_stack.exec();
};

$app.on_table_acc_render_created = function (render) {
    // render.filter_role = function (header, title, col) {
    //     var _ret = ['<div class="tp-table-filter tp-table-filter-' + col.cell_align + '">'];
    //     _ret.push('<div class="tp-table-filter-inner">');
    //     _ret.push('<div class="search-title">' + title + '</div>');
    //
    //     // 表格内嵌过滤器的DOM实体在这时生成
    //     var filter_ctrl = header._table_ctrl.get_filter_ctrl('role');
    //     _ret.push(filter_ctrl.render());
    //
    //     _ret.push('</div></div>');
    //
    //     return _ret.join('');
    // };

    // render.filter_user_state = function (header, title, col) {
    //     var _ret = ['<div class="tp-table-filter tp-table-filter-' + col.cell_align + '">'];
    //     _ret.push('<div class="tp-table-filter-inner">');
    //     _ret.push('<div class="search-title">' + title + '</div>');
    //
    //     // 表格内嵌过滤器的DOM实体在这时生成
    //     var filter_ctrl = header._table_ctrl.get_filter_ctrl('user_state');
    //     _ret.push(filter_ctrl.render());
    //
    //     _ret.push('</div></div>');
    //
    //     return _ret.join('');
    // };

    // render.filter_search = function (header, title, col) {
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
    //
    // render.make_check_box = function (row_id, fields) {
    //     return '<span><input type="checkbox" data-check-box="' + fields.id + '" data-row-id="' + row_id + '"></span>';
    // };

    $app._add_common_render(render);
};

$app.on_table_acc_header_created = function (header) {
    $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
        CALLBACK_STACK.create()
            .add(header._table_ctrl.load_data)
            .add(header._table_ctrl.reset_filters)
            .exec();
    });

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    header._table_ctrl.get_filter_ctrl('search').on_created();
};

$app.get_selected_members = function (tbl) {
    var members = [];
    var _objs = $('#' + $app.table_members.dom_id + ' tbody tr td input[data-check-box]');
    $.each(_objs, function (i, _obj) {
        if ($(_obj).is(':checked')) {
            var _row_data = tbl.get_row(_obj);
            members.push(_row_data);
        }
    });

    return members;
};

$app.on_btn_remove_members_click = function () {
    var members = $app.get_selected_members($app.table_members);
    if (members.length === 0) {
        $tp.notify_error('请选择要移除的成员主机！');
        return;
    }

    var member_list = [];
    $.each(members, function (i, m) {
        member_list.push(m.id);
    });

    var _fn_sure = function (cb_stack, cb_args) {
        $tp.ajax_post_json('/group/remove-members', {gtype: TP_GROUP_HOST, gid: $app.options.group_id, members: member_list},
            function (ret) {
                if (ret.code === TPE_OK) {
                    cb_stack
                        .add($app.check_members_all_selected)
                        .add($app.table_members.load_data);
                    $tp.notify_success('移除成员主机操作成功！');
                } else {
                    $tp.notify_error('移除成员主机操作失败：' + tp_error_msg(ret.code, ret.message));
                }

                cb_stack.exec();
            },
            function () {
                $tp.notify_error('网络故障，移除成员主机操作失败！');
                cb_stack.exec();
            }
        );
    };

    var cb_stack = CALLBACK_STACK.create();
    $tp.dlg_confirm(cb_stack, {
        msg: '<div class="alert alert-info">移除组内成员不会删除主机！</div><p>您确定要移除所有选定的 <strong>' + member_list.length + '个</strong> 成员主机吗？</p>',
        fn_yes: _fn_sure
    });

};

$app.create_dlg_select_members = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-select-members';
    dlg.field_id = -1;
    dlg.field_name = '';
    dlg.field_desc = '';

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        btn_add: $('#btn-add-to-group')
    };

    dlg.init = function (cb_stack) {
        dlg.dom.btn_add.click(dlg.on_add);
        cb_stack.exec();
    };

    dlg.show = function () {
        // dlg.init_fields();
        // $app.table_host.load_data();
        dlg.dom.dialog.modal();
    };

    dlg.get_selected_items = function () {
        var items = [];
        var _objs = $('#' + dlg.dom_id + ' tbody tr td input[data-check-box]');
        $.each(_objs, function (i, _obj) {
            if ($(_obj).is(':checked')) {
                var _row_data = $app.table_host.get_row(_obj);
                items.push(_row_data.id);
            }
        });

        return items;
    };

    dlg.on_add = function () {
        var items = dlg.get_selected_items();
        console.log('items:', items);

        // 如果id为-1表示创建，否则表示更新
        $tp.ajax_post_json('/group/add-members', {
                gtype: TP_GROUP_HOST,
                gid: $app.options.group_id,
                members: items
            },
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('主机成员添加成功！');
                    $app.table_members.load_data();
                    $app.table_host.load_data();
                } else {
                    $tp.notify_error('主机成员添加失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，主机成员添加失败！');
            }
        );

    };

    return dlg;
};
