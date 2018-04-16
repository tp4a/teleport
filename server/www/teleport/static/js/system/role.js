"use strict";

$app.on_init = function (cb_stack) {
    $app.last_role_id = 0; // todo: 使用数组的方式管理选择历史
    $app.selected_role_id = 0;
    $app.edit_mode = false;

    $app.dom = {
        role_list: $('#role-list'),
        area_action: $('#area-action'),
        btn_edit_role: $('#btn-edit-role'),
        btn_remove_role: $('#btn-remove-role'),
        btn_save_role: $('#btn-save-role'),
        btn_cancel_edit_role: $('#btn-cancel-edit-role'),

        role_info: $('#role-info'),
        privilege_list: $('#privilege-list')
    };

    $app.dom.role = {
        label_area: $('#label-role-name-area'),
        input_area: $('#input-role-name-area'),
        save_area: $('#save-area'),
        label_role_name: $app.dom.role_info.find('span[data-role-name]'),
        input_role_name: $('#input-role-name')
    };

    cb_stack
        .add($app.create_controls)
        .add($app.load_role_list);

    cb_stack.exec();
};

$app.create_controls = function (cb_stack) {
    console.log($app.role_list);
    var nodes = [];
    var selected_role_id = 0;
    for (var i = 0; i < $app.role_list.length; ++i) {
        nodes.push('<li data-role-id="' + $app.role_list[i].id + '"');
        if (i === 0) {
            nodes.push(' class="active"');
            selected_role_id = $app.role_list[i].id;
            $app.last_role_id = selected_role_id;
        }
        nodes.push('><i class="fa fa-user-circle fa-fw"></i> ');
        nodes.push($app.role_list[i].name);
        nodes.push('</li>');
    }
    // 增加一个“创建角色”的项
    nodes.push('<li id="btn-create-role" data-role-id="0"><i class="fa fa-plus-circle fa-fw"></i> 创建角色</li>');

    $app.dom.role_list.append($(nodes.join('')));
    $app.dom.btn_create_role = $('#btn-create-role');

    var privileges = [
        {
            t: '资产', i: [
            {n: '主机信息创建/编辑', p: TP_PRIVILEGE_ASSET_CREATE},
            {n: '删除主机信息', p: TP_PRIVILEGE_ASSET_DELETE},
            {n: '主机禁用/解禁', p: TP_PRIVILEGE_ASSET_LOCK},
            {n: '主机分组管理', p: TP_PRIVILEGE_ASSET_GROUP},
            {n: '主机账号管理', p: TP_PRIVILEGE_ACCOUNT},
            {n: '主机账号分组管理', p: TP_PRIVILEGE_ACCOUNT_GROUP}]
        },
        {
            t: '用户', i: [
            {n: '登录WEB系统', p: TP_PRIVILEGE_LOGIN_WEB},
            {n: '用户创建/编辑', p: TP_PRIVILEGE_USER_CREATE},
            {n: '删除用户', p: TP_PRIVILEGE_USER_DELETE},
            {n: '用户禁用/解禁', p: TP_PRIVILEGE_USER_LOCK},
            {n: '用户分组管理', p: TP_PRIVILEGE_USER_GROUP}]
        },
        {
            t: '运维', i: [
            {n: '远程主机运维', p: TP_PRIVILEGE_OPS},
            {n: '运维授权管理', p: TP_PRIVILEGE_OPS_AUZ},
            {n: '查看在线会话', p: TP_PRIVILEGE_SESSION_VIEW},
            {n: '阻断在线会话', p: TP_PRIVILEGE_SESSION_BLOCK}]
        },
        {
            t: '审计', i: [
            {n: '审计（回放操作录像）', p: TP_PRIVILEGE_AUDIT},
            {n: '审计授权管理', p: TP_PRIVILEGE_AUDIT_AUZ}]
        },
        {
            t: '系统', i: [
            {n: '角色管理', p: TP_PRIVILEGE_SYS_ROLE},
            {n: '系统配置与维护', p: TP_PRIVILEGE_SYS_CONFIG},
            // {n: '历史会话管理', p: TP_PRIVILEGE_SYS_OPS_HISTORY},
            {n: '查看系统日志', p: TP_PRIVILEGE_SYS_LOG}]
        }
    ];
    nodes = [];
    $.each(privileges, function (_, ps) {
        nodes.push('<hr/><div class="title">' + ps.t + '</div><ul>');
        $.each(ps.i, function (_, p) {
            nodes.push('<li><span data-privilege="' + p.p + '" class="">' + p.n + '</span></li>');
        });
        nodes.push('</ul>');
    });
    $app.dom.privilege_list.append($(nodes.join('')));

    $app.show_role(selected_role_id, false);

    //===================================================
    // 绑定事件
    //===================================================
    $app.dom.role_list.find('[data-role-id]').click(function () {
        var obj = $(this);
        if (obj.hasClass('active')) {
            return;
        }
        var role_id = parseInt(obj.attr('data-role-id'));
        $app.show_role(role_id, false);
    });
    $app.dom.privilege_list.find('[data-privilege]').click(function () {
        if (!$app.edit_mode)
            return;

        var obj = $(this);
        if (obj.hasClass('enabled')) {
            obj.removeClass('enabled');
        } else {
            obj.addClass('enabled');
        }

        // if (!$app.edit_mode) {
        //     $app.edit_mode = true;
        //     $app.dom.role.save_area.slideDown();
        // }
    });

    $app.dom.btn_edit_role.click(function () {
        $app.show_role($app.selected_role_id, true);
    });

    $app.dom.btn_cancel_edit_role.click(function () {
        if ($app.selected_role_id !== 0)
            $app.show_role($app.selected_role_id, false);
        else
            $app.show_role($app.last_role_id, false);
    });

    $app.dom.btn_save_role.click(function () {
        $app.save_role();
    });

    $app.dom.btn_remove_role.click(function () {
        $app.remove_role();
    });

    cb_stack.exec();
};

