"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        area_operator: $('#area-operator'),
        area_asset: $('#area-asset'),

        btn_refresh_operator: $('#btn-refresh-operator'),
        btn_add_user: $('#btn-add-user'),
        btn_add_user_group: $('#btn-add-user-group'),
        select_all_operator: $('#table-operator-select-all'),
        btn_remove_operator: $('#btn-remove-operator'),

        btn_refresh_asset: $('#btn-refresh-asset'),
        btn_add_acc: $('#btn-add-acc'),
        btn_add_acc_group: $('#btn-add-acc-group'),
        btn_add_host: $('#btn-add-host'),
        btn_add_host_group: $('#btn-add-host-group'),
        select_all_asset: $('#table-asset-select-all'),
        btn_remove_asset: $('#btn-remove-asset'),

        flag_checkboxes: $('#tab-config div.tp-checkbox.tp-editable'),
        // flag_record_allow_replay: $('#record-allow-replay'),
        flag_rdp_allow_clipboard: $('#rdp-allow-clipboard'),
        flag_rdp_allow_disk: $('#rdp-allow-disk'),
        flag_rdp_allow_console: $('#rdp-allow-console'),
        flag_ssh_allow_shell: $('#ssh-allow-shell'),
        flag_ssh_allow_sftp: $('#ssh-allow-sftp'),
        btn_save_flags: $('#btn-save-flags')
    };

    $app.init_flags();

    if ($app.options.policy_id !== 0) {
        window.onresize = $app.on_win_resize;
        cb_stack
            .add($app.sync_height)
            .add($app.create_controls);
    }


    cb_stack.exec();
};

