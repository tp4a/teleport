"use strict";

$app.on_init = function (cb_stack) {

    console.log($app.options);

    $app.dom = {
        btn_refresh_user_list: $('#btn-refresh-user-list'),
        btn_create_user: $('#btn-create-user'),
        chkbox_user_list_select_all: $('#table-user-list-select-all'),

        btn_set_role: $('#btn-set-role button'),
        role_list_for_set: $('#btn-set-role ul'),
        btn_lock_user: $('#btn-lock-user'),
        btn_unlock_user: $('#btn-unlock-user'),
        btn_remove_user: $('#btn-remove-user'),

        btn_ldap_import: $('a[data-action="ldap-import"]'),
        btn_ldap_config: $('a[data-action="ldap-config"]'),

        dlg_import_user: $('#dlg-import-user'),
        btn_import_user: $('#btn-import-user'),
        btn_select_file: $('#btn-select-file'),
        btn_do_upload: $('#btn-do-upload-file'),
        upload_file_info: $('#upload-file-info'),
        upload_file_message: $('#upload-file-message')
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
    // 用户列表表格
    //-------------------------------
    var table_users_options = {
        dom_id: 'table-user-list',
        data_source: {
            type: 'ajax-post',
            url: '/user/get-users'
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
                title: "类型",
                key: "type",
                width: 120,
                sort: true,
                header_render: 'filter_type',
                render: 'user_type',
                fields: {user_type: 'type'}
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
            },
            {
                title: '',
                key: 'action',
                sort: false,
                align: 'center',
                width: 70,
                render: 'make_action_btn',
                fields: {id: 'id', state: 'state', user_type: 'type'}
            }
        ],

        // 重载回调函数
        on_header_created: $app.on_table_users_header_created,
        on_render_created: $app.on_table_users_render_created,
        on_cell_created: $app.on_table_users_cell_created
    };

    $app.table_users = $tp.create_table(table_users_options);
    cb_stack
        .add($app.table_users.load_data)
        .add($app.table_users.init);

    //-------------------------------
    // 用户列表相关过滤器
    //-------------------------------
    $tp.create_table_header_filter_search($app.table_users, {
        name: 'search',
        place_holder: '搜索：用户账号/姓名/邮箱/描述/等等...'
    });
    $tp.create_table_header_filter_dropdown($app.table_users, 'type', $app.user_type);
    $tp.create_table_filter_role($app.table_users, $app.role_list);
    $tp.create_table_header_filter_dropdown($app.table_users, 'state', $app.obj_states);
    // 从cookie中读取用户分页限制的选择
    $tp.create_table_paging($app.table_users, 'table-user-list-paging',
        {
            per_page: Cookies.get($app.page_id('user_user') + '_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('user_user') + '_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_users, 'table-user-list-pagination');


    //-------------------------------
    // 对话框
    //-------------------------------
    $app.dlg_edit_user = $app.create_dlg_edit_user();
    cb_stack.add($app.dlg_edit_user.init);
    $app.dlg_user_info = $app.create_dlg_user_info();
    cb_stack.add($app.dlg_user_info.init);
    $app.dlg_reset_password = $app.create_dlg_reset_password();
    cb_stack.add($app.dlg_reset_password.init);

    //-------------------------------
    // 页面控件事件绑定
    //-------------------------------
    $app.dom.btn_create_user.click(function () {
        $app.dlg_edit_user.show_create();
    });
    $app.dom.btn_refresh_user_list.click(function () {
        $app.table_users.load_data();
    });
    $app.dom.btn_select_file.click($app.on_btn_select_file_click);
    $app.dom.btn_do_upload.click($app.on_btn_do_upload_click);
    $app.dom.btn_import_user.click(function () {
        $app.dom.upload_file_info.html('- 尚未选择文件 -');
        $app.dom.btn_do_upload.hide();
        $app.dom.upload_file_message.html('').hide();
        $app.dom.dlg_import_user.modal({backdrop: 'static'});
    });
    $app.dom.chkbox_user_list_select_all.click(function () {
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

    $app.dlg_ldap_config = $app.create_dlg_ldap_config();
    cb_stack.add($app.dlg_ldap_config.init);

    $app.dlg_ldap_import = $app.create_dlg_ldap_import();
    cb_stack.add($app.dlg_ldap_import.init);
    $app.dom.btn_ldap_import.click(function () {
        if (0 === $app.options.sys_cfg.ldap.server.length) {
            $tp.notify_error('LDAP服务尚未设置，请先设置！');
            return;
        }
        $app.dlg_ldap_import.show();
    });
    $app.dom.btn_ldap_config.click(function () {
        $app.dlg_ldap_config.show();
    });

    $app.dlg_ldap_list_attr_result = $app.create_dlg_ldap_list_attr_result();
    cb_stack.add($app.dlg_ldap_list_attr_result.init);

    $app.dlg_ldap_test_result = $app.create_dlg_ldap_test_result();
    cb_stack.add($app.dlg_ldap_test_result.init);


    $app.dom.btn_set_role.click($app.on_btn_set_role_click);
    $app.dom.btn_lock_user.click($app.on_btn_lock_user_click);
    $app.dom.btn_unlock_user.click($app.on_btn_unlock_user_click);
    $app.dom.btn_remove_user.click($app.on_btn_remove_user_click);

    var html = [];
    $.each($app.role_list, function (i, role) {
        html.push('<li><a href="javascript:;" data-tp-selector="' + role.id + '" data-name="' + role.name + '"><i class="fa fa-caret-right fa-fw"></i> ' + role.name + '</a></li>');
    });
    $app.dom.role_list_for_set.append($(html.join('')));
    $app.dom.role_list_for_set.find('a[data-tp-selector]').click(function () {
        var obj = $(this);
        $app.set_selected_to_role(parseInt(obj.attr('data-tp-selector')), obj.attr('data-name'));
    });

    cb_stack.exec();
};

$app.on_table_users_cell_created = function (tbl, row_id, col_key, cell_obj) {
    if (col_key === 'chkbox') {
        cell_obj.find('[data-check-box]').click(function () {
            $app.check_user_list_all_selected();
        });
    }

    else if (col_key === 'action') {
        cell_obj.find('[data-action]').click(function () {
            var user = $app.table_users.get_row(row_id);
            var action = $(this).attr('data-action');
            if (action === 'edit') {
                $app.dlg_edit_user.show_edit(row_id);
            } else if (action === 'reset-password') {
                console.log(user);
                if(user.type === TP_USER_TYPE_LDAP)
                    return;
                $app.dlg_reset_password.show_edit(row_id);
            } else if (action === 'reset-oath-bind') {
                $app._reset_oath_bind(user.id);
            } else if (action === 'lock') {
                if (user.state !== TP_STATE_NORMAL)
                    return;
                $app._lock_users([user.id]);
            } else if (action === 'unlock') {
                if (user.state === TP_STATE_NORMAL)
                    return;
                $app._unlock_users([user.id]);
            } else if (action === 'remove') {
                $app._remove_users([user.id]);
            }
        });
    }
};

$app.check_user_list_all_selected = function (cb_stack) {
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
        $app.dom.chkbox_user_list_select_all.prop('checked', true);
    } else {
        $app.dom.chkbox_user_list_select_all.prop('checked', false);
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

    render.filter_type = function (header, title, col) {
        var _ret = ['<div class="tp-table-filter tp-table-filter-' + col.cell_align + '">'];
        _ret.push('<div class="tp-table-filter-inner">');
        _ret.push('<div class="search-title">' + title + '</div>');

        // 表格内嵌过滤器的DOM实体在这时生成
        var filter_ctrl = header._table_ctrl.get_filter_ctrl('type');
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
        if (fields.id === 1)
            return '';
        return '<span><input type="checkbox" data-check-box="' + fields.id + '" data-row-id="' + row_id + '"></span>';
    };

    render.user_info = function (row_id, fields) {
        var ret = [];
        ret.push('<a href="javascript:;" onclick="$app.show_user_info(' + row_id + ');" class="user-username">');
        ret.push(fields.username);
        ret.push('</a><span class="user-surname">');
        ret.push(fields.surname);
        ret.push('</span>');
        if (fields.email.length > 0)
            ret.push(' <span class="user-email">&lt;' + fields.email + '&gt;</span>');

        return ret.join('');
    };

    render.user_type = function (row_id, fields) {
        if (fields.user_type === 1) {
            return '本地用户';
        } else if (fields.user_type === 2) {
            return 'LDAP';
        } else {
            return '-未知-'
        }
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

    render.make_action_btn = function (row_id, fields) {
        if (fields.id === 1) {
            return '';
        }
        var h = [];
        h.push('<div class="btn-group btn-group-sm">');
        h.push('<button type="button" class="btn btn-no-border dropdown-toggle" data-toggle="dropdown">');
        h.push('<span data-selected-action>操作</span> <i class="fa fa-caret-right"></i></button>');
        h.push('<ul class="dropdown-menu dropdown-menu-right dropdown-menu-sm">');
        h.push('<li><a href="javascript:;" data-action="edit"><i class="fa fa-edit fa-fw"></i> 编辑</a></li>');

        var class_lock = '', class_unlock = '';
        if (fields.state === TP_STATE_NORMAL) {
            class_unlock = ' class="disabled"';
        } else {
            class_lock = ' class="disabled"';
        }

        h.push('<li' + class_lock + '><a href="javascript:;" data-action="lock"><i class="fa fa-lock fa-fw"></i> 禁用</a></li>');
        h.push('<li' + class_unlock + '><a href="javascript:;" data-action="unlock"><i class="fa fa-unlock fa-fw"></i> 解禁</a></li>');

        h.push('<li role="separator" class="divider"></li>');

        var class_user_type = '';
        if (fields.user_type === TP_USER_TYPE_LDAP) {
            class_user_type = ' class="disabled"';
        } else {
            class_user_type = '';
        }
        h.push('<li' + class_user_type +'><a href="javascript:;" data-action="reset-password"><i class="fa fa-street-view fa-fw"></i> 重置密码</a></li>');

        h.push('<li><a href="javascript:;" data-action="reset-oath-bind"><i class="fa fa-street-view fa-fw"></i> 重置身份验证器</a></li>');
        h.push('<li role="separator" class="divider"></li>');
        h.push('<li><a href="javascript:;" data-action="remove"><i class="fa fa-times-circle fa-fw"></i> 删除</a></li>');
        h.push('</ul>');
        h.push('</div>');

        return h.join('');
    };
};

$app.on_table_users_header_created = function (header) {
    $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
        CALLBACK_STACK.create()
            .add(header._table_ctrl.load_data)
            .add(header._table_ctrl.reset_filters)
            .exec();
    });

    // // TODO: 当过滤器不是默认值时，让“重置过滤器按钮”有呼吸效果，避免用户混淆 - 实验性质
    // var t1 = function(){
    //     $app.dom.btn_table_users_reset_filter.fadeTo(1000, 1.0, function(){
    //         $app.dom.btn_table_users_reset_filter.fadeTo(1000, 0.2, t1);
    //     });
    // };
    // $app.dom.btn_table_users_reset_filter.fadeTo(1000, 0.2, t1);

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    header._table_ctrl.get_filter_ctrl('search').on_created();
    header._table_ctrl.get_filter_ctrl('type').on_created();
    header._table_ctrl.get_filter_ctrl('state').on_created();
    header._table_ctrl.get_filter_ctrl('role').on_created();
};

$app.on_btn_select_file_click = function () {

    var html = '<input id="file-selector" type="file" name="csvfile" accept=".csv,text/csv,text/comma-separated-values" class="hidden" value="" style="display: none;"/>';
    $('body').after($(html));
    var btn_file_selector = $("#file-selector");

    btn_file_selector.change(function () {
        $app.dom.upload_file_message.hide();
        // var dom_file_name = $('#upload-file-name');

        console.log(btn_file_selector[0]);
        console.log(btn_file_selector[0].files);

        var file = null;
        if (btn_file_selector[0].files && btn_file_selector[0].files[0]) {
            file = btn_file_selector[0].files[0];
        } else if (btn_file_selector[0].files && btn_file_selector[0].files.item(0)) {
            file = btn_file_selector[0].files.item(0);
        }

        console.log(file);

        if (file === null) {
            $app.dom.upload_file_info.html('请点击图标，选择要上传的文件！');
            return;
        }

        var _ext = file.name.substring(file.name.lastIndexOf('.')).toLocaleLowerCase();
        if (_ext !== '.csv') {
            $app.dom.upload_file_info.html('抱歉，仅支持导入 csv 格式的文件！');
            return;
        }

        if (file.size >= MB * 2) {
            $app.dom.upload_file_info.html('文件太大，超过2MB，无法导入！');
            return;
        }

        var fileInfo = '';
        fileInfo += file.name;
        fileInfo += '<br/>';
        fileInfo += tp_size2str(file.size, 2);
        $app.dom.upload_file_info.html(fileInfo);

        $app.dom.btn_do_upload.show();
    });

    btn_file_selector.click();

};

$app.on_btn_do_upload_click = function () {
    $app.dom.btn_do_upload.hide();

    $app.dom.upload_file_message
        .removeClass('alert-danger alert-info')
        .addClass('alert-info')
        .html('<i class="fa fa-cog fa-spin fa-fw"></i> 正在导入，请稍候...')
        .show();

    var param = {};
    $.ajaxFileUpload({
        url: "/user/upload-import",// 需要链接到服务器地址
        fileElementId: "file-selector", // 文件选择框的id属性
        timeout: 120000,
        secureuri: false,
        dataType: 'text',
        data: param,
        success: function (data) {
            $('#file-selector').remove();

            var ret = JSON.parse(data);

            console.log('import ret', ret);

            if (ret.code === TPE_OK) {
                $app.dom.upload_file_message
                    .removeClass('alert-info')
                    .addClass('alert-success')
                    .html('<i class="far fa-check-square fa-fw"></i> 用户导入成功：' + ret.message);

                $app.table_users.load_data();
            } else {
                var err_msg = ['<i class="far fa-times-circle fa-fw"></i> 用户导入失败：' + ret.message];
                if (!_.isUndefined(ret.data)) {
                    err_msg.push('<div style="max-height:280px;overflow:auto;margin-left:20px;">');
                    var err_lines = [];
                    $.each(ret.data, function (i, item) {
                        err_lines.push('第' + item.line + '行：' + item.error);
                    });
                    err_msg.push(err_lines.join('<br/>'));
                    err_msg.push('</div>');

                    $app.table_users.load_data();
                }

                $app.dom.upload_file_message
                    .removeClass('alert-info')
                    .addClass('alert-danger')
                    .html(err_msg.join(''));
            }
        },
        error: function () {
            $('#file-selector').remove();
            $tp.notify_error('网络故障，批量导入用户失败！');
        }
    });
};

$app.show_user_info = function (row_id) {
    $app.dlg_user_info.show(row_id);
};

$app.get_selected_user = function () {
    var items = [];
    var _objs = $('#' + $app.table_users.dom_id + ' tbody tr td input[data-check-box]');
    $.each(_objs, function (i, _obj) {
        if ($(_obj).is(':checked')) {
            var _row_data = $app.table_users.get_row(_obj);
            items.push(_row_data.id);
        }
    });
    return items;
};

$app.on_btn_set_role_click = function () {
    var items = $app.get_selected_user();
    if (items.length === 0) {
        $tp.notify_error('请先选择用户！');
        return false;
    }
};

$app.set_selected_to_role = function (role_id, role_name) {
    var users = $app.get_selected_user($app.table_users);
    if (users.length === 0) {
        return;
    }

    var _fn_sure = function (cb_stack, cb_args) {
        $tp.ajax_post_json('/user/set-role', {users: users, role_id: role_id},
            function (ret) {
                if (ret.code === TPE_OK) {
                    cb_stack.add($app.check_user_list_all_selected);
                    cb_stack.add($app.table_users.load_data);
                    $tp.notify_success('设置用户角色操作成功！');
                } else {
                    $tp.notify_error('设置用户角色操作失败：' + tp_error_msg(ret.code, ret.message));
                }

                cb_stack.exec();
            },
            function () {
                $tp.notify_error('网络故障，设置用户角色操作失败！');
                cb_stack.exec();
            }
        );
    };

    var cb_stack = CALLBACK_STACK.create();
    $tp.dlg_confirm(cb_stack, {
        msg: '<p>您确定要将选定的 <strong>' + users.length + '个</strong> 用户设置为 <strong>' + role_name + '</strong> 角色吗？</p>',
        fn_yes: _fn_sure
    });

};

$app._reset_oath_bind = function (users) {
    $tp.ajax_post_json('/user/do-unbind-oath', {users: users},
        function (ret) {
            if (ret.code === TPE_OK) {
                $tp.notify_success('重置身份验证器操作成功！');
            } else {
                $tp.notify_error('重置身份验证器操作失败：' + tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $tp.notify_error('网络故障，重置身份验证器操作失败！');
        }
    );
};

$app._lock_users = function (users) {
    $tp.ajax_post_json('/user/update-users', {action: 'lock', users: users},
        function (ret) {
            if (ret.code === TPE_OK) {
                CALLBACK_STACK.create()
                    .add($app.check_user_list_all_selected)
                    .add($app.table_users.load_data)
                    .exec();
                $tp.notify_success('禁用用户账号操作成功！');
            } else {
                $tp.notify_error('禁用用户账号操作失败：' + tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $tp.notify_error('网络故障，禁用用户账号操作失败！');
        }
    );
};

$app.on_btn_lock_user_click = function () {
    var users = $app.get_selected_user($app.table_users);
    if (users.length === 0) {
        $tp.notify_error('请选择要禁用的用户！');
        return;
    }

    $app._lock_hosts(users);
};

$app._unlock_users = function (users) {
    $tp.ajax_post_json('/user/update-users', {action: 'unlock', users: users},
        function (ret) {
            if (ret.code === TPE_OK) {
                CALLBACK_STACK.create()
                    .add($app.check_user_list_all_selected)
                    .add($app.table_users.load_data)
                    .exec();
                $tp.notify_success('解禁用户账号操作成功！');
            } else {
                $tp.notify_error('解禁用户账号操作失败：' + tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $tp.notify_error('网络故障，解禁用户账号操作失败！');
        }
    );
};

$app.on_btn_unlock_user_click = function () {
    var users = $app.get_selected_user($app.table_users);
    if (users.length === 0) {
        $tp.notify_error('请选择要解禁的用户！');
        return;
    }

    $app._unlock_users(users);
};

$app._remove_users = function (users) {
    var _fn_sure = function (cb_stack, cb_args) {
        $tp.ajax_post_json('/user/update-users', {action: 'remove', users: users},
            function (ret) {
                if (ret.code === TPE_OK) {
                    cb_stack.add($app.check_user_list_all_selected);
                    cb_stack.add($app.table_users.load_data);
                    $tp.notify_success('删除用户账号操作成功！');
                } else {
                    $tp.notify_error('删除用户账号操作失败：' + tp_error_msg(ret.code, ret.message));
                }

                cb_stack.exec();
            },
            function () {
                $tp.notify_error('网络故障，删除用户账号操作失败！');
                cb_stack.exec();
            }
        );
    };

    var cb_stack = CALLBACK_STACK.create();
    $tp.dlg_confirm(cb_stack, {
        msg: '<div class="alert alert-danger"><p><strong>注意：删除操作不可恢复！！</strong></p><p>删除用户账号将同时将其从所在用户组中移除，并且删除所有分配给此用户的授权！</p></div><p>如果您希望禁止某个用户登录本系统，可对其进行“禁用”操作！</p><p>您确定要移除所有选定的 <strong>' + users.length + '个</strong> 用户账号吗？</p>',
        fn_yes: _fn_sure
    });
};

$app.on_btn_remove_user_click = function () {
    var users = $app.get_selected_user($app.table_users);
    if (users.length === 0) {
        $tp.notify_error('请选择要删除的用户！');
        return;
    }

    $app._remove_users(users);
};

$app.create_dlg_edit_user = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-edit-user';
    dlg.field_id = -1;  // 用户id（仅编辑模式）
    dlg.field_role = -1;
    dlg.field_auth_type = 0;
    dlg.field_username = '';
    dlg.field_surname = '';
    dlg.field_email = '';
    dlg.field_mobile = '';
    dlg.field_qq = '';
    dlg.field_wechat = '';
    dlg.field_desc = '';

    dlg.dom = {
        dialog: $('#' + dlg.dom_id)
        , dlg_title: $('#' + dlg.dom_id + ' [data-field="dlg-title"]')
        , select_role: $('#edit-user-role')
        , edit_username: $('#edit-user-username')
        , edit_surname: $('#edit-user-surname')
        , edit_email: $('#edit-user-email')
        , edit_mobile: $('#edit-user-mobile')
        , edit_qq: $('#edit-user-qq')
        , edit_wechat: $('#edit-user-wechat')
        , edit_desc: $('#edit-user-desc')
        , msg: $('#edit-user-message')
        , btn_save: $('#btn-edit-user-save')

        , btn_auth_use_sys_config: $('#sec-auth-use-sys-config')
        // , btn_auth_username_password: $('#sec-auth-username-password')
        , btn_auth_username_password_captcha: $('#sec-auth-username-password-captcha')
        // , btn_auth_username_oath: $('#sec-auth-username-oath')
        , btn_auth_username_password_oath: $('#sec-auth-username-password-oath')

    };

    dlg.init = function (cb_stack) {
        // 创建角色选择框
        var _ret = [];
        _ret.push('<button type="button" class="btn btn-sm dropdown-toggle" data-toggle="dropdown">');
        _ret.push('<span data-selected-role>选择角色</span> <i class="fa fa-caret-right"></i></button>');
        _ret.push('<ul class="dropdown-menu dropdown-menu-sm">');
        $.each($app.role_list, function (i, role) {
            _ret.push('<li><a href="javascript:;" data-tp-selector="' + role.id + '"><i class="fa fa-user-circle fa-fw"></i> ' + role.name + '</a></li>');
        });
        _ret.push('</ul>');
        dlg.dom.select_role.after($(_ret.join('')));

        dlg.dom.selected_role = $('#' + dlg.dom_id + ' span[data-selected-role]');

        // 绑定角色选择框事件
        $('#' + dlg.dom_id + ' li a[data-tp-selector]').click(function () {
            var select = parseInt($(this).attr('data-tp-selector'));
            if (dlg.field_role === select)
                return;
            // var name = dlg._id2name(select);

            var name = $app.role_id2name(select);
            if (_.isUndefined(name)) {
                name = '选择角色';
                dlg.field_role = -1;
            } else {
                dlg.field_role = select;
            }

            dlg.dom.selected_role.text(name);
        });

        dlg.dom.btn_auth_use_sys_config.click(function () {
            if ($(this).hasClass('tp-selected')) {
                // $(this).removeClass('tp-selected');
                // dlg.dom.btn_auth_username_password.addClass('tp-editable');
                // dlg.dom.btn_auth_username_password_captcha.addClass('tp-editable');
                // dlg.dom.btn_auth_username_oath.addClass('tp-editable');
                // dlg.dom.btn_auth_username_password_oath.addClass('tp-editable');
                dlg._use_sys_auth_config(false);
            } else {
                dlg._use_sys_auth_config(true);
            }
        });
        // dlg.dom.btn_auth_username_password.click(function () {
        //     dlg._switch_auth($(this));
        // });
        dlg.dom.btn_auth_username_password_captcha.click(function () {
            dlg._switch_auth($(this));
        });
        // dlg.dom.btn_auth_username_oath.click(function () {
        //     dlg._switch_auth($(this));
        // });
        dlg.dom.btn_auth_username_password_oath.click(function () {
            dlg._switch_auth($(this));
        });

        dlg.dom.btn_save.click(dlg.on_save);

        cb_stack.exec();
    };

    dlg._use_sys_auth_config = function (use_sys) {
        if (use_sys) {
            dlg.dom.btn_auth_use_sys_config.addClass('tp-selected');
            // dlg.dom.btn_auth_username_password.removeClass('tp-editable tp-selected');
            dlg.dom.btn_auth_username_password_captcha.removeClass('tp-editable tp-selected');
            // dlg.dom.btn_auth_username_oath.removeClass('tp-editable tp-selected');
            dlg.dom.btn_auth_username_password_oath.removeClass('tp-editable tp-selected');

            var auth_type = $app.options.sys_cfg.login.auth;
            // if (auth_type & TP_LOGIN_AUTH_USERNAME_PASSWORD)
            //     dlg.dom.btn_auth_username_password.addClass('tp-selected');
            if (auth_type & TP_LOGIN_AUTH_USERNAME_PASSWORD_CAPTCHA)
                dlg.dom.btn_auth_username_password_captcha.addClass('tp-selected');
            // if (auth_type & TP_LOGIN_AUTH_USERNAME_OATH)
            //     dlg.dom.btn_auth_username_oath.addClass('tp-selected');
            if (auth_type & TP_LOGIN_AUTH_USERNAME_PASSWORD_OATH)
                dlg.dom.btn_auth_username_password_oath.addClass('tp-selected');
        } else {
            dlg.dom.btn_auth_use_sys_config.removeClass('tp-selected');
            // dlg.dom.btn_auth_username_password.addClass('tp-editable');
            dlg.dom.btn_auth_username_password_captcha.addClass('tp-editable');
            // dlg.dom.btn_auth_username_oath.addClass('tp-editable');
            dlg.dom.btn_auth_username_password_oath.addClass('tp-editable');
        }
    };
    dlg._switch_auth = function (obj) {
        if (!obj.hasClass('tp-editable'))
            return;
        if (obj.hasClass('tp-selected')) {
            obj.removeClass('tp-selected');
        } else {
            obj.addClass('tp-selected');
        }
    };

    dlg.init_fields = function (user) {
        var role_name = '选择角色';
        dlg.field_role = -1;
        dlg.field_auth_type = 0;

        // dlg.dom.btn_auth_use_sys_config.removeClass('tp-selected');
        // dlg.dom.btn_auth_username_password.removeClass('tp-selected');
        // dlg.dom.btn_auth_username_password_captcha.removeClass('tp-selected');
        // dlg.dom.btn_auth_username_oath.removeClass('tp-selected');
        // dlg.dom.btn_auth_username_password_oath.removeClass('tp-selected');

        if (_.isUndefined(user)) {
            dlg.dom.dlg_title.html('创建用户账号');
            dlg.field_id = -1;

            dlg.dom.edit_username.val('');
            dlg.dom.edit_surname.val('');
            dlg.dom.edit_email.val('');
            dlg.dom.edit_mobile.val('');
            dlg.dom.edit_qq.val('');
            dlg.dom.edit_wechat.val('');
            dlg.dom.edit_desc.val('');
        } else {
            dlg.field_id = user.id;
            dlg.field_auth_type = user.auth_type;
            dlg.dom.dlg_title.html('编辑：' + user.surname);

            var _name = $app.role_id2name(user.role_id);
            if (!_.isUndefined(_name)) {
                role_name = _name;
                dlg.field_role = user.role_id;
            }

            dlg.dom.edit_username.val(user.username);
            dlg.dom.edit_surname.val(user.surname);
            dlg.dom.edit_email.val(user.email);
            dlg.dom.edit_mobile.val(user.mobile);
            dlg.dom.edit_qq.val(user.qq);
            dlg.dom.edit_wechat.val(user.wechat);
            dlg.dom.edit_desc.val(user.desc);
        }
        dlg.dom.selected_role.text(role_name);

        if (dlg.field_auth_type === 0) {
            dlg._use_sys_auth_config(true);
        } else {
            dlg._use_sys_auth_config(false);
            var auth_type = dlg.field_auth_type;
            // if (auth_type & TP_LOGIN_AUTH_USERNAME_PASSWORD)
            //     dlg.dom.btn_auth_username_password.addClass('tp-selected');
            if (auth_type & TP_LOGIN_AUTH_USERNAME_PASSWORD_CAPTCHA)
                dlg.dom.btn_auth_username_password_captcha.addClass('tp-selected');
            // if (auth_type & TP_LOGIN_AUTH_USERNAME_OATH)
            //     dlg.dom.btn_auth_username_oath.addClass('tp-selected');
            if (auth_type & TP_LOGIN_AUTH_USERNAME_PASSWORD_OATH)
                dlg.dom.btn_auth_username_password_oath.addClass('tp-selected');
        }
    };

    dlg.show_create = function () {
        dlg.init_fields();
        dlg.dom.dialog.modal({backdrop: 'static'});
    };

    dlg.show_edit = function (row_id) {
        var user = $app.table_users.get_row(row_id);
        console.log(user);
        dlg.init_fields(user);
        dlg.dom.dialog.modal({backdrop: 'static'});
    };

    dlg.check_input = function () {
        dlg.field_username = dlg.dom.edit_username.val();
        dlg.field_surname = dlg.dom.edit_surname.val();
        dlg.field_email = dlg.dom.edit_email.val();
        dlg.field_mobile = dlg.dom.edit_mobile.val();
        dlg.field_qq = dlg.dom.edit_qq.val();
        dlg.field_wechat = dlg.dom.edit_wechat.val();
        dlg.field_desc = dlg.dom.edit_desc.val();

        if (dlg.field_role === -1) {
            $tp.notify_error('请为用户指定一个角色！');
            return false;
        }

        if (dlg.field_username.length === 0) {
            dlg.dom.edit_username.focus();
            $tp.notify_error('请指定 4~32 个英文字母和数字组成的用户账号，注意，账号不区分大小写！');
            return false;
        }

        if (dlg.field_email.length > 0) {
            if (!tp_is_email(dlg.field_email)) {
                dlg.dom.edit_email.focus();
                $tp.notify_error('邮箱地址格式有误哦！');
                return false;
            }
        }

        dlg.field_auth_type = 0;
        if (!dlg.dom.btn_auth_use_sys_config.hasClass('tp-selected')) {
            // if (dlg.dom.btn_auth_username_password.hasClass('tp-selected'))
            //     dlg.field_auth_type |= TP_LOGIN_AUTH_USERNAME_PASSWORD;
            if (dlg.dom.btn_auth_username_password_captcha.hasClass('tp-selected'))
                dlg.field_auth_type |= TP_LOGIN_AUTH_USERNAME_PASSWORD_CAPTCHA;
            // if (dlg.dom.btn_auth_username_oath.hasClass('tp-selected'))
            //     dlg.field_auth_type |= TP_LOGIN_AUTH_USERNAME_OATH;
            if (dlg.dom.btn_auth_username_password_oath.hasClass('tp-selected'))
                dlg.field_auth_type |= TP_LOGIN_AUTH_USERNAME_PASSWORD_OATH;

            if (dlg.field_auth_type === 0) {
                $tp.notify_error('请设置用户登录时身份验证方式！');
                return false;
            }
        }

        return true;
    };

    dlg.on_save = function () {
        if (!dlg.check_input())
            return;

        var action = (dlg.field_id === -1) ? '创建' : '更新';
        var timeout = (dlg.field_id === -1) ? 60000 : 30000;

        // 如果id为-1表示创建，否则表示更新
        $tp.ajax_post_json('/user/update-user', {
                id: dlg.field_id
                , role: dlg.field_role
                , auth_type: dlg.field_auth_type
                , username: dlg.field_username
                , surname: dlg.field_surname
                , email: dlg.field_email
                , mobile: dlg.field_mobile
                , qq: dlg.field_qq
                , wechat: dlg.field_wechat
                , desc: dlg.field_desc
            },
            function (ret) {
                if (ret.code === TPE_OK) {
                    if (ret.message.length > 0)
                        $tp.notify_success(ret.message);
                    else
                        $tp.notify_success('用户账号' + action + '成功！');
                    $app.table_users.load_data();
                    dlg.dom.dialog.modal('hide');
                } else {
                    $tp.notify_error('用户账号' + action + '失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，用户账号' + action + '失败！');
            },
            timeout
        );

    };

    return dlg;
};

$app.create_dlg_user_info = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-user-info';
    dlg.row_id = -1;
    dlg.need_edit = false;

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        dlg_title: $('#' + dlg.dom_id + ' [data-field="dlg-title"]'),
        info: $('#' + dlg.dom_id + ' [data-field="user-info"]'),
        btn_edit: $('#' + dlg.dom_id + ' [data-field="btn-edit"]')
    };

    dlg.init = function (cb_stack) {
        dlg.dom.dialog.on('hidden.bs.modal', function () {
            if (!dlg.need_edit)
                return;
            $app.dlg_edit_user.show_edit(dlg.row_id);
        });

        dlg.dom.btn_edit.click(function () {
            dlg.need_edit = true;
            dlg.dom.dialog.modal('hide');
        });

        cb_stack.exec();
    };

    dlg.show = function (row_id) {
        dlg.row_id = row_id;
        dlg.need_edit = false;

        var _row_data = $app.table_users.get_row(dlg.row_id);

        // 表格加载时，是不会读取用户的 desc 字段的，因此可以判断此用户是否已经读取过详细信息了
        if (_.isUndefined(_row_data.desc)) {
            // 尚未读取，则向服务器要求获取此用户账号的完整信息
            $tp.ajax_post_json('/user/get-user/' + _row_data.id, {},
                function (ret) {
                    if (ret.code === TPE_OK) {
                        $app.table_users.update_row(dlg.row_id, ret.data);
                        dlg.show_info(ret.data);
                    } else {
                        $tp.notify_error('无法获取用户详细信息：' + tp_error_msg(ret.code, ret.message));
                    }
                },
                function () {
                    $tp.notify_error('网络故障，无法获取用户详细信息！');
                }
            );
        } else {
            dlg.show_info(_row_data);
        }
    };

    dlg.show_info = function (user) {
        // 更新对话框中显示的信息
        dlg.dom.dlg_title.html('<i class="far fa-id-card fa-fw"></i> ' + user.surname);

        var info = [];

        var not_set = '<span class="label label-sm label-ignore">未设置</span>';
        var mobile = (user.mobile.length === 0) ? not_set : user.mobile;
        var qq = (user.qq.length === 0) ? not_set : user.qq;
        var wechat = (user.wechat.length === 0) ? not_set : user.wechat;
        var desc = (user.desc.length === 0) ? not_set : user.desc;
        info.push('<tr><td class="key">账号：</td><td class="value">' + user.username + '</td></tr>');
        info.push('<tr><td class="key">姓名：</td><td class="value">' + user.surname + '</td></tr>');
        info.push('<tr><td class="key">邮箱：</td><td class="value">' + user.email + '</td></tr>');
        info.push('<tr><td class="key">电话：</td><td class="value">' + mobile + '</td></tr>');
        info.push('<tr><td class="key">QQ：</td><td class="value">' + qq + '</td></tr>');
        info.push('<tr><td class="key">微信：</td><td class="value">' + wechat + '</td></tr>');
        info.push('<tr><td class="key">描述：</td><td class="value"><div style="max-height:80px;overflow:auto;">' + desc + '</div></td></tr>');

        dlg.dom.info.html($(info.join('')));

        dlg.dom.dialog.modal();
    };

    return dlg;
};

$app.create_dlg_reset_password = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-reset-password';
    dlg.field_id = -1;
    dlg.field_email = '';
    dlg.field_password = '';

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        dlg_title: $('#' + dlg.dom_id + ' [data-field="dlg-title"]'),
        password: $('#' + dlg.dom_id + ' [data-field="password"]'),
        email: $('#' + dlg.dom_id + ' [data-field="email"]'),
        btn_send_reset_email: $('#btn-send-reset-email'),

        can_send_email: $('#can-send-email'),
        cannot_send_email: $('#cannot-send-email'),
        msg_cannot_send_email: $('#msg-cannot-send-email'),

        btn_switch_password: $('#btn-switch-password'),
        btn_switch_password_icon: $('#btn-switch-password i'),
        btn_gen_random_password: $('#btn-gen-random-password'),
        btn_reset_password: $('#btn-reset-password')
    };

    dlg.init = function (cb_stack) {
        dlg.dom.btn_send_reset_email.click(dlg.do_send_reset_email);
        dlg.dom.btn_reset_password.click(dlg.do_reset_password);

        dlg.dom.btn_gen_random_password.click(function () {
            dlg.dom.password.val(tp_gen_password(8));
            dlg.dom.password.attr('type', 'text');
            dlg.dom.btn_switch_password_icon.removeClass('fa-eye').addClass('fa-eye-slash')
        });

        dlg.dom.btn_switch_password.click(function () {
            if ('password' === dlg.dom.password.attr('type')) {
                dlg.dom.password.attr('type', 'text');
                dlg.dom.btn_switch_password_icon.removeClass('fa-eye').addClass('fa-eye-slash')
            } else {
                dlg.dom.password.attr('type', 'password');
                dlg.dom.btn_switch_password_icon.removeClass('fa-eye-slash').addClass('fa-eye')
            }
        });

        if (!$app.options.sys_smtp)
            dlg.dom.msg_cannot_send_email.text('未配置邮件发送服务');

        cb_stack.exec();
    };

    dlg.init_fields = function (user) {
        dlg.field_id = user.id;
        dlg.field_email = user.email;
        dlg.dom.dlg_title.html('密码重置：' + user.surname);

        dlg.dom.password.val('');

        if (!$app.options.sys_smtp || user.email.length === 0) {
            dlg.dom.email.text('');
            dlg.dom.can_send_email.hide();
            dlg.dom.cannot_send_email.show();
        } else {
            dlg.dom.email.text(user.email);
            dlg.dom.can_send_email.show();
            dlg.dom.cannot_send_email.hide();
        }
    };

    dlg.show_edit = function (row_id) {
        var user = $app.table_users.get_row(row_id);
        dlg.init_fields(user);
        dlg.dom.dialog.modal({backdrop: 'static'});
    };

    dlg.do_send_reset_email = function () {
        dlg.dom.btn_send_reset_email.attr('disabled', 'disabled');
        $tp.ajax_post_json('/user/do-reset-password', {
                mode: 1,
                id: dlg.field_id
            },
            function (ret) {
                dlg.dom.btn_send_reset_email.removeAttr('disabled');
                if (ret.code === TPE_OK) {
                    $tp.notify_success('用户密码重置成功！');
                    dlg.dom.dialog.modal('hide');
                } else {
                    $tp.notify_error('用户密码重置失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                dlg.dom.btn_send_reset_email.removeAttr('disabled');
                $tp.notify_error('网络故障，用户密码重置失败！');
            },
            60000
        );

    };

    dlg.do_reset_password = function () {
        dlg.field_password = dlg.dom.password.val();
        if (dlg.field_password.length === 0) {
            dlg.dom.field_password.focus();
            $tp.notify_error('请先填写用户的新密码！');
            return;
        }

        $tp.ajax_post_json('/user/do-reset-password', {
                mode: 2,
                id: dlg.field_id,
                password: dlg.field_password
            },
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('用户密码重置成功！');
                    dlg.dom.dialog.modal('hide');
                } else {
                    $tp.notify_error('用户密码重置失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，用户密码重置失败！');
            }
        );

    };

    return dlg;
};

$app.create_dlg_ldap_config = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-ldap-config';
    dlg.mode = 'set'; // edit or set
    dlg.ldap_config = {
        server: '',
        port: '',
        domain: '',
        admin: '',
        password: '',
        base_dn: '',
        filter: '',
        attr_username: '',
        attr_surname: '',
        attr_email: ''
    };
    // {"server":"192.168.0.101","port":3892,"domain":"apexnas.com","admin":"cn=admin,dc=apexnas,dc=com","password":"Abcd1234","base_dn":"ou=people,dc=apexnas,dc=com","filter":"(&(objectClass=person))","attr_map":"tp.username = uid\ntp.surname = cn111\ntp.email = mail"}

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        server: $('#edit-ldap-server'),
        port: $('#edit-ldap-port'),
        domain: $('#edit-ldap-domain'),
        admin: $('#edit-ldap-admin'),
        password: $('#edit-ldap-password'),
        base_dn: $('#edit-ldap-base-dn'),
        filter: $('#edit-ldap-filter'),
        // attr_map: $('#edit-ldap-attr-map'),
        attr_username: $('#edit-ldap-attr-username'),
        attr_surname: $('#edit-ldap-attr-surname'),
        attr_email: $('#edit-ldap-attr-email'),

        btn_switch_password: $('#btn-switch-ldap-password'),
        btn_switch_password_icon: $('#btn-switch-ldap-password i'),

        btn_list_attr: $('#btn-ldap-config-list-attr'),
        btn_test: $('#btn-ldap-config-test'),
        btn_save: $('#btn-ldap-config-save')
    };

    dlg.init = function (cb_stack) {
        dlg.dom.btn_list_attr.click(dlg.do_list_attr);
        dlg.dom.btn_test.click(dlg.do_test);
        dlg.dom.btn_save.click(dlg.do_save);

        dlg.dom.btn_switch_password.click(function () {
            if ('password' === dlg.dom.password.attr('type')) {
                dlg.dom.password.attr('type', 'text');
                dlg.dom.btn_switch_password_icon.removeClass('fa-eye').addClass('fa-eye-slash')
            } else {
                dlg.dom.password.attr('type', 'password');
                dlg.dom.btn_switch_password_icon.removeClass('fa-eye-slash').addClass('fa-eye')
            }
        });

        cb_stack.exec();
    };

    dlg.init_fields = function () {
        if (0 === $app.options.sys_cfg.ldap.server.length) {
            dlg.mode = 'set';
        } else {
            dlg.ldap_config = $app.options.sys_cfg.ldap;

            dlg.mode = 'edit';
            // dlg.dom.password.val();
            dlg.dom.server.val(dlg.ldap_config.server);
            dlg.dom.port.val(dlg.ldap_config.port);
            dlg.dom.domain.val(dlg.ldap_config.domain);
            dlg.dom.admin.val(dlg.ldap_config.admin);
            dlg.dom.base_dn.val(dlg.ldap_config.base_dn);
            dlg.dom.filter.val(dlg.ldap_config.filter);
            // dlg.dom.attr_map.text(dlg.ldap_config.attr_map);
            dlg.dom.attr_username.val(dlg.ldap_config.attr_username);
            dlg.dom.attr_surname.val(dlg.ldap_config.attr_surname);
            dlg.dom.attr_email.val(dlg.ldap_config.attr_email);
        }
    };

    dlg.show = function () {
        dlg.init_fields();
        dlg.dom.dialog.modal({backdrop: 'static'});
    };

    dlg.check_fields = function () {
        dlg.ldap_config.password = dlg.dom.password.val();
        dlg.ldap_config.server = dlg.dom.server.val();
        dlg.ldap_config.domain = dlg.dom.domain.val();
        dlg.ldap_config.port = parseInt(dlg.dom.port.val());
        dlg.ldap_config.admin = dlg.dom.admin.val();
        dlg.ldap_config.base_dn = dlg.dom.base_dn.val();
        dlg.ldap_config.filter = dlg.dom.filter.val();
        // dlg.ldap_config.attr_map = dlg.dom.attr_map.val();
        dlg.ldap_config.attr_username = dlg.dom.attr_username.val();
        dlg.ldap_config.attr_surname = dlg.dom.attr_surname.val();
        dlg.ldap_config.attr_email = dlg.dom.attr_email.val();

        if (!tp_is_host(dlg.ldap_config.server)) {
            dlg.dom.server.focus();
            $tp.notify_error('请填写LDAP主机地址！');
            return false;
        }
        if (!tp_is_empty_str(dlg.ldap_config.port)) {
            dlg.dom.port.focus();
            $tp.notify_error('请正确填写LDAP主机端口！');
            return false;
        } else {
            var _port = parseInt(dlg.ldap_config.port);
            if (_port <= 0 || _port >= 65535) {
                dlg.dom.port.focus();
                $tp.notify_error('请正确填写LDAP主机端口！');
                return false;
            }
        }
        if (tp_is_empty_str(dlg.ldap_config.domain)) {
            dlg.dom.domain.focus();
            $tp.notify_error('请填写LDAP的域！');
            return false;
        }
        if (tp_is_empty_str(dlg.ldap_config.admin)) {
            dlg.dom.admin.focus();
            $tp.notify_error('请填写LDAP的管理员用户名！');
            return false;
        }

        if (dlg.mode === 'set') {
            if (tp_is_empty_str(dlg.ldap_config.password)) {
                dlg.dom.password.focus();
                $tp.notify_error('请填写LDAP的管理员密码！');
                return false;
            }
        }

        if (tp_is_empty_str(dlg.ldap_config.base_dn)) {
            dlg.dom.base_dn.focus();
            $tp.notify_error('请填写LDAP的用户基准DN！');
            return false;
        }
        if (tp_is_empty_str(dlg.ldap_config.filter)) {
            dlg.dom.filter.focus();
            $tp.notify_error('请填写LDAP的用户过滤器！');
            return false;
        }
        // if (tp_is_empty_str(dlg.ldap_config.attr_map)) {
        //     dlg.dom.attr_map.focus();
        //     $tp.notify_error('请填写LDAP的用户属性与teleport用户属性的映射关系！');
        //     return false;
        // }
        // if (tp_is_empty_str(dlg.ldap_config.attr_username)) {
        //     dlg.dom.attr_username.focus();
        //     $tp.notify_error('请填写映射为teleport登录账号的LDAP用户属性！');
        //     return false;
        // }

        return true;
    };

    dlg.do_list_attr = function () {
        if (!dlg.check_fields())
            return;
        dlg.dom.btn_list_attr.attr('disabled', 'disabled');
        $tp.ajax_post_json('/system/do-ldap-config-list-attr', {
                ldap: dlg.ldap_config
            },
            function (ret) {
                dlg.dom.btn_list_attr.removeAttr('disabled');
                if (ret.code === TPE_OK) {
                    $tp.notify_success('列举LDAP用户属性成功！');
                    console.log(ret.data);
                    $app.dlg_ldap_list_attr_result.show(ret.data.attributes);
                } else {
                    $tp.notify_error('列举LDAP用户属性失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                dlg.dom.btn_list_attr.removeAttr('disabled');
                $tp.notify_error('网络故障，列举LDAP用户属性失败！');
            },
            15000
        );
    };

    dlg.do_test = function () {
        if (!dlg.check_fields())
            return;
        if (tp_is_empty_str(dlg.ldap_config.attr_username)) {
            dlg.dom.attr_username.focus();
            $tp.notify_error('请填写映射为teleport登录账号的LDAP用户属性！');
            return false;
        }
        dlg.dom.btn_test.attr('disabled', 'disabled');
        $tp.ajax_post_json('/system/do-ldap-config-test', {
                ldap: dlg.ldap_config
            },
            function (ret) {
                dlg.dom.btn_test.removeAttr('disabled');
                if (ret.code === TPE_OK) {
                    console.log(ret.data);
                    $tp.notify_success('LDAP连接测试成功！');
                    $app.dlg_ldap_test_result.show(ret.data);
                } else {
                    $tp.notify_error('LDAP连接测试失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                dlg.dom.btn_test.removeAttr('disabled');
                $tp.notify_error('网络故障，LDAP连接测试失败！');
            },
            15000
        );
    };

    dlg.do_save = function () {
        if (!dlg.check_fields())
            return;
        dlg.dom.btn_save.attr('disabled', 'disabled');
        $tp.ajax_post_json('/system/save-cfg', {
                ldap: dlg.ldap_config
            },
            function (ret) {
                dlg.dom.btn_save.removeAttr('disabled');
                if (ret.code === TPE_OK) {
                    $app.options.sys_cfg.ldap = dlg.ldap_config;
                    dlg.dom.dialog.modal('hide');
                    $tp.notify_success('保存LDAP设置成功！');
                } else {
                    $tp.notify_error('保存LDAP设置失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                dlg.dom.btn_save.removeAttr('disabled');
                $tp.notify_error('网络故障，保存LDAP设置失败！');
            },
            15000
        );

    };

    return dlg;
};

$app.create_dlg_ldap_list_attr_result = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-ldap-list-attr-result';

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        msg_ret: $('#msg-ldap-list-attr-ret')
    };

    dlg.init = function (cb_stack) {
        cb_stack.exec();
    };

    dlg.show = function (data) {
        dlg.dom.msg_ret.html('');

        var h = [];

        var attr_name;
        for (attr_name in data) {
            h.push('<div style="white-space:nowrap;"><span class="mono important">' + attr_name + '</span>: ');
            // h.push('<span>'+data[attr_name]+'</span></div>');
            h.push('<span>');
            h.push(data[attr_name].join(', '));
            h.push('</span></div>');
        }

        dlg.dom.msg_ret.html($(h.join('')));

        dlg.dom.dialog.modal();
    };

    return dlg;
};

$app.create_dlg_ldap_test_result = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-ldap-test-result';

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        table: $('#table-ldap-test-ret')
    };

    dlg.init = function (cb_stack) {
        cb_stack.exec();
    };

    dlg.show = function (data) {
        dlg.dom.table.empty();

        var h = [];
        h.push('<thead>');
        h.push('<th style="text-align:left;" class="mono">登录名</th>');
        h.push('<th style="text-align:left;" class="mono">姓名</th>');
        h.push('<th style="text-align:left;" class="mono">邮箱</th>');
        h.push('</thead>');

        var _mktd = function(h, d) {
            if((!_.isUndefined(d)) && !_.isEmpty(d))
                h.push('<td style="text-align:left;" class="mono">'+d+'</td>');
            else
                h.push('<td></td>');
        };

        var dn;
        for (dn in data) {
            h.push('<tr>');
            console.log(data[dn]);
            _mktd(h, data[dn]['username']);
            _mktd(h, data[dn]['surname']);
            _mktd(h, data[dn]['email']);
            h.push('</tr>');
        }

        dlg.dom.table.append($(h.join('')));
        dlg.dom.dialog.modal();
    };

    return dlg;
};

$app.create_dlg_ldap_import = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-ldap-import';

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        table: $('#table-ldap-import'),

        chkbox_user_list_select_all: $('#table-ldap-user-select-all'),

        btn_refresh: $('#btn-ldap-import-refresh'),
        btn_import: $('#btn-ldap-import-import')
    };

    dlg.init = function (cb_stack) {

        //-------------------------------
        // LDAP用户列表表格
        //-------------------------------
        var table_ldap_users_options = {
            dom_id: 'table-ldap-user-list',
            data_source: {
                type: 'none'
            },
            column_default: {sort: false, align: 'left'},
            columns: [
                {
                    // title: '<input type="checkbox" id="user-list-select-all" value="">',
                    title: '',
                    key: 'chkbox',
                    sort: false,
                    width: 36,
                    align: 'center',
                    render: 'make_check_box',
                    fields: {id: 'id'}
                },
                {
                    title: "用户名",
                    key: "username",
                    sort: false
                },
                {
                    title: "姓名",
                    key: "surname",
                    // width: 120,
                    sort: false
                },
                {
                    title: "邮箱",
                    key: "email",
                    // width: 120,
                    sort: false
                }
                // ,
                // {
                //     title: "状态",
                //     key: "bound",
                //     sort: false,
                //     width: 80,
                //     align: 'center',
                //     render: 'ldap_user_state',
                //     fields: {bound: 'bound'}
                // }
            ],

            // 重载回调函数
            on_render_created: dlg.on_table_users_render_created,
            on_cell_created: dlg.on_table_users_cell_created
        };

        $app.table_ldap_users = $tp.create_table(table_ldap_users_options);
        cb_stack
            .add($app.table_ldap_users.init);

        dlg.dom.btn_refresh.click(function () {
            dlg.load_users();
        });

        dlg.dom.chkbox_user_list_select_all.click(function () {
            var _objects = $('#' + $app.table_ldap_users.dom_id + ' tbody').find('[data-check-box]');
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

        // dlg.dom.btn_refresh.click(dlg.load_users);
        dlg.dom.btn_import.click(dlg.do_import);
        cb_stack.exec();
    };

    dlg.get_selected_user = function (tbl) {
        var items = [];
        var _objs = $('#' + tbl.dom_id + ' tbody tr td input[data-check-box]');
        $.each(_objs, function (i, _obj) {
            if ($(_obj).is(':checked')) {
                var _row_data = tbl.get_row(_obj);
                items.push(_row_data.id);
            }
        });
        return items;
    };

    dlg.on_table_users_cell_created = function (tbl, row_id, col_key, cell_obj) {
        if (col_key === 'chkbox') {
            cell_obj.find('[data-check-box]').click(function () {
                dlg.check_user_list_all_selected();
            });
        }
    };

    dlg.on_table_users_render_created = function (render) {

        render.make_check_box = function (row_id, fields) {
            return '<span><input type="checkbox" data-check-box="' + fields.id + '" data-row-id="' + row_id + '"></span>';
        };

        // render.ldap_user_state = function (row_id, fields) {
        //     if (fields.bound) {
        //         return '已导入';
        //     }
        // };
    };

    dlg.check_user_list_all_selected = function (cb_stack) {
        var _all_checked = true;
        var _objs = $('#' + $app.table_ldap_users.dom_id + ' tbody').find('[data-check-box]');
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
            dlg.dom.chkbox_user_list_select_all.prop('checked', true);
        } else {
            dlg.dom.chkbox_user_list_select_all.prop('checked', false);
        }

        if (cb_stack)
            cb_stack.exec();
    };

    dlg.show = function () {
        dlg.load_users();
        dlg.dom.dialog.modal({backdrop: 'static'});
    };

    dlg.load_users = function (cb_stack) {
        cb_stack = cb_stack || CALLBACK_STACK.create();

        dlg.dom.btn_refresh.attr('disabled', 'disabled');
        $tp.ajax_post_json('/system/do-ldap-get-users', {},
            function (ret) {
                dlg.dom.btn_refresh.removeAttr('disabled');
                if (ret.code === TPE_OK) {
                    console.log(ret.data);

                    var _d = [];
                    for (var i = 0; i < ret.data.length; ++i) {
                        _d.push(ret.data[i]);
                    }

                    cb_stack.add(dlg.check_user_list_all_selected);
                    $app.table_ldap_users.set_data(cb_stack, {}, {total: ret.data.length, page_index: 1, data: _d});
                } else {
                    $tp.notify_error('获取LDAP用户列表失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                dlg.dom.btn_refresh.removeAttr('disabled');
                $tp.notify_error('网络故障，获取LDAP用户列表失败！');
            },
            15000
        );
    };

    dlg.do_import = function () {
        var items = dlg.get_selected_user($app.table_ldap_users);
        if (items.length === 0) {
            $tp.notify_error('请选择要导入的账号！');
            return;
        }

        console.log(items);

        dlg.dom.btn_import.attr('disabled', 'disabled');
        $tp.ajax_post_json('/system/do-ldap-import', {ldap_users: items},
            function (ret) {
                dlg.dom.btn_import.removeAttr('disabled');
                if (ret.code === TPE_OK) {
                    CALLBACK_STACK.create()
                        .add($app.table_users.load_data)
                        .add(dlg.check_user_list_all_selected)
                        .add(dlg.load_users)
                        .exec();

                    $tp.notify_success('导入LDAP用户成功！');
                } else {
                    $tp.notify_error('导入LDAP用户失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                dlg.dom.btn_import.removeAttr('disabled');
                $tp.notify_error('网络故障，导入LDAP用户失败！');
            },
            60000
        );
    };

    return dlg;
};
