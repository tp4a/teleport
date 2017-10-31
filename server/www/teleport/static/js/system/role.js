"use strict";

$app.on_init = function (cb_stack) {
    $app.last_role_id = 0;
    $app.selected_role_id = 0;
    $app.edit_mode = false;

    $app.dom = {
        role_list: $('#role-list'),
        btn_edit_role: $('#btn-edit-role'),
        btn_del_role: $('#btn-delete-role'),
        btn_save_role: $('#btn-save-role'),
        btn_cancel_edit_role: $('#btn-cancel-edit-role'),
        // btn_verify_oath_code: $('#btn-verify-oath-code'),
        // btn_verify_oath_code_and_save: $('#btn-verify-oath-and-save'),
        // btn_modify_password: $('#btn-modify-password'),
        // btn_toggle_oath_download: $('#toggle-oath-download'),
        //
        // oath_app_download_box: $('#oath-app-download-box'),
        //
        // input_role_name: $('#input-role-name'),
        // input_new_password: $('#new-password-1'),
        // input_new_password_confirm: $('#new-password-2'),
        // input_oath_code: $('#oath-code'),
        // input_oath_code_verify: $('#oath-code-verify'),
        //
        // dlg_reset_oath_code: $('#dialog-reset-oath-code'),
        // oath_secret_image: $('#oath-secret-qrcode'),
        // tmp_oath_secret: $('#tmp-oath-secret'),

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

$app.create_controls = function () {
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
            {n: '审计（查看历史会话）', p: TP_PRIVILEGE_AUDIT_OPS_HISTORY},
            {n: '审计授权管理', p: TP_PRIVILEGE_AUDIT_AUZ}]
        },
        {
            t: '系统', i: [
            {n: '角色管理', p: TP_PRIVILEGE_SYS_ROLE},
            {n: '系统配置与维护', p: TP_PRIVILEGE_SYS_CONFIG},
            {n: '历史会话管理', p: TP_PRIVILEGE_SYS_OPS_HISTORY},
            {n: '系统日志管理', p: TP_PRIVILEGE_SYS_LOG}]
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
        var obj = $(this);
        if (obj.hasClass('enabled')) {
            obj.removeClass('enabled');
        } else {
            obj.addClass('enabled');
        }

        if (!$app.edit_mode) {
            $app.edit_mode = true;
            $app.dom.role.save_area.slideDown();
        }
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
};

$app.show_role = function (role_id, edit_mode) {
    var edit = edit_mode || false;
    var role = null;

    if (role_id === 0) {
        role = {id: 0, name: '', privilege: 0};
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