//===================================
// 创建页面控件对象
//===================================
$app.create_controls = function (cb_stack) {

    //-------------------------------
    // 操作者列表表格
    //-------------------------------
    var table_operator_options = {
        dom_id: 'table-operator',
        data_source: {
            type: 'ajax-post',
            url: '/ops/policy/get-operators'
        },
        message_no_data: '还没有授权的操作者...',
        column_default: {sort: false, align: 'left'},
        columns: [
            {
                title: '<a href="javascript:;" data-reset-filter><i class="fa fa-undo fa-fw"></i></a>',
                key: 'chkbox',
                sort: false,
                width: 36,
                align: 'center',
                render: 'make_check_box',
                fields: {id: 'id'}
            },
            {
                title: '类型',
                key: 'rtype',
                sort: true,
                width: 80,
                render: 'ref_type',
                fields: {rtype: 'rtype'}
            },
            {
                title: '操作者',
                key: 'name',
                sort: true,
                header_render: 'filter_search',
                fields: {name: 'name'}
            }
        ],

        // 重载回调函数
        on_header_created: $app.on_table_operator_header_created,
        on_render_created: $app.on_table_operator_render_created,
        on_cell_created: $app.on_table_operator_cell_created
    };

    $app.table_operator = $tp.create_table(table_operator_options);
    cb_stack
        .add($app.table_operator.load_data)
        .add($app.table_operator.init);

    $tp.create_table_header_filter_search($app.table_operator, {
        name: 'search',
        place_holder: '搜索：用户名/用户组名'
    });
    $tp.create_table_filter_fixed_value($app.table_operator, {policy_id: $app.options.policy_id});

    $tp.create_table_paging($app.table_operator, 'table-operator-paging',
        {
            per_page: Cookies.get($app.page_id('ops_auz') + '_operator_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('ops_auz') + '_operator_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_operator, 'table-operator-pagination');

    $app.dom.btn_refresh_operator.click(function () {
        $app.table_operator.load_data();
    });
    $app.dom.select_all_operator.click(function () {
        var _objects = $('#' + $app.table_operator.dom_id + ' tbody').find('[data-check-box]');
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
    $app.dom.btn_remove_operator.click($app.on_btn_remove_operator_click);

    //-------------------------------
    // 资产列表表格
    //-------------------------------
    var table_asset_options = {
        dom_id: 'table-asset',
        data_source: {
            type: 'ajax-post',
            url: '/ops/policy/get-asset'
        },
        message_no_data: '还没有分配被授权访问的资产哦...',
        column_default: {sort: false, align: 'left'},
        columns: [
            {
                title: '<a href="javascript:;" data-reset-filter><i class="fa fa-undo fa-fw"></i></a>',
                key: 'chkbox',
                sort: false,
                width: 36,
                align: 'center',
                render: 'make_check_box',
                fields: {id: 'id'}
            },
            {
                title: '类型',
                key: 'rtype',
                sort: true,
                width: 80,
                render: 'ref_type',
                fields: {rtype: 'rtype'}
            },
            {
                title: '资产',
                key: 'name',
                sort: true,
                header_render: 'filter_search',
                fields: {name: 'name'}
            }
        ],

        // 重载回调函数
        on_header_created: $app.on_table_asset_header_created,
        on_render_created: $app.on_table_asset_render_created,
        on_cell_created: $app.on_table_asset_cell_created
    };

    $app.table_asset = $tp.create_table(table_asset_options);
    cb_stack
        .add($app.table_asset.load_data)
        .add($app.table_asset.init);

    $tp.create_table_header_filter_search($app.table_asset, {
        name: 'search',
        place_holder: '搜索：账号名/账号组名/主机名/主机组名'
    });
    $tp.create_table_filter_fixed_value($app.table_asset, {policy_id: $app.options.policy_id});

    $tp.create_table_paging($app.table_asset, 'table-asset-paging',
        {
            per_page: Cookies.get($app.page_id('ops_auz') + '_asset_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('ops_auz') + '_asset_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_asset, 'table-asset-pagination');

    $app.dom.btn_refresh_asset.click(function () {
        $app.table_asset.load_data();
    });
    $app.dom.select_all_asset.click(function () {
        var _objects = $('#' + $app.table_asset.dom_id + ' tbody').find('[data-check-box]');
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
    $app.dom.btn_remove_asset.click($app.on_btn_remove_asset_click);

    //-------------------------------
    // 选择用户对话框
    //-------------------------------
    var table_sel_user_options = {
        dom_id: 'table-sel-user',
        data_source: {
            type: 'ajax-post',
            url: '/user/get-users',
            exclude: {'ops_policy_id': $app.options.policy_id}
        },
        message_no_data: '所有用户都被授权了哦...',
        column_default: {sort: false, align: 'left'},
        columns: [
            {
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
                render: 'state',
                fields: {state: 'state'}
            }
        ],

        // 重载回调函数
        on_header_created: $app.on_table_sel_user_header_created,
        on_render_created: $app.on_table_sel_user_render_created,
        on_cell_created: $app.on_table_sel_user_cell_created
    };
    $app.table_sel_user = $tp.create_table(table_sel_user_options);
    cb_stack.add($app.table_sel_user.init);

    $tp.create_table_header_filter_search($app.table_sel_user, {
        name: 'search',
        place_holder: '搜索：用户账号/姓名/邮箱/描述/等等...'
    });
    $tp.create_table_filter_role($app.table_sel_user, $app.role_list);
    $tp.create_table_header_filter_state($app.table_sel_user, 'state', $app.obj_states);

    $tp.create_table_paging($app.table_sel_user, 'table-sel-user-paging',
        {
            per_page: Cookies.get($app.page_id('ops_auz_detail') + '_sel_user_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('ops_auz_detail') + '_sel_user_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_sel_user, 'table-sel-user-pagination');

    $app.dlg_sel_user = $app.create_dlg_sel_user();
    cb_stack.add($app.dlg_sel_user.init);
    cb_stack.add($app.load_role_list);


    //-------------------------------
    // 选择用户组对话框
    //-------------------------------
    var table_sel_user_group_options = {
        dom_id: 'table-sel-user-group',
        data_source: {
            type: 'ajax-post',
            url: '/group/get-groups',
            exclude: {'ops_policy_id': {pid: $app.options.policy_id, gtype: TP_GROUP_USER}}  // 排除指定成员
        },
        message_no_data: '所有用户组都被授权了哦...',
        column_default: {sort: false, align: 'left'},
        columns: [
            {
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
                header_render: 'filter_search',
                render: 'name',
                fields: {name: 'name', desc: 'desc'}
            }
        ],

        // 重载回调函数
        on_header_created: $app.on_table_sel_user_group_header_created,
        on_render_created: $app.on_table_sel_user_group_render_created,
        on_cell_created: $app.on_table_sel_user_group_cell_created
    };
    $app.table_sel_user_group = $tp.create_table(table_sel_user_group_options);
    cb_stack.add($app.table_sel_user_group.init);

    $tp.create_table_header_filter_search($app.table_sel_user_group, {
        name: 'search',
        place_holder: '搜索：用户组名称/描述/等等...'
    });
    $tp.create_table_filter_fixed_value($app.table_sel_user_group, {type: TP_GROUP_USER});
    $tp.create_table_paging($app.table_sel_user_group, 'table-sel-user-group-paging',
        {
            per_page: Cookies.get($app.page_id('ops_auz_detail') + '_user_group_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('ops_auz_detail') + '_user_group_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_sel_user_group, 'table-sel-user-group-pagination');

    $app.dlg_sel_user_group = $app.create_dlg_sel_user_group();
    cb_stack.add($app.dlg_sel_user_group.init);


    //-------------------------------
    // 选择账号对话框
    //-------------------------------
    var table_sel_acc_options = {
        dom_id: 'table-sel-acc',
        data_source: {
            type: 'ajax-post',
            url: '/asset/get-accounts',
            exclude: {'ops_policy_id': $app.options.policy_id}  // 排除指定成员
        },
        message_no_data: '所有账号都被授权了哦...',
        column_default: {sort: false, align: 'left'},
        columns: [
            {
                title: '<a href="javascript:;" data-reset-filter><i class="fa fa-undo fa-fw"></i></a>',
                key: 'chkbox',
                sort: false,
                width: 36,
                align: 'center',
                render: 'make_check_box',
                fields: {id: 'id'}
            },
            {
                title: "账号",
                key: "username",
                sort: true,
                header_render: 'filter_search',
                render: 'acc_info',
                fields: {id: 'id', username: 'username', _host: '_host'}
            },
            {
                title: "远程连接协议",
                key: "protocol_type",
                sort: true,
                width: 120,
                align: 'center',
                render: 'protocol',
                fields: {protocol_type: 'protocol_type'}
            },
            {
                title: "认证方式",
                key: "auth_type",
                width: 80,
                align: 'center',
                render: 'auth_type',
                fields: {auth_type: 'auth_type'}
            },
            {
                title: "状态",
                key: "state",
                sort: true,
                width: 80,
                align: 'center',
                render: 'state',
                fields: {state: 'state'}
            }
        ],

        // 重载回调函数
        on_header_created: $app.on_table_sel_acc_header_created,
        on_render_created: $app.on_table_sel_acc_render_created,
        on_cell_created: $app.on_table_sel_acc_cell_created
    };
    $app.table_sel_acc = $tp.create_table(table_sel_acc_options);
    cb_stack.add($app.table_sel_acc.init);

    $tp.create_table_header_filter_search($app.table_sel_acc, {
        name: 'search',
        place_holder: '搜索：账号/主机IP/等等...'
    });
    // 从cookie中读取用户分页限制的选择
    $tp.create_table_paging($app.table_sel_acc, 'table-sel-acc-paging',
        {
            per_page: Cookies.get($app.page_id('ops_auz_detail') + '_sel_acc_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('ops_auz_detail') + '_sel_acc_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_sel_acc, 'table-sel-acc-pagination');

    $app.dlg_sel_acc = $app.create_dlg_sel_acc();
    cb_stack.add($app.dlg_sel_acc.init);


    //-------------------------------
    // 选择账号组对话框
    //-------------------------------
    var table_sel_acc_group_options = {
        dom_id: 'table-sel-acc-group',
        data_source: {
            type: 'ajax-post',
            url: '/group/get-groups',
            exclude: {'ops_policy_id': {pid: $app.options.policy_id, gtype: TP_GROUP_ACCOUNT}}  // 排除指定成员
        },
        message_no_data: '所有账号组都被授权了哦...',
        column_default: {sort: false, align: 'left'},
        columns: [
            {
                title: '<a href="javascript:;" data-reset-filter><i class="fa fa-undo fa-fw"></i></a>',
                key: 'chkbox',
                sort: false,
                width: 36,
                align: 'center',
                render: 'make_check_box',
                fields: {id: 'id'}
            },
            {
                title: "账号组",
                key: "name",
                sort: true,
                header_render: 'filter_search',
                render: 'name',
                fields: {name: 'name', desc: 'desc'}
            }
        ],

        // 重载回调函数
        on_header_created: $app.on_table_sel_acc_group_header_created,
        on_render_created: $app.on_table_sel_acc_group_render_created,
        on_cell_created: $app.on_table_sel_acc_group_cell_created
    };
    $app.table_sel_acc_group = $tp.create_table(table_sel_acc_group_options);
    cb_stack.add($app.table_sel_acc_group.init);

    $tp.create_table_header_filter_search($app.table_sel_acc_group, {
        name: 'search',
        place_holder: '搜索：账号组名称/描述/等等...'
    });
    $tp.create_table_filter_fixed_value($app.table_sel_acc_group, {type: TP_GROUP_ACCOUNT});
    $tp.create_table_paging($app.table_sel_acc_group, 'table-sel-acc-group-paging',
        {
            per_page: Cookies.get($app.page_id('ops_auz_detail') + '_acc_group_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('ops_auz_detail') + '_acc_group_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_sel_acc_group, 'table-sel-acc-group-pagination');

    $app.dlg_sel_acc_group = $app.create_dlg_sel_acc_group();
    cb_stack.add($app.dlg_sel_acc_group.init);


    //-------------------------------
    // 选择主机对话框
    //-------------------------------
    var table_sel_host_options = {
        dom_id: 'table-sel-host',
        data_source: {
            type: 'ajax-post',
            url: '/asset/get-hosts',
            exclude: {'ops_policy_id': $app.options.policy_id}  // 排除指定成员
        },
        message_no_data: '所有主机都被授权了哦...',
        column_default: {sort: false, align: 'left'},
        columns: [
            {
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
                render: 'state',
                fields: {state: 'state'}
            }
        ],

        // 重载回调函数
        on_header_created: $app.on_table_sel_host_header_created,
        on_render_created: $app.on_table_sel_host_render_created,
        on_cell_created: $app.on_table_sel_host_cell_created
    };
    $app.table_sel_host = $tp.create_table(table_sel_host_options);
    cb_stack.add($app.table_sel_host.init);

    $tp.create_table_header_filter_search($app.table_sel_host, {
        name: 'search',
        place_holder: '搜索：主机IP/名称/等等...'
    });
    // 从cookie中读取用户分页限制的选择
    $tp.create_table_paging($app.table_sel_host, 'table-sel-host-paging',
        {
            per_page: Cookies.get($app.page_id('ops_auz_detail') + '_sel_host_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('ops_auz_detail') + '_sel_host_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_sel_host, 'table-sel-host-pagination');

    $app.dlg_sel_host = $app.create_dlg_sel_host();
    cb_stack.add($app.dlg_sel_host.init);


    //-------------------------------
    // 选择主机组对话框
    //-------------------------------
    var table_sel_host_group_options = {
        dom_id: 'table-sel-host-group',
        data_source: {
            type: 'ajax-post',
            url: '/group/get-groups',
            exclude: {'ops_policy_id': {pid: $app.options.policy_id, gtype: TP_GROUP_HOST}}  // 排除指定成员
        },
        message_no_data: '所有主机组都被授权了哦...',
        column_default: {sort: false, align: 'left'},
        columns: [
            {
                title: '<a href="javascript:;" data-reset-filter><i class="fa fa-undo fa-fw"></i></a>',
                key: 'chkbox',
                sort: false,
                width: 36,
                align: 'center',
                render: 'make_check_box',
                fields: {id: 'id'}
            },
            {
                title: "主机组",
                key: "name",
                sort: true,
                header_render: 'filter_search',
                render: 'name',
                fields: {name: 'name', desc: 'desc'}
            }
        ],

        // 重载回调函数
        on_header_created: $app.on_table_sel_host_group_header_created,
        on_render_created: $app.on_table_sel_host_group_render_created,
        on_cell_created: $app.on_table_sel_host_group_cell_created
    };
    $app.table_sel_host_group = $tp.create_table(table_sel_host_group_options);
    cb_stack.add($app.table_sel_host_group.init);

    $tp.create_table_header_filter_search($app.table_sel_host_group, {
        name: 'search',
        place_holder: '搜索：主机组名称/描述/等等...'
    });
    $tp.create_table_filter_fixed_value($app.table_sel_host_group, {type: TP_GROUP_HOST});
    $tp.create_table_paging($app.table_sel_host_group, 'table-sel-host-group-paging',
        {
            per_page: Cookies.get($app.page_id('ops_auz_detail') + '_host_group_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('ops_auz_detail') + '_host_group_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_sel_host_group, 'table-sel-host-group-pagination');

    $app.dlg_sel_host_group = $app.create_dlg_sel_host_group();
    cb_stack.add($app.dlg_sel_host_group.init);


    //-------------------------------
    // 页面控件事件绑定
    //-------------------------------
    $app.dom.btn_add_user.click(function () {
        $app.dlg_sel_user.show();
    });
    $app.dom.btn_add_user_group.click(function () {
        $app.dlg_sel_user_group.show();
    });
    $app.dom.btn_add_acc.click(function () {
        $app.dlg_sel_acc.show();
    });
    $app.dom.btn_add_acc_group.click(function () {
        $app.dlg_sel_acc_group.show();
    });
    $app.dom.btn_add_host.click(function () {
        $app.dlg_sel_host.show();
    });
    $app.dom.btn_add_host_group.click(function () {
        $app.dlg_sel_host_group.show();
    });

    $app.dom.flag_checkboxes.click(function (e) {
        $app.on_click_flag(e);
    });
    $app.dom.btn_save_flags.click(function () {
        $app.on_save_flags();
    });

    cb_stack.exec();
};

// 为保证界面美观，两个表格的高度不一致时，自动调整到一致。
$app.on_win_resize = function () {
    $app.sync_height();
};
$app.sync_height = function (cb_stack) {
    var o_top = $app.dom.area_operator.offset().top;
    var a_top = $app.dom.area_asset.offset().top;

    // 如果两个表格的top不一致，说明是页面宽度缩小到一定程度后，两个表格上下排列了。
    if (o_top !== a_top) {
        $app.dom.area_operator.css({height: 'auto', minHeight: 'auto'});
        $app.dom.area_asset.css({height: 'auto', minHeight: 'auto'});
        return;
    }

    $app.dom.area_operator.css({height: 'auto', minHeight: 'auto'});
    $app.dom.area_asset.css({height: 'auto', minHeight: 'auto'});

    var o_height = $app.dom.area_operator.height();
    var a_height = $app.dom.area_asset.height();

    var h = _.max([o_height, a_height]);

    if (o_height <= h) {
        $app.dom.area_operator.css({minHeight: h});
    } else {
        $app.dom.area_operator.css({height: 'auto', minHeight: 'auto'});
    }
    if (a_height <= h) {
        $app.dom.area_asset.css({minHeight: h});
    } else {
        $app.dom.area_asset.css({height: 'auto', minHeight: 'auto'});
    }

    if (cb_stack)
        cb_stack.exec();
};

//-------------------------------
// 通用渲染器
//-------------------------------
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

    render.make_check_box = function (row_id, fields) {
        return '<span><input type="checkbox" data-check-box="' + fields.id + '" data-row-id="' + row_id + '"></span>';
    };

    render.state = function (row_id, fields) {
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

    render.ref_type = function (row_id, fields) {
        switch (fields.rtype) {
            case TP_USER:
                return '<i class="far fa-user-circle fa-fw"></i> 用户';
            case TP_GROUP_USER:
                return '<i class="far fa-address-book fa-fw"></i> 用户组';
            case TP_ACCOUNT:
                return '<i class="fa fa-user-circle fa-fw"></i> 账号';
            case TP_GROUP_ACCOUNT:
                return '<i class="fa fa-address-book fa-fw"></i> 账号组';
            case TP_HOST:
                return '<i class="fa fa-cube fa-fw"></i> 主机';
            case TP_GROUP_HOST:
                return '<i class="fa fa-cubes fa-fw"></i> 主机组';
            default:
                return '<span class="label label-sm label-ignore">未知</span>'
        }
    };
};

//-------------------------------
// 操作者列表
//-------------------------------

$app.check_operator_all_selected = function (cb_stack) {
    var _all_checked = true;
    var _objs = $('#' + $app.table_operator.dom_id + ' tbody').find('[data-check-box]');
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
        $app.dom.select_all_operator.prop('checked', true);
    } else {
        $app.dom.select_all_operator.prop('checked', false);
    }

    if (cb_stack)
        cb_stack.exec();
};

$app.on_table_operator_cell_created = function (tbl, row_id, col_key, cell_obj) {
    if (col_key === 'chkbox') {
        cell_obj.find('[data-check-box]').click(function () {
            $app.check_operator_all_selected();
        });
    }
};

$app.on_table_operator_render_created = function (render) {

    $app._add_common_render(render);

};

$app.on_table_operator_header_created = function (header) {
    $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
        CALLBACK_STACK.create()
            .add(header._table_ctrl.load_data)
            .add(header._table_ctrl.reset_filters)
            .exec();
    });

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    header._table_ctrl.get_filter_ctrl('search').on_created();
};

$app.get_selected_operator = function (tbl) {
    var items = [];
    var _objs = $('#' + $app.table_operator.dom_id + ' tbody tr td input[data-check-box]');
    $.each(_objs, function (i, _obj) {
        if ($(_obj).is(':checked')) {
            var _row_data = tbl.get_row(_obj);
            items.push(_row_data.id);
        }
    });
    return items;
};

$app.on_btn_remove_operator_click = function () {
    var items = $app.get_selected_operator($app.table_operator);
    if (items.length === 0) {
        $tp.notify_error('请选择要移除的操作者！');
        return;
    }

    var _fn_sure = function (cb_stack) {
        $tp.ajax_post_json('/ops/policy/remove-members', {policy_id: $app.options.policy_id, policy_type: TP_POLICY_OPERATOR, ids: items},
            function (ret) {
                if (ret.code === TPE_OK) {
                    cb_stack
                        .add($app.sync_height)
                        .add($app.check_operator_all_selected)
                        .add($app.check_operator_all_selected)
                        .add($app.table_operator.load_data);
                    $tp.notify_success('移除授权操作者成功！');
                } else {
                    $tp.notify_error('移除授权操作者失败：' + tp_error_msg(ret.code, ret.message));
                }

                cb_stack.exec();
            },
            function () {
                $tp.notify_error('网络故障，移除授权操作者失败！');
                cb_stack.exec();
            }
        );
    };

    var cb_stack = CALLBACK_STACK.create();
    $tp.dlg_confirm(cb_stack, {
        msg: '<div class="alert alert-danger"><p><strong>注意：移除操作不可恢复！！</strong></p><p>您确定要移除选定的' + items.length + '个授权操作者吗？</p>',
        fn_yes: _fn_sure
    });

};


//-------------------------------
// 资产列表
//-------------------------------

$app.check_asset_all_selected = function (cb_stack) {
    var _all_checked = true;
    var _objs = $('#' + $app.table_asset.dom_id + ' tbody').find('[data-check-box]');
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
        $app.dom.select_all_asset.prop('checked', true);
    } else {
        $app.dom.select_all_asset.prop('checked', false);
    }

    if (cb_stack)
        cb_stack.exec();
};

$app.on_table_asset_cell_created = function (tbl, row_id, col_key, cell_obj) {
    if (col_key === 'chkbox') {
        cell_obj.find('[data-check-box]').click(function () {
            $app.check_asset_all_selected();
        });
    }
};

$app.on_table_asset_render_created = function (render) {
    $app._add_common_render(render);
};

$app.on_table_asset_header_created = function (header) {
    $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
        CALLBACK_STACK.create()
            .add(header._table_ctrl.load_data)
            .add(header._table_ctrl.reset_filters)
            .exec();
    });

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    header._table_ctrl.get_filter_ctrl('search').on_created();
};

$app.get_selected_asset = function (tbl) {
    var items = [];
    var _objs = $('#' + $app.table_asset.dom_id + ' tbody tr td input[data-check-box]');
    $.each(_objs, function (i, _obj) {
        if ($(_obj).is(':checked')) {
            var _row_data = tbl.get_row(_obj);
            items.push(_row_data.id);
        }
    });
    return items;
};

$app.on_btn_remove_asset_click = function () {
    var items = $app.get_selected_asset($app.table_asset);
    if (items.length === 0) {
        $tp.notify_error('请选择要移除的被授权资产！');
        return;
    }

    var _fn_sure = function (cb_stack) {
        $tp.ajax_post_json('/ops/policy/remove-members', {policy_id: $app.options.policy_id, policy_type: TP_POLICY_ASSET, ids: items},
            function (ret) {
                if (ret.code === TPE_OK) {
                    cb_stack
                        .add($app.sync_height)
                        .add($app.check_asset_all_selected)
                        .add($app.check_asset_all_selected)
                        .add($app.table_asset.load_data);
                    $tp.notify_success('移除被授权资产成功！');
                } else {
                    $tp.notify_error('移除被授权资产失败：' + tp_error_msg(ret.code, ret.message));
                }

                cb_stack.exec();
            },
            function () {
                $tp.notify_error('网络故障，移除被授权资产失败！');
                cb_stack.exec();
            }
        );
    };

    var cb_stack = CALLBACK_STACK.create();
    $tp.dlg_confirm(cb_stack, {
        msg: '<div class="alert alert-danger"><p><strong>注意：移除操作不可恢复！！</strong></p><p>您确定要移除选定的' + items.length + '个被授权资产吗？</p>',
        fn_yes: _fn_sure
    });

};


//-------------------------------
// 选择用户对话框
//-------------------------------

$app.on_table_sel_user_cell_created = function (tbl, row_id, col_key, cell_obj) {
    if (col_key === 'chkbox') {
        cell_obj.find('[data-check-box]').click(function () {
            $app.dlg_sel_user.check_all_selected();
        });
    }
};

$app.on_table_sel_user_render_created = function (render) {
    $app._add_common_render(render);

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

    render.user_info = function (row_id, fields) {
        var ret = [];
        if(fields.surname.length > 0) {
            ret.push('<span class="field-name">' + fields.surname + '</span>');
        }
        else {
            ret.push('<span class="field-name">' + fields.username + '</span>');
        }
        ret.push('<span class="field-desc mono">');
        ret.push(fields.username);
        if (fields.email.length > 0)
            ret.push(' &lt;' + fields.email + '&gt;');
        ret.push('</span>');
        return ret.join('')
    };

    render.role = function (row_id, fields) {
        for (var i = 0; i < $app.role_list.length; ++i) {
            if ($app.role_list[i].id === fields.role_id)
                return $app.role_list[i].name;
        }
        return '<span class="label label-sm label-info"><i class="fa fa-question-circle"></i> 未设置</span>';
    };
};

$app.on_table_sel_user_header_created = function (header) {
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

$app.create_dlg_sel_user = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-sel-user';
    dlg.field_id = -1;
    dlg.field_name = '';
    dlg.field_desc = '';

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        btn_sel_all: $('#' + dlg.dom_id + ' input[data-action="sel-all"]'),
        btn_add: $('#' + dlg.dom_id + ' button[data-action="use-selected"]')
    };

    dlg.init = function (cb_stack) {
        dlg.dom.btn_add.click(dlg.on_add);
        dlg.dom.btn_sel_all.click(dlg.on_sel_all);
        cb_stack.exec();
    };

    dlg.show = function () {
        $app.table_sel_user.load_data();
        dlg.dom.dialog.modal();
    };

    dlg.on_sel_all = function () {
        var _objects = $('#' + $app.table_sel_user.dom_id + ' tbody').find('[data-check-box]');
        if ($(this).is(':checked')) {
            $.each(_objects, function (i, _obj) {
                $(_obj).prop('checked', true);
            });
        } else {
            $.each(_objects, function (i, _obj) {
                $(_obj).prop('checked', false);
            });
        }
    };

    dlg.check_all_selected = function (cb_stack) {
        var _all_checked = true;
        var _objs = $('#' + dlg.dom_id + ' tbody').find('[data-check-box]');
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
            dlg.dom.btn_sel_all.prop('checked', true);
        } else {
            dlg.dom.btn_sel_all.prop('checked', false);
        }
        if (cb_stack)
            cb_stack.exec();
    };

    dlg.get_selected_items = function () {
        var items = [];
        var _objs = $('#' + dlg.dom_id + ' tbody tr td input[data-check-box]');
        $.each(_objs, function (i, _obj) {
            if ($(_obj).is(':checked')) {
                var _row_data = $app.table_sel_user.get_row(_obj);

                var name = _row_data.username;
                if (_row_data.surname.length > 0 && _row_data.surname !== name)
                    name += '（' + _row_data.surname + '）';

                items.push({id: _row_data.id, name: name});
            }
        });

        return items;
    };

    dlg.on_add = function () {
        var items = dlg.get_selected_items();
        if(items.length === 0) {
            $tp.notify_error('请先选择要添加的操作者！');
            return;
        }

        $tp.ajax_post_json('/ops/policy/add-members', {
                policy_id: $app.options.policy_id,
                type: TP_POLICY_OPERATOR, // 授权操作者
                rtype: TP_USER,  // 用户
                members: items
            },
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('授权操作者添加成功！');
                    CALLBACK_STACK.create()
                        .add($app.sync_height)
                        .add(dlg.check_all_selected)
                        .add($app.table_operator.load_data)
                        .add($app.table_sel_user.load_data)
                        .exec();
                } else {
                    $tp.notify_error('授权操作者添加失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，授权操作者添加失败！');
            }
        );

    };

    return dlg;
};


//-------------------------------
// 选择用户组对话框
//-------------------------------

$app.on_table_sel_user_group_cell_created = function (tbl, row_id, col_key, cell_obj) {
    if (col_key === 'chkbox') {
        cell_obj.find('[data-check-box]').click(function () {
            $app.dlg_sel_user_group.check_all_selected();
        });
    }
};

$app.on_table_sel_user_group_render_created = function (render) {

    $app._add_common_render(render);

    render.name = function (row_id, fields) {
        return '<span class="field-name">' + fields.name + '</span><span class="field-desc">' + fields.desc + '</span>';
    };
};

$app.on_table_sel_user_group_header_created = function (header) {
    $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
        CALLBACK_STACK.create()
            .add(header._table_ctrl.load_data)
            .add(header._table_ctrl.reset_filters)
            .exec();
    });

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    header._table_ctrl.get_filter_ctrl('search').on_created();
};

$app.create_dlg_sel_user_group = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-sel-user-group';
    dlg.field_id = -1;  // 用户id
    dlg.field_name = '';
    dlg.field_desc = '';

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        btn_sel_all: $('#' + dlg.dom_id + ' input[data-action="sel-all"]'),
        btn_add: $('#' + dlg.dom_id + ' button[data-action="use-selected"]')
    };

    dlg.init = function (cb_stack) {
        dlg.dom.btn_add.click(dlg.on_add);
        dlg.dom.btn_sel_all.click(dlg.on_sel_all);
        cb_stack.exec();
    };

    dlg.show = function () {
        $app.table_sel_user_group.load_data();
        dlg.dom.dialog.modal();
    };

    dlg.on_sel_all = function () {
        var _objects = $('#' + $app.table_sel_user_group.dom_id + ' tbody').find('[data-check-box]');
        if ($(this).is(':checked')) {
            $.each(_objects, function (i, _obj) {
                $(_obj).prop('checked', true);
            });
        } else {
            $.each(_objects, function (i, _obj) {
                $(_obj).prop('checked', false);
            });
        }
    };

    dlg.check_all_selected = function (cb_stack) {
        var _all_checked = true;
        var _objs = $('#' + dlg.dom_id + ' tbody').find('[data-check-box]');
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
            dlg.dom.btn_sel_all.prop('checked', true);
        } else {
            dlg.dom.btn_sel_all.prop('checked', false);
        }
        if (cb_stack)
            cb_stack.exec();
    };

    dlg.get_selected_items = function () {
        var items = [];
        var _objs = $('#' + dlg.dom_id + ' tbody tr td input[data-check-box]');
        $.each(_objs, function (i, _obj) {
            if ($(_obj).is(':checked')) {
                var _row_data = $app.table_sel_user_group.get_row(_obj);
                items.push({id: _row_data.id, name: _row_data.name});
            }
        });

        return items;
    };

    dlg.on_add = function () {
        var items = dlg.get_selected_items();
        if(items.length === 0) {
            $tp.notify_error('请先选择要添加的操作者！');
            return;
        }

        $tp.ajax_post_json('/ops/policy/add-members', {
                policy_id: $app.options.policy_id,
                type: TP_POLICY_OPERATOR, // 授权操作者
                rtype: TP_GROUP_USER,  // 用户组
                members: items
            },
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('授权操作者添加成功！');
                    CALLBACK_STACK.create()
                        .add($app.sync_height)
                        .add(dlg.check_all_selected)
                        .add($app.table_operator.load_data)
                        .add($app.table_sel_user_group.load_data)
                        .exec();
                } else {
                    $tp.notify_error('授权操作者添加失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，授权操作者添加失败！');
            }
        );

    };

    return dlg;
};

//-------------------------------
// 选择账号对话框
//-------------------------------

$app.on_table_sel_acc_cell_created = function (tbl, row_id, col_key, cell_obj) {
    if (col_key === 'chkbox') {
        cell_obj.find('[data-check-box]').click(function () {
            $app.dlg_sel_acc.check_all_selected();
        });
    }
};

$app.on_table_sel_acc_render_created = function (render) {

    $app._add_common_render(render);

    render.acc_info = function (row_id, fields) {
        var ret = [];

        ret.push('<span class="field-name">' + fields.username + '@' + fields._host.ip);
        if(fields._host.name.length > 0)
            ret.push(' (' + fields._host.name + ')</span>');
        ret.push('</span>');
        if (fields._host.router_ip.length > 0)
            ret.push('<span class="field-desc">由 ' + fields._host.router_ip + ':' + fields._host.router_port + ' 路由</span>');

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
};

$app.on_table_sel_acc_header_created = function (header) {
    $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
        CALLBACK_STACK.create()
            .add(header._table_ctrl.load_data)
            .add(header._table_ctrl.reset_filters)
            .exec();
    });

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    header._table_ctrl.get_filter_ctrl('search').on_created();
};

$app.create_dlg_sel_acc = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-sel-acc';
    dlg.field_id = -1;
    dlg.field_name = '';
    dlg.field_desc = '';

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        btn_sel_all: $('#' + dlg.dom_id + ' input[data-action="sel-all"]'),
        btn_add: $('#' + dlg.dom_id + ' button[data-action="use-selected"]')
    };

    dlg.init = function (cb_stack) {
        dlg.dom.btn_add.click(dlg.on_add);
        dlg.dom.btn_sel_all.click(dlg.on_sel_all);
        cb_stack.exec();
    };

    dlg.show = function () {
        // dlg.init_fields();
        $app.table_sel_acc.load_data();
        dlg.dom.dialog.modal();
    };

    dlg.on_sel_all = function () {
        var _objects = $('#' + $app.table_sel_acc.dom_id + ' tbody').find('[data-check-box]');
        if ($(this).is(':checked')) {
            $.each(_objects, function (i, _obj) {
                $(_obj).prop('checked', true);
            });
        } else {
            $.each(_objects, function (i, _obj) {
                $(_obj).prop('checked', false);
            });
        }
    };

    dlg.check_all_selected = function (cb_stack) {
        var _all_checked = true;
        var _objs = $('#' + dlg.dom_id + ' tbody').find('[data-check-box]');
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
            dlg.dom.btn_sel_all.prop('checked', true);
        } else {
            dlg.dom.btn_sel_all.prop('checked', false);
        }
        if (cb_stack)
            cb_stack.exec();
    };

    dlg.get_selected_items = function () {
        var items = [];
        var _objs = $('#' + dlg.dom_id + ' tbody tr td input[data-check-box]');
        $.each(_objs, function (i, _obj) {
            if ($(_obj).is(':checked')) {
                var _row_data = $app.table_sel_acc.get_row(_obj);
                console.log(_row_data);

                var name = _row_data.username + '@' + _row_data._host.ip;
                if (_row_data._host.router_ip.length > 0)
                    name += ' （由 ' + _row_data._host.router_ip + ':' + _row_data._host.router_port + ' 路由）';


                items.push({id: _row_data.id, name: name});
            }
        });

        return items;
    };

    dlg.on_add = function () {
        var items = dlg.get_selected_items();
        if(items.length === 0) {
            $tp.notify_error('请先选择要添加的资产！');
            return;
        }

        $tp.ajax_post_json('/ops/policy/add-members', {
                policy_id: $app.options.policy_id,
                type: TP_POLICY_ASSET, // 被授权资产
                rtype: TP_ACCOUNT,  // 账号
                members: items
            },
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('被授权资产添加成功！');
                    CALLBACK_STACK.create()
                        .add($app.sync_height)
                        .add(dlg.check_all_selected)
                        .add($app.table_asset.load_data)
                        .add($app.table_sel_acc.load_data)
                        .exec();
                } else {
                    $tp.notify_error('被授权资产添加失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，被授权资产添加失败！');
            }
        );

    };

    return dlg;
};

