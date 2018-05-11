"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        btn_refresh_members: $('#btn-refresh-members'),
        btn_add_members: $('#btn-add-members'),
        chkbox_members_select_all: $('#table-members-select-all'),
        btn_remove_members: $('#btn-remove-members'),

        chkbox_users_select_all: $('#table-users-select-all')
    };

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
    // 成员列表表格
    //-------------------------------
    var table_members_options = {
        dom_id: 'table-members',
        data_source: {
            type: 'ajax-post',
            url: '/user/get-users',
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
                title: "用户",
                key: "surname",
                sort: true,
                // width: 240,
                header_render: 'filter_search',
                render: 'user_info',
                fields: {id: 'id', username: 'username', surname: 'surname', email: 'email'}
            },
            {
                title: "角色",
                key: "role_id",
                width: 120,
                sort: true,
                header_render: 'filter_role',
                render: 'role',
                fields: {role_id: 'role_id'}
            },
            {
                title: "状态",
                key: "state",
                sort: true,
                width: 120,
                align: 'center',
                header_render: 'filter_state',
                render: 'user_state',
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
        place_holder: '搜索：用户账号/姓名/邮箱/等等...'
    });
    $tp.create_table_filter_role($app.table_members, $app.role_list);
    $tp.create_table_header_filter_state($app.table_members, 'state', $app.obj_states);
    // 从cookie中读取用户分页限制的选择
    $tp.create_table_paging($app.table_members, 'table-members-paging',
        {
            per_page: Cookies.get($app.page_id('user_group') + '_member_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('user_group') + '_member_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_members, 'table-members-pagination');

    //-------------------------------
    // 选择用户列表表格
    //-------------------------------
    var table_users_options = {
        dom_id: 'table-users',
        data_source: {
            type: 'ajax-post',
            url: '/user/get-users',
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
                title: "用户",
                key: "username",
                sort: true,
                header_render: 'filter_search',
                render: 'user_info',
                fields: {id: 'id', username: 'username', surname: 'surname', email: 'email'}
            },
            {
                title: "角色",
                key: "role_id",
                width: 120,
                sort: true,
                header_render: 'filter_role',
                render: 'role',
                fields: {role_id: 'role_id'}
            },
            {
                title: "状态",
                key: "state",
                sort: true,
                width: 120,
                align: 'center',
                header_render: 'filter_state',
                render: 'user_state',
                fields: {state: 'state'}
            }
        ],

        // 重载回调函数
        on_header_created: $app.on_table_users_header_created,
        on_render_created: $app.on_table_users_render_created,
        on_cell_created: $app.on_table_users_cell_created
    };

    $app.table_users = $tp.create_table(table_users_options);
    cb_stack
        //.add($app.table_users.load_data)
        .add($app.table_users.init);

    //-------------------------------
    // 用户列表相关过滤器
    //-------------------------------
    $tp.create_table_header_filter_search($app.table_users, {
        name: 'search',
        place_holder: '搜索：用户账号/姓名/邮箱/描述/等等...'
    });
    $tp.create_table_filter_role($app.table_users, $app.role_list);
    $tp.create_table_header_filter_state($app.table_users, 'state', $app.obj_states);
    // 从cookie中读取用户分页限制的选择
    $tp.create_table_paging($app.table_users, 'table-users-paging',
        {
            per_page: Cookies.get($app.page_id('user_group') + '_users_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('user_group') + '_users_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_users, 'table-users-pagination');

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

    $app.dom.chkbox_users_select_all.click(function () {
        var _objects = $('#' + $app.table_users.dom_id + ' tbody').find('[data-check-box]');
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

$app.on_table_members_render_created = function (render) {
    render.filter_role = function (header, title, col) {
        var _ret = ['<div class="tp-table-filter tp-table-filter-' + col.cell_align + '">'];
        _ret.push('<div class="tp-table-filter-inner">');
        _ret.push('<div class="search-title">' + title + '</div>');

        // 表格内嵌过滤器的DOM实体在这时生成
        var filter_ctrl = header._table_ctrl.get_filter_ctrl('role');
        _ret.push(filter_ctrl.render());

        _ret.push('</div></div>');

        return _ret.join('');
    };

    render.filter_state = function (header, title, col) {
        var _ret = ['<div class="tp-table-filter tp-table-filter-' + col.cell_align + '">'];
        _ret.push('<div class="tp-table-filter-inner">');
        _ret.push('<div class="search-title">' + title + '</div>');

        // 表格内嵌过滤器的DOM实体在这时生成
        var filter_ctrl = header._table_ctrl.get_filter_ctrl('state');
        _ret.push(filter_ctrl.render());

        _ret.push('</div></div>');

        return _ret.join('');
    };

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

    render.user_info = function (row_id, fields) {
        return '<span class="user-surname">' + fields.surname + '</span><span class="user-account">' + fields.username + ' <span class="user-email">&lt;' + fields.email + '&gt;</span></span>';
    };

    render.role = function (row_id, fields) {
        for (var i = 0; i < $app.role_list.length; ++i) {
            if ($app.role_list[i].id === fields.role_id)
                return $app.role_list[i].name;
        }
        return '<span class="label label-sm label-info"><i class="fa fa-question-circle"></i> 未设置</span>';
    };

    render.user_state = function (row_id, fields) {
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

$app.on_table_members_header_created = function (header) {
    $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
        CALLBACK_STACK.create()
            .add(header._table_ctrl.load_data)
            .add(header._table_ctrl.reset_filters)
            .exec();
    });

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    header._table_ctrl.get_filter_ctrl('search').on_created();
    header._table_ctrl.get_filter_ctrl('role').on_created();
    header._table_ctrl.get_filter_ctrl('state').on_created();
};

$app.on_table_users_cell_created = function (tbl, row_id, col_key, cell_obj) {
    if (col_key === 'chkbox') {
        cell_obj.find('[data-check-box]').click(function () {
            $app.check_users_all_selected();
        });
    }
};

$app.check_users_all_selected = function (cb_stack) {
    var _all_checked = true;
    var _objs = $('#' + $app.table_users.dom_id + ' tbody').find('[data-check-box]');
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
        $app.dom.chkbox_users_select_all.prop('checked', true);
    } else {
        $app.dom.chkbox_users_select_all.prop('checked', false);
    }

    if (cb_stack)
        cb_stack.exec();
};

$app.on_table_users_render_created = function (render) {
    render.filter_role = function (header, title, col) {
        var _ret = ['<div class="tp-table-filter tp-table-filter-' + col.cell_align + '">'];
        _ret.push('<div class="tp-table-filter-inner">');
        _ret.push('<div class="search-title">' + title + '</div>');

        // 表格内嵌过滤器的DOM实体在这时生成
        var filter_ctrl = header._table_ctrl.get_filter_ctrl('role');
        _ret.push(filter_ctrl.render());

        _ret.push('</div></div>');

        return _ret.join('');
    };

    render.filter_state = function (header, title, col) {
        var _ret = ['<div class="tp-table-filter tp-table-filter-' + col.cell_align + '">'];
        _ret.push('<div class="tp-table-filter-inner">');
        _ret.push('<div class="search-title">' + title + '</div>');

        // 表格内嵌过滤器的DOM实体在这时生成
        var filter_ctrl = header._table_ctrl.get_filter_ctrl('state');
        _ret.push(filter_ctrl.render());

        _ret.push('</div></div>');

        return _ret.join('');
    };

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

    render.user_info = function (row_id, fields) {
        return '<span class="user-surname">' + fields.surname + '</span><span class="user-account">' + fields.username + ' <span class="user-email">&lt;' + fields.email + '&gt;</span></span>';
    };

    render.role = function (row_id, fields) {
        for (var i = 0; i < $app.role_list.length; ++i) {
            if ($app.role_list[i].id === fields.role_id)
                return $app.role_list[i].name;
        }
        return '<span class="label label-sm label-info"><i class="fa fa-question-circle"></i> 未设置</span>';
    };

    render.user_state = function (row_id, fields) {
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

$app.on_table_users_header_created = function (header) {
    $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
        CALLBACK_STACK.create()
            .add(header._table_ctrl.load_data)
            .add(header._table_ctrl.reset_filters)
            .exec();
    });

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    header._table_ctrl.get_filter_ctrl('search').on_created();
    header._table_ctrl.get_filter_ctrl('role').on_created();
    header._table_ctrl.get_filter_ctrl('state').on_created();
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
        $tp.notify_error('请选择要移除的成员用户！');
        return;
    }

    var member_list = [];
    $.each(members, function (i, m) {
        member_list.push(m.id);
    });

    var _fn_sure = function (cb_stack, cb_args) {
        $tp.ajax_post_json('/group/remove-members', {gtype: TP_GROUP_USER, gid: $app.options.group_id, members: member_list},
            function (ret) {
                if (ret.code === TPE_OK) {
                    cb_stack
                        .add($app.check_members_all_selected)
                        .add($app.table_members.load_data);
                    $tp.notify_success('移除成员用户操作成功！');
                } else {
                    $tp.notify_error('移除成员用户操作失败：' + tp_error_msg(ret.code, ret.message));
                }

                cb_stack.exec();
            },
            function () {
                $tp.notify_error('网络故障，移除成员用户操作失败！');
                cb_stack.exec();
            }
        );
    };

    var cb_stack = CALLBACK_STACK.create();
    $tp.dlg_confirm(cb_stack, {
        msg: '<div class="alert alert-info">移除用户组内成员不会删除用户账号！</div><p>您确定要移除所有选定的 <strong>' + member_list.length + '个</strong> 成员用户吗？</p>',
        fn_yes: _fn_sure
    });

};

$app.create_dlg_select_members = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-select-members';
    dlg.field_id = -1;  // 用户id
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
        $app.table_users.load_data();
        dlg.dom.dialog.modal();
    };

    dlg.get_selected_users = function () {
        var users = [];
        var _objs = $('#' + dlg.dom_id + ' tbody tr td input[data-check-box]');
        $.each(_objs, function (i, _obj) {
            if ($(_obj).is(':checked')) {
                var _row_data = $app.table_users.get_row(_obj);
                users.push(_row_data.id);
            }
        });

        return users;
    };

    dlg.on_add = function () {
        console.log('---save.');
        // dlg.hide_error();
        // if (!dlg.check_input())
        //     return;
        var users = dlg.get_selected_users();
        console.log('users:', users);

        // 如果id为-1表示创建，否则表示更新
        $tp.ajax_post_json('/group/add-members', {
                gtype: TP_GROUP_USER,
                gid: $app.options.group_id,
                members: users
            },
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('用户成员添加成功！');
                    $app.table_members.load_data();
                    $app.table_users.load_data();
                    // dlg.dom.dialog.modal('hide');
                } else {
                    $tp.notify_error('用户成员添加失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，用户成员添加失败！');
            }
        );

    };

    return dlg;
};