$app.show_role = function (role_id, edit_mode) {
    var edit = edit_mode || false;
    var role = null;

    if (role_id === 1 || role_id === 0 || edit_mode) {
        $app.dom.area_action.hide();
    } else {
        $app.dom.area_action.show();
    }

    if (role_id === 1 && edit_mode) {
        $tp.notify_error('禁止修改管理员角色！');
        return;
    }

    if (role_id === 0) {
        role = {id: 0, name: '', privilege: TP_PRIVILEGE_LOGIN_WEB};
        edit = true;
    } else {
        for (var i = 0; i < $app.role_list.length; ++i) {
            if ($app.role_list[i].id === role_id) {
                role = $app.role_list[i];
                break;
            }
        }

        if (_.isNull(role))
            return;
    }

    $app.dom.role_list.find('[data-role-id="' + $app.selected_role_id + '"]').removeClass('active');
    $app.dom.role_list.find('[data-role-id="' + role_id + '"]').addClass('active');

    $app.dom.role.label_role_name.text(role.name);
    $app.dom.role.input_role_name.val(role.name);
    if (edit) {
        $app.edit_mode = true;
        $app.dom.role.label_area.hide();
        $app.dom.role.input_area.show();
        $app.dom.role.input_role_name.focus();
        $app.dom.role.save_area.slideDown();
    } else {
        $app.edit_mode = false;
        $app.dom.role.input_area.hide();
        $app.dom.role.label_area.show();
        $app.dom.role.save_area.slideUp();
    }

    var privilege_objs = $('#role-info').find('[data-privilege]');
    $.each(privilege_objs, function (i, j) {
        var obj = $(j);
        var p = parseInt(obj.attr('data-privilege'));
        obj.removeClass('enabled');
        if (p & role.privilege) {
            obj.addClass('enabled');
        }
    });

    $app.selected_role_id = role_id;
    if (role_id !== 0)
        $app.last_role_id = role_id;
};