//-------------------------------
// 选择账号组对话框
//-------------------------------

$app.on_table_sel_acc_group_cell_created = function (tbl, row_id, col_key, cell_obj) {
    if (col_key === 'chkbox') {
        cell_obj.find('[data-check-box]').click(function () {
            $app.dlg_sel_acc_group.check_all_selected();
        });
    }
};

$app.on_table_sel_acc_group_render_created = function (render) {

    $app._add_common_render(render);

    render.name = function (row_id, fields) {
        return '<span class="field-name">' + fields.name + '</span><span class="field-desc">' + fields.desc + '</span>';
    };
};

$app.on_table_sel_acc_group_header_created = function (header) {
    $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
        CALLBACK_STACK.create()
            .add(header._table_ctrl.load_data)
            .add(header._table_ctrl.reset_filters)
            .exec();
    });

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    header._table_ctrl.get_filter_ctrl('search').on_created();
};

$app.create_dlg_sel_acc_group = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-sel-acc-group';
    dlg.field_id = -1;  // 用户id
    dlg.field_name = '';
    dlg.field_desc = '';

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        btn_sel_all: $('#' + dlg.dom_id + ' input[data-action="sel-all"]'),
        btn_add: $('#' + dlg.dom_id + ' button[data-action="use-selected"]')
    };

    dlg.init = function (cb_stack) {
        dlg.dom.btn_add.click(dlg.on_add);
        dlg.dom.btn_sel_all.click(dlg.on_sel_all);
        cb_stack.exec();
    };

    dlg.show = function () {
        // dlg.init_fields();
        $app.table_sel_acc_group.load_data();
        dlg.dom.dialog.modal();
    };

    dlg.on_sel_all = function () {
        var _objects = $('#' + $app.table_sel_acc_group.dom_id + ' tbody').find('[data-check-box]');
        if ($(this).is(':checked')) {
            $.each(_objects, function (i, _obj) {
                $(_obj).prop('checked', true);
            });
        } else {
            $.each(_objects, function (i, _obj) {
                $(_obj).prop('checked', false);
            });
        }
    };

    dlg.check_all_selected = function (cb_stack) {
        var _all_checked = true;
        var _objs = $('#' + dlg.dom_id + ' tbody').find('[data-check-box]');
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
            dlg.dom.btn_sel_all.prop('checked', true);
        } else {
            dlg.dom.btn_sel_all.prop('checked', false);
        }
        if (cb_stack)
            cb_stack.exec();
    };

    dlg.get_selected_items = function () {
        var items = [];
        var _objs = $('#' + dlg.dom_id + ' tbody tr td input[data-check-box]');
        $.each(_objs, function (i, _obj) {
            if ($(_obj).is(':checked')) {
                var _row_data = $app.table_sel_acc_group.get_row(_obj);
                items.push({id: _row_data.id, name: _row_data.name});
            }
        });

        return items;
    };

    dlg.on_add = function () {
        var items = dlg.get_selected_items();
        if(items.length === 0) {
            $tp.notify_error('请先选择要添加的资产！');
            return;
        }

        $tp.ajax_post_json('/ops/policy/add-members', {
                policy_id: $app.options.policy_id,
                type: TP_POLICY_ASSET, // 授权操作者
                rtype: TP_GROUP_ACCOUNT,  // 账号组
                members: items
            },
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('被授权资产添加成功！');
                    CALLBACK_STACK.create()
                        .add($app.sync_height)
                        .add(dlg.check_all_selected)
                        .add($app.table_asset.load_data)
                        .add($app.table_sel_acc_group.load_data)
                        .exec();
                } else {
                    $tp.notify_error('被授权资产添加失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，被授权资产添加失败！');
            }
        );

    };

    return dlg;
};

