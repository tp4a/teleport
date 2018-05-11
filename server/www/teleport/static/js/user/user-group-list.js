"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        btn_refresh_groups: $('#btn-refresh-groups'),
        btn_create_group: $('#btn-create-group'),
        chkbox_groups_select_all: $('#table-groups-select-all'),

        // btn_lock_group: $('#btn-lock-group'),
        // btn_unlock_group: $('#btn-unlock-group'),
        btn_remove_group: $('#btn-remove-group'),

        chkbox_user_list_select_all: $('#table-user-list-select-all')
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
    // 用户组列表表格
    //-------------------------------
    var table_groups_options = {
        dom_id: 'table-groups',
        data_source: {
            type: 'ajax-post',
            url: '/user/get-groups-with-member'
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
                title: "用户组",
                key: "name",
                sort: true,
                width: 240,
                header_render: 'filter_group_search',
                render: 'group_info',
                fields: {id: 'id', name: 'name', desc: 'desc'}
            },
            {
                title: "成员数",
                key: "member_count",
                width: 20,
                align: 'center',
                // sort: true,
                // header_render: 'filter_role',
                render: 'member_count',
                fields: {member_count: 'member_count'}
            },
            {
                title: "成员用户",
                key: "members",
                // width: 200,
                // sort: true,
                // header_render: 'filter_role',
                render: 'members',
                fields: {id: 'id', member_count: 'member_count', members: 'members'}
            },
            // {
            //     title: "状态",
            //     key: "state",
            //     sort: true,
            //     width: 90,
            //     align: 'center',
            //     header_render: 'filter_state',
            //     render: 'group_state',
            //     fields: {state: 'state'}
            // },
            {
                title: '操作',
                key: 'actions',
                width: 120,
                align: 'center',
                render: 'make_action_btn',
                fields: {id: 'id'}
            }
        ],

        // 重载回调函数
        on_header_created: $app.on_table_groups_header_created,
        on_render_created: $app.on_table_groups_render_created,
        on_cell_created: $app.on_table_groups_cell_created
    };

    $app.table_groups = $tp.create_table(table_groups_options);
    cb_stack
        .add($app.table_groups.load_data)
        .add($app.table_groups.init);

    //-------------------------------
    // 用户组列表相关过滤器
    //-------------------------------
    $app.table_groups_filter_search_user = $tp.create_table_header_filter_search($app.table_groups, {
        name: 'search_group',
        place_holder: '搜索：用户组名称/描述'
    });
    $tp.create_table_header_filter_state($app.table_groups, 'state', $app.obj_states, [TP_STATE_LOCKED]);
    $app.table_groups_paging = $tp.create_table_paging($app.table_groups, 'table-groups-paging',
        {
            per_page: Cookies.get($app.page_id('user_group') + '_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('user_group') + '_per_page', per_page, {expires: 365});
            }
        });
    $app.table_groups_pagination = $tp.create_table_pagination($app.table_groups, 'table-groups-pagination');


    //-------------------------------
    // 对话框
    //-------------------------------
    $app.dlg_edit_group = $app.create_dlg_edit_group();
    cb_stack.add($app.dlg_edit_group.init);

    //-------------------------------
    // 页面控件事件绑定
    //-------------------------------
    $app.dom.btn_create_group.click(function () {
        // $app.dom.dlg_edit_user.modal();
        $app.dlg_edit_group.show_create();
    });
    $app.dom.btn_refresh_groups.click(function () {
        $app.table_groups.load_data();
    });
    $app.dom.chkbox_groups_select_all.click(function () {
        var _objects = $('#' + $app.table_groups.dom_id + ' tbody').find('[data-check-box]');
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

    // $app.dom.btn_lock_group.click(function () {
    //     $app.on_btn_lock_group_click();
    // });
    // $app.dom.btn_unlock_group.click(function () {
    //     $app.on_btn_unlock_group_click();
    // });
    $app.dom.btn_remove_group.click(function () {
        $app.on_btn_remove_group_click();
    });

    cb_stack.exec();
};

$app.on_table_groups_cell_created = function (tbl, row_id, col_key, cell_obj) {
    if (col_key === 'chkbox') {
        cell_obj.find('[data-check-box]').click(function () {
            $app.check_groups_all_selected();
        });
    } else if (col_key === 'actions') {
        var _row_id = row_id;
        cell_obj.find('[data-btn-edit]').click(function () {
            $app.dlg_edit_group.show_edit(_row_id);
        });
        cell_obj.find('[data-btn-remove]').click(function () {
            console.log(_row_id);
            $app.on_btn_remove_group_click(_row_id);
        });
    }
};

$app.check_groups_all_selected = function () {
    var _all_checked = true;
    var _objs = $('#' + $app.table_groups.dom_id + ' tbody').find('[data-check-box]');
    $.each(_objs, function (i, _obj) {
        if (!$(_obj).is(':checked')) {
            _all_checked = false;
            return false;
        }
    });

    if (_all_checked) {
        $app.dom.chkbox_groups_select_all.prop('checked', true);
    } else {
        $app.dom.chkbox_groups_select_all.prop('checked', false);
    }
};

$app.on_table_groups_render_created = function (render) {
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

    render.filter_group_search = function (header, title, col) {
        var _ret = ['<div class="tp-table-filter tp-table-filter-input">'];
        _ret.push('<div class="tp-table-filter-inner">');
        _ret.push('<div class="search-title">' + title + '</div>');

        // 表格内嵌过滤器的DOM实体在这时生成
        var filter_ctrl = header._table_ctrl.get_filter_ctrl('search_group');
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

    render.group_state = function (row_id, fields) {
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

    render.make_check_box = function (row_id, fields) {
        return '<span><input type="checkbox" data-check-box="' + fields.id + '" data-row-id="' + row_id + '"></span>';
    };

    render.group_info = function (row_id, fields) {
        return '<a href="/user/group/' + fields.id + '">' + fields.name + '</a><div class="group-desc">' + fields.desc + '</div>'
            // +'<div class="actions"><btn class="btn btn-sm btn-default" data-btn-edit="' + fields.id + '"><i class="fa fa-edit fa-fw"></i> 编辑</btn></div>'
            ;
    };

    render.members = function (row_id, fields) {
        if (_.isUndefined(fields.members))
            return '';

        console.log(fields.members);

        var ret = [];
        for (var i = 0; i < fields.members.length; ++i) {
            var surname = fields.members[i].surname;
            var email = fields.members[i].email;
            if (email.length !== 0) {
                email = '&lt;' + email + '&gt;';
            }

            var u_info = '账号：' + fields.members[i].username;
            if (email.length > 0)
                u_info += '\n邮箱：' + email;

            if (surname.length === 0) {
                surname = fields.members[i].username;
            }
            ret.push('<div class="user-info-wrap"><div class="user-info" title="' + u_info + '">');
            ret.push(surname);
            ret.push('</div></div>');

            // ret.push('<div class="user-info-wrap"><div class="user-info" title="' + fields.members[i].username + '\n' + fields.members[i].email + '">');
            // // ret.push('<i class="fa fa-vcard-o"></i> ' + fields.members[i].surname);
            // ret.push(fields.members[i].surname);
            // // ret.push('<span class="user-account">'+fields.members[i].account+'</span>');
            // // ret.push('，<span class="user-email">' + fields.members[i].account + '&lt;' + fields.members[i].email + '&gt;</span>');
            // ret.push('</div></div>');
        }

        if (fields.member_count > 5) {
            ret.push('<div class="user-info-wrap"><div class="user-info">');
            ret.push('<a href="/user/group/' + fields.id + '">...更多 <i class="fa fa-arrow-circle-right"></i></a>');
            ret.push('</div></div>');
        }

        return ret.join('');
    };

    render.member_count = function (row_id, fields) {
        return '' + fields.member_count;
    };

    render.make_action_btn = function (row_id, fields) {
        var ret = [];
        ret.push('<div class="btn-group btn-group-sm" role="group">');
        ret.push('<btn class="btn btn-default" data-btn-edit="' + fields.id + '"><i class="fa fa-edit"></i> 编辑</btn>');
        ret.push('<btn class="btn btn-danger" data-btn-remove="' + fields.id + '"><i class="fas fa-trash-alt"></i> 删除</btn>');
        ret.push('</div>');
        return ret.join('');
    };
};

$app.on_table_groups_header_created = function (header) {
    $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
        CALLBACK_STACK.create()
            .add(header._table_ctrl.load_data)
            .add(header._table_ctrl.reset_filters)
            .exec();
    });

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    header._table_ctrl.get_filter_ctrl('search_group').on_created();
    header._table_ctrl.get_filter_ctrl('state').on_created();
};

$app.get_selected_group = function (tbl) {
    var groups = [];
    var _objs = $('#' + $app.table_groups.dom_id + ' tbody tr td input[data-check-box]');
    $.each(_objs, function (i, _obj) {
        if ($(_obj).is(':checked')) {
            var _row_data = tbl.get_row(_obj);
            groups.push(_row_data);
        }
    });
    return groups;
};


// $app.on_btn_lock_group_click = function (_row_id) {
//     var group_list = [];
//
//     if (_.isUndefined(_row_id)) {
//         var groups = $app.get_selected_group($app.table_groups);
//         if (groups.length === 0) {
//             $tp.notify_error('请选择要禁用的分组！');
//             return;
//         }
//
//         $.each(groups, function (i, g) {
//             group_list.push(g.id);
//         });
//     } else {
//         var _row_data = $app.table_groups.get_row(_row_id);
//         group_list.push(_row_data.id);
//     }
//
//     $tp.ajax_post_json('/group/lock', {gtype: TP_GROUP_USER, glist: group_list},
//         function (ret) {
//             if (ret.code === TPE_OK) {
//                 $app.table_groups.load_data();
//                 $tp.notify_success('禁用分组操作成功！');
//             } else {
//                 $tp.notify_error('禁用分组操作失败：' + tp_error_msg(ret.code, ret.message));
//             }
//         },
//         function () {
//             $tp.notify_error('网络故障，禁用分组操作失败！');
//         }
//     );
//
// };
//
// $app.on_btn_unlock_group_click = function (_row_id) {
//     var group_list = [];
//
//     if (_.isUndefined(_row_id)) {
//         var groups = $app.get_selected_group($app.table_groups);
//         if (groups.length === 0) {
//             $tp.notify_error('请选择要解禁的分组！');
//             return;
//         }
//
//         $.each(groups, function (i, g) {
//             group_list.push(g.id);
//         });
//     } else {
//         var _row_data = $app.table_groups.get_row(_row_id);
//         group_list.push(_row_data.id);
//     }
//
//     $tp.ajax_post_json('/group/unlock', {gtype: TP_GROUP_USER, glist: group_list},
//         function (ret) {
//             if (ret.code === TPE_OK) {
//                 $app.table_groups.load_data();
//                 $tp.notify_success('分组解禁操作成功！');
//             } else {
//                 $tp.notify_error('分组解禁操作失败：' + tp_error_msg(ret.code, ret.message));
//             }
//         },
//         function () {
//             $tp.notify_error('网络故障，分组解禁操作失败！');
//         }
//     );
//
// };
//
$app.on_btn_remove_group_click = function (_row_id) {
    var group_list = [];

    if (_.isUndefined(_row_id)) {
        var groups = $app.get_selected_group($app.table_groups);
        if (groups.length === 0) {
            $tp.notify_error('请选择要删除的用户组！');
            return;
        }

        $.each(groups, function (i, g) {
            group_list.push(g.id);
        });
    } else {
        var _row_data = $app.table_groups.get_row(_row_id);
        group_list.push(_row_data.id);
    }

    var _fn_sure = function (cb_stack, cb_args) {
        $tp.ajax_post_json('/group/remove', {gtype: TP_GROUP_USER, glist: group_list},
            function (ret) {
                if (ret.code === TPE_OK) {
                    $app.table_groups.load_data();
                    $tp.notify_success('删除用户组操作成功！');
                } else {
                    $tp.notify_error('删除用户组操作失败：' + tp_error_msg(ret.code, ret.message));
                }

                cb_stack.exec();
            },
            function () {
                $tp.notify_error('网络故障，删除用户组操作失败！');
                cb_stack.exec();
            }
        );
    };

    var cb_stack = CALLBACK_STACK.create();
    var _msg_remove = '您确定要移除此用户组吗？';
    if (group_list.length > 1)
        _msg_remove = '您确定要移除选定的 <strong>' + group_list.length + '个</strong> 用户组吗？';
    $tp.dlg_confirm(cb_stack, {
        msg: '<div class="alert alert-danger"><p><strong>注意：删除操作不可恢复！！</strong></p><p>删除用户组将同时删除所有分配给此用户组的授权！</p></div><div class="alert alert-info">删除用户组不会删除组内的用户账号！</div><p>' + _msg_remove + '</p>',
        fn_yes: _fn_sure
    });

};

$app.create_dlg_edit_group = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-edit-group';
    dlg.field_id = -1;  // 用户id（仅编辑模式）
    dlg.field_name = '';
    dlg.field_desc = '';

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        dlg_title: $('#' + dlg.dom_id + ' [data-field="dlg-title"]'),
        edit_name: $('#edit-group-name'),
        edit_desc: $('#edit-group-desc'),
        msg: $('#edit-group-message'),
        btn_save: $('#btn-edit-group-save')
    };

    dlg.init = function (cb_stack) {
        dlg.dom.btn_save.click(dlg.on_save);

        cb_stack.exec();
    };

    dlg.init_fields = function (g) {
        if (_.isUndefined(g)) {
            dlg.field_id = -1;
            dlg.dom.dlg_title.html('创建用户组');

            dlg.dom.edit_name.val('');
            dlg.dom.edit_desc.val('');
        } else {
            dlg.field_id = g.id;
            dlg.dom.dlg_title.html('编辑：' + g.name);

            dlg.dom.edit_name.val(g.name);
            dlg.dom.edit_desc.val(g.desc);
        }
    };

    dlg.show_create = function () {
        dlg.init_fields();
        dlg.dom.dialog.modal({backdrop: 'static'});
    };

    dlg.show_edit = function (row_id) {
        var g = $app.table_groups.get_row(row_id);
        dlg.init_fields(g);
        dlg.dom.dialog.modal({backdrop: 'static'});
    };

    dlg.show_error = function (error) {
        dlg.dom.msg.removeClass().addClass('alert alert-danger').html(error).show();
    };
    dlg.hide_error = function () {
        dlg.dom.msg.hide();
    };

    dlg.check_input = function () {
        dlg.field_name = dlg.dom.edit_name.val();
        dlg.field_desc = dlg.dom.edit_desc.val();

        if (dlg.field_name.length === 0) {
            dlg.dom.edit_name.focus();
            dlg.show_error('请指定用户组名称！');
            return false;
        }

        return true;
    };

    dlg.on_save = function () {
        console.log('---save.');
        dlg.hide_error();
        if (!dlg.check_input())
            return;

        var action = (dlg.field_id === -1) ? '创建' : '更新';

        // 如果id为-1表示创建，否则表示更新
        $tp.ajax_post_json('/group/update', {
                gtype: TP_GROUP_USER,
                gid: dlg.field_id,
                name: dlg.field_name,
                desc: dlg.field_desc
            },
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('用户组' + action + '成功！');
                    $app.table_groups.load_data();
                    dlg.dom.dialog.modal('hide');
                } else {
                    $tp.notify_error('用户组' + action + '失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，用户组' + action + '失败！');
            }
        );

    };

    return dlg;
};