$app.save_role = function () {
    var role_name = $app.dom.role.input_role_name.val();
    if (role_name.length === 0) {
        $tp.notify_error('请为此角色设置一个名称！');
        $app.role.dom.input_role_name.focus();
        return;
    }

    var p = 0;
    var privilege_objs = $('#role-info').find('[data-privilege]');
    for (var i = 0; i < privilege_objs.length; ++i) {
        var obj = $(privilege_objs[i]);
        if (obj.hasClass('enabled')) {
            p |= parseInt(obj.attr('data-privilege'));
        }
    }

    if (0 === p) {
        $tp.notify_error('此角色未设定任何权限！');
        return;
    }

    var action = ($app.selected_role_id === 0) ? '添加' : '更新';

    $tp.ajax_post_json('/system/role-update',
        {
            role_id: $app.selected_role_id,
            role_name: role_name,
            privilege: p
        },
        function (ret) {
            if (ret.code === TPE_OK) {
                var role_id = ret.data;
                $tp.notify_success('角色' + action + '成功！');

                if ($app.selected_role_id === 0) {
                    $app.role_list.push({id: role_id, name: role_name, privilege: p});

                    var html = [];
                    html.push('<li data-role-id="' + role_id + '"');
                    html.push('><i class="fa fa-user-circle fa-fw"></i> ');
                    html.push(role_name);
                    html.push('</li>');

                    $app.dom.btn_create_role.before($(html.join('')));


                    $app.dom.role_list.find('[data-role-id="' + role_id + '"]').click(function () {
                        var obj = $(this);
                        if (obj.hasClass('active')) {
                            return;
                        }
                        var r_id = parseInt(obj.attr('data-role-id'));
                        $app.show_role(r_id, false);
                    });

                } else {
                    for (var i = 0; i < $app.role_list.length; ++i) {
                        console.log($app.role_list[i].id, role_id);
                        if ($app.role_list[i].id === role_id) {
                            $app.role_list[i].name = role_name;
                            $app.role_list[i].privilege = p;
                            break;
                        }
                    }
                }

                $app.dom.role_list.find('[data-role-id="' + role_id + '"]').html('<i class="fa fa-user-circle fa-fw"></i> ' + role_name);

                $app.show_role(role_id, false);

            } else {
                $tp.notify_error('角色' + action + '失败：' + tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $tp.notify_error('网路故障，角色' + action + '失败！');
        }
    );

};

$app.remove_role = function () {
    if ($app.selected_role_id === 1) {
        $tp.notify_error('禁止删除管理员角色！');
        return;
    }

    var _fn_sure = function (cb_stack, cb_args) {
        $tp.ajax_post_json('/system/role-remove',
            {
                role_id: $app.selected_role_id
            },
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('角色删除成功！');
                    for (var i = 0; i < $app.role_list; ++i) {
                        if ($app.role_list[i].id === $app.selected_role_id) {
                            delete $app.role_list[i];
                            break;
                        }
                    }

                    $app.dom.role_list.find('[data-role-id="' + $app.selected_role_id + '"]').remove();

                    if ($app.last_role_id === $app.selected_role_id)
                        $app.last_role_id = 1;
                    $app.show_role($app.last_role_id, false);

                    cb_stack.exec();
                } else {
                    $tp.notify_error('角色删除失败：' + tp_error_msg(ret.code, ret.message));
                    cb_stack.exec();
                }
            },
            function () {
                $tp.notify_error('网路故障，角色删除失败！');
            }
        );

    };


    var cb_stack = CALLBACK_STACK.create();
    $tp.dlg_confirm(cb_stack, {
        msg: '<p>删除角色后，属于此角色的用户将没有任何操作权限，直到为用户重新指定角色！</p><p>您确定要将删除此角色吗？</p>',
        fn_yes: _fn_sure
    });

};