//-------------------------------
// 选择主机对话框
//-------------------------------

$app.on_table_sel_host_cell_created = function (tbl, row_id, col_key, cell_obj) {
    if (col_key === 'chkbox') {
        cell_obj.find('[data-check-box]').click(function () {
            $app.dlg_sel_host.check_all_selected();
        });
    }
};

$app.on_table_sel_host_render_created = function (render) {

    $app._add_common_render(render);

    render.host_info = function (row_id, fields) {
        var ret = [];

        var name = fields.name;
        if (name.length === 0)
            name = fields.ip;
        var ip = fields.ip;
        ret.push('<span class="field-name">' + name + '</span> <div class="field-desc mono">[' + ip + ']');
        if (fields.router_ip.length > 0)
            ret.push(' 由 ' + fields.router_ip + ':' + fields.router_port + ' 路由');
        ret.push('</div>');

        return ret.join('');
    };

};

$app.on_table_sel_host_header_created = function (header) {
    $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
        CALLBACK_STACK.create()
            .add(header._table_ctrl.load_data)
            .add(header._table_ctrl.reset_filters)
            .exec();
    });

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    header._table_ctrl.get_filter_ctrl('search').on_created();
};

$app.create_dlg_sel_host = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-sel-host';
    dlg.field_id = -1;
    dlg.field_name = '';
    dlg.field_desc = '';

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        btn_sel_all: $('#' + dlg.dom_id + ' input[data-action="sel-all"]'),
        btn_add: $('#' + dlg.dom_id + ' button[data-action="use-selected"]')
    };

    dlg.init = function (cb_stack) {
        dlg.dom.btn_add.click(dlg.on_add);
        dlg.dom.btn_sel_all.click(dlg.on_sel_all);
        cb_stack.exec();
    };

    dlg.show = function () {
        $app.table_sel_host.load_data();
        dlg.dom.dialog.modal();
    };

    dlg.on_sel_all = function () {
        var _objects = $('#' + $app.table_sel_host.dom_id + ' tbody').find('[data-check-box]');
        if ($(this).is(':checked')) {
            $.each(_objects, function (i, _obj) {
                $(_obj).prop('checked', true);
            });
        } else {
            $.each(_objects, function (i, _obj) {
                $(_obj).prop('checked', false);
            });
        }
    };

    dlg.check_all_selected = function (cb_stack) {
        var _all_checked = true;
        var _objs = $('#' + dlg.dom_id + ' tbody').find('[data-check-box]');
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
            dlg.dom.btn_sel_all.prop('checked', true);
        } else {
            dlg.dom.btn_sel_all.prop('checked', false);
        }
        if (cb_stack)
            cb_stack.exec();
    };

    dlg.get_selected_items = function () {
        var items = [];
        var _objs = $('#' + dlg.dom_id + ' tbody tr td input[data-check-box]');
        $.each(_objs, function (i, _obj) {
            if ($(_obj).is(':checked')) {
                var _row_data = $app.table_sel_host.get_row(_obj);

                var name = '';
                if (_row_data.name.length > 0)
                    name = _row_data.name + ' [' + _row_data.ip + ']';
                else
                    name = _row_data.ip;

                if (_row_data.router_ip.length > 0)
                    name += ' （由 ' + _row_data.router_ip + ':' + _row_data.router_port + ' 路由）';


                items.push({id: _row_data.id, name: name});
            }
        });

        return items;
    };

    dlg.on_add = function () {
        var items = dlg.get_selected_items();
        if(items.length === 0) {
            $tp.notify_error('请先选择要添加的资产！');
            return;
        }

        $tp.ajax_post_json('/ops/policy/add-members', {
                policy_id: $app.options.policy_id,
                type: TP_POLICY_ASSET, // 被授权资产
                rtype: TP_HOST,  // 主机
                members: items
            },
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('被授权资产添加成功！');
                    CALLBACK_STACK.create()
                        .add($app.sync_height)
                        .add(dlg.check_all_selected)
                        .add($app.table_asset.load_data)
                        .add($app.table_sel_host.load_data)
                        .exec();
                } else {
                    $tp.notify_error('被授权资产添加失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，被授权资产添加失败！');
            }
        );

    };

    return dlg;
};

//-------------------------------
// 选择主机组对话框
//-------------------------------

$app.on_table_sel_host_group_cell_created = function (tbl, row_id, col_key, cell_obj) {
    if (col_key === 'chkbox') {
        cell_obj.find('[data-check-box]').click(function () {
            // $app.check_users_all_selected();
            $app.dlg_sel_host_group.check_all_selected();
        });
    }
};

$app.on_table_sel_host_group_render_created = function (render) {

    $app._add_common_render(render);

    render.name = function (row_id, fields) {
        return '<span class="field-name">' + fields.name + '</span><span class="field-desc">' + fields.desc + '</span>';
    };
};

$app.on_table_sel_host_group_header_created = function (header) {
    $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
        CALLBACK_STACK.create()
            .add(header._table_ctrl.load_data)
            .add(header._table_ctrl.reset_filters)
            .exec();
    });

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    header._table_ctrl.get_filter_ctrl('search').on_created();
};

$app.create_dlg_sel_host_group = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-sel-host-group';
    dlg.field_id = -1;
    dlg.field_name = '';
    dlg.field_desc = '';

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        btn_sel_all: $('#' + dlg.dom_id + ' input[data-action="sel-all"]'),
        btn_add: $('#' + dlg.dom_id + ' button[data-action="use-selected"]')
    };

    dlg.init = function (cb_stack) {
        dlg.dom.btn_add.click(dlg.on_add);
        dlg.dom.btn_sel_all.click(dlg.on_sel_all);
        cb_stack.exec();
    };

    dlg.show = function () {
        $app.table_sel_host_group.load_data();
        dlg.dom.dialog.modal();
    };

    dlg.on_sel_all = function () {
        var _objects = $('#' + $app.table_sel_host_group.dom_id + ' tbody').find('[data-check-box]');
        if ($(this).is(':checked')) {
            $.each(_objects, function (i, _obj) {
                $(_obj).prop('checked', true);
            });
        } else {
            $.each(_objects, function (i, _obj) {
                $(_obj).prop('checked', false);
            });
        }
    };

    dlg.check_all_selected = function (cb_stack) {
        var _all_checked = true;
        var _objs = $('#' + dlg.dom_id + ' tbody').find('[data-check-box]');
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
            dlg.dom.btn_sel_all.prop('checked', true);
        } else {
            dlg.dom.btn_sel_all.prop('checked', false);
        }

        if (cb_stack)
            cb_stack.exec();
    };

    dlg.get_selected_items = function () {
        var items = [];
        var _objs = $('#' + dlg.dom_id + ' tbody tr td input[data-check-box]');
        $.each(_objs, function (i, _obj) {
            if ($(_obj).is(':checked')) {
                var _row_data = $app.table_sel_host_group.get_row(_obj);
                items.push({id: _row_data.id, name: _row_data.name});
            }
        });

        return items;
    };

    dlg.on_add = function () {
        var items = dlg.get_selected_items();
        if(items.length === 0) {
            $tp.notify_error('请先选择要添加的资产！');
            return;
        }

        $tp.ajax_post_json('/ops/policy/add-members', {
                policy_id: $app.options.policy_id,
                type: TP_POLICY_ASSET, // 授权操作者
                rtype: TP_GROUP_HOST,  // 主机组
                members: items
            },
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('被授权资产添加成功！');
                    CALLBACK_STACK.create()
                        .add($app.sync_height)
                        .add(dlg.check_all_selected)
                        .add($app.table_asset.load_data)
                        .add($app.table_sel_host_group.load_data)
                        .exec();
                } else {
                    $tp.notify_error('被授权资产添加失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，被授权资产添加失败！');
            }
        );

    };

    return dlg;
};

$app.init_flags = function() {
    console.log($app.options);

    // if(($app.options.policy_flags.record & TP_FLAG_RECORD_REPLAY) !== 0)
    //     $app.dom.flag_record_allow_replay.addClass('tp-selected');

    if(($app.options.policy_flags.rdp & TP_FLAG_RDP_CLIPBOARD) !== 0)
        $app.dom.flag_rdp_allow_clipboard.addClass('tp-selected');
    if(($app.options.policy_flags.rdp & TP_FLAG_RDP_DISK) !== 0)
        $app.dom.flag_rdp_allow_disk.addClass('tp-selected');
    if(($app.options.policy_flags.rdp & TP_FLAG_RDP_CONSOLE) !== 0)
        $app.dom.flag_rdp_allow_console.addClass('tp-selected');

    if(($app.options.policy_flags.ssh & TP_FLAG_SSH_SHELL) !== 0)
        $app.dom.flag_ssh_allow_shell.addClass('tp-selected');
    if(($app.options.policy_flags.ssh & TP_FLAG_SSH_SFTP) !== 0)
        $app.dom.flag_ssh_allow_sftp.addClass('tp-selected');
};

$app.on_click_flag = function (e) {
    var obj = $(e.target);
    if (obj.hasClass('tp-selected')) {
        obj.removeClass('tp-selected');
    } else {
        obj.addClass('tp-selected');
    }
};

$app.on_save_flags = function () {
    var flag_record = 0;
    flag_record |= TP_FLAG_RECORD_REPLAY; // now we always need record replay.
    flag_record |= TP_FLAG_RECORD_REAL_TIME; // not implement, set this flag for default.
    // if ($app.dom.flag_record_allow_replay.hasClass('tp-selected'))
    //     flag_record |= TP_FLAG_RECORD_REPLAY;

    var flag_rdp = 0;
    flag_rdp |= TP_FLAG_RDP_DESKTOP; // before support remote-app, remote-desktop is the only way to access remote host.
    if ($app.dom.flag_rdp_allow_clipboard.hasClass('tp-selected'))
        flag_rdp |= TP_FLAG_RDP_CLIPBOARD;
    if ($app.dom.flag_rdp_allow_disk.hasClass('tp-selected'))
        flag_rdp |= TP_FLAG_RDP_DISK;
    if ($app.dom.flag_rdp_allow_console.hasClass('tp-selected'))
        flag_rdp |= TP_FLAG_RDP_CONSOLE;

    var flag_ssh = 0;
    if ($app.dom.flag_ssh_allow_shell.hasClass('tp-selected'))
        flag_ssh |= TP_FLAG_SSH_SHELL;
    if ($app.dom.flag_ssh_allow_sftp.hasClass('tp-selected'))
        flag_ssh |= TP_FLAG_SSH_SFTP;

    if (flag_ssh === 0) {
        $tp.notify_error('SSH选项都未选择，无法进行SSH连接哦！');
        return;
    }


    $tp.ajax_post_json('/ops/policy/set-flags', {
            policy_id: $app.options.policy_id,
            flag_record: flag_record,
            flag_rdp: flag_rdp,
            flag_ssh: flag_ssh
        },
        function (ret) {
            if (ret.code === TPE_OK) {
                $tp.notify_success('选项设置成功！');
            } else {
                $tp.notify_error('选项设置失败：' + tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $tp.notify_error('网络故障，选项设置失败！');
        }
    );
};
