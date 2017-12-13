"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        btn_refresh_host: $('#btn-refresh-host'),
        btn_add_user: $('#btn-add-host'),
        chkbox_host_select_all: $('#table-host-select-all')
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
    // 资产列表表格
    //-------------------------------
    var table_host_options = {
        dom_id: 'table-host',
        data_source: {
            type: 'ajax-post',
            url: '/ops/get-remotes'
        },
        column_default: {sort: false, align: 'left'},
        columns: [
            // {
            //     // title: '<input type="checkbox" id="user-list-select-all" value="">',
            //     title: '<a href="javascript:;" data-reset-filter><i class="fa fa-rotate-left fa-fw"></i></a>',
            //     key: 'chkbox',
            //     sort: false,
            //     width: 36,
            //     align: 'center',
            //     render: 'make_check_box',
            //     fields: {id: 'id'}
            // },
            {
                title: '主机',
                key: 'host',
                // sort: true,
                // header_render: 'filter_search',
                width: 300,
                render: 'host_info',
                fields: {ip: 'ip', router_ip: 'router_ip', router_port: 'router_port', h_name: 'h_name'}
            },
            {
                title: '远程账号',
                key: 'account',
                width: 100,
                header_align: 'center',
                cell_align: 'right',
                render: 'account',
                fields: {accs: 'accounts_', h_state: 'h_state', gh_state: 'gh_state'}
            },
            {
                title: '远程连接',
                key: 'action',
                render: 'action',
                fields: {accs: 'accounts_', h_state: 'h_state', gh_state: 'gh_state'}
            }
        ],

        // 重载回调函数
        on_header_created: $app.on_table_host_header_created,
        on_render_created: $app.on_table_host_render_created,
        on_cell_created: $app.on_table_host_cell_created
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
        place_holder: '搜索：主机IP/名称/描述/资产编号/等等...'
    });
    // $app.table_host_role_filter = $tp.create_table_filter_role($app.table_host, $app.role_list);
    // 主机没有“临时锁定”状态，因此要排除掉
    // $tp.create_table_header_filter_state($app.table_host, 'state', $app.obj_states, [TP_STATE_LOCKED]);

    // 从cookie中读取用户分页限制的选择
    $tp.create_table_paging($app.table_host, 'table-host-paging',
        {
            per_page: Cookies.get($app.page_id('asset_host') + '_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('asset_host') + '_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_host, 'table-host-pagination');

    //-------------------------------
    // 对话框
    //-------------------------------

    //-------------------------------
    // 页面控件事件绑定
    //-------------------------------
    $app.dom.btn_refresh_host.click(function () {
        $app.table_host.load_data();
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
            var action = $(this).attr('data-action');
            var protocol_sub_type = $(this).attr('data-sub-protocol');
            var uni_id = $(this).attr('data-id');

            // console.log(uni_id, protocol_sub_type);

            if (action === 'rdp') {
                $app.connect_remote(uni_id, TP_PROTOCOL_TYPE_RDP, TP_PROTOCOL_TYPE_RDP_DESKTOP);
            } else if (action === 'ssh') {
                $app.connect_remote(uni_id, TP_PROTOCOL_TYPE_SSH, protocol_sub_type);
            } else if (action === 'telnet') {
                $tp.notify_error('尚未实现！');
            }
        });
    }
};

// $app.check_host_all_selected = function (cb_stack) {
//     var _all_checked = true;
//     var _objs = $('#' + $app.table_host.dom_id + ' tbody').find('[data-check-box]');
//     if (_objs.length === 0) {
//         _all_checked = false;
//     } else {
//         $.each(_objs, function (i, _obj) {
//             if (!$(_obj).is(':checked')) {
//                 _all_checked = false;
//                 return false;
//             }
//         });
//     }
//
//     if (_all_checked) {
//         $app.dom.chkbox_host_select_all.prop('checked', true);
//     } else {
//         $app.dom.chkbox_host_select_all.prop('checked', false);
//     }
//
//     if (cb_stack)
//         cb_stack.exec();
// };

$app.on_table_host_render_created = function (render) {
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
    // render.filter_os = function (header, title, col) {
    //     return '';
    // };

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

    // render.make_check_box = function (row_id, fields) {
    //     return '<span><input type="checkbox" data-check-box="' + fields.id + '" data-row-id="' + row_id + '"></span>';
    // };
    //
    render.host_info = function (row_id, fields) {
        var title, sub_title;

        title = fields.h_name;
        sub_title = fields.ip;

        if (title.length === 0) {
            title = fields.ip;
        }

        // title = fields.a_name + '@' + title;

        var desc = [];
        // if (fields.desc.length > 0) {
        //     desc.push(fields.desc.replace(/\r/ig, "").replace(/\n/ig, "<br/>"));
        // }
        if (fields.router_ip.length > 0) {
            sub_title += '，由 ' + fields.router_ip + ':' + fields.router_port + ' 路由';
        }

        var ret = [];
        // ret.push('<div><span class="host-name" href="javascript:;">' + title + '</span>');
        // if (desc.length > 0) {
        //     ret.push('<a class="host-id-desc" data-toggle="popover" data-placement="right"');
        //     ret.push(' data-html="true"');
        //     ret.push(' data-content="' + desc.join('') + '"');
        //     ret.push('><i class="fa fa-list-alt fw"></i></a>');
        // }

        if (desc.length > 0) {
            ret.push('<div><a class="host-name host-name-desc" data-toggle="popover" data-placement="right"');
            // ret.push('<a class="host-id-desc" data-toggle="popover" data-placement="right"');
            ret.push(' data-html="true"');
            ret.push(' data-content="' + desc.join('') + '"');
            ret.push('>' + title + '</a>');
        } else {
            ret.push('<div><span class="host-name">' + title + '</span>');
        }

        ret.push('</div><div class="host-ip" href="javascript:;" data-host-desc="' + sub_title + '">' + sub_title + '</div>');
        return ret.join('');
    };

    render.account = function (row_id, fields) {
        var h = [];
        for (var i = 0; i < fields.accs.length; ++i) {
            var acc = fields.accs[i];
            h.push('<div class="remote-info-group" id =' + "account-id-" + acc.id + '"><ul>');
            h.push('<li>' + acc.a_name + '</li>');
            h.push('</ul></div>');
        }
        return h.join('');
    };
    render.action = function (row_id, fields) {
        // console.log(fields);
        var h = [];
        for (var i = 0; i < fields.accs.length; ++i) {
            var acc = fields.accs[i];
            var act_btn = [];

            var disabled = '';
            if (acc.a_state !== TP_STATE_NORMAL)
                disabled = '账号已禁用';
            if (disabled.length === 0 && (acc.policy_auth_type === TP_POLICY_AUTH_USER_gACC || acc.policy_auth_type === TP_POLICY_AUTH_gUSER_gACC) && acc.ga_state !== TP_STATE_NORMAL)
                disabled = '账号所在组已禁用';
            if (disabled.length === 0 && fields.h_state !== TP_STATE_NORMAL)
                disabled = '主机已禁用';
            if (disabled.length === 0 && (acc.policy_auth_type === TP_POLICY_AUTH_USER_gHOST || acc.policy_auth_type === TP_POLICY_AUTH_gUSER_gHOST) && fields.gh_state !== TP_STATE_NORMAL)
                disabled = '主机所在组已禁用';

            if (disabled.length > 0) {
                act_btn.push('<li class="remote-action-state state-disabled">');
                act_btn.push('<i class="fa fa-ban fa-fw"></i> ' + disabled);
                act_btn.push('</li>');
            } else {
                if (acc.protocol_type === TP_PROTOCOL_TYPE_RDP) {
                    if ((acc.policy_.flag_rdp & TP_FLAG_RDP_DESKTOP) !== 0) {
                        act_btn.push('<li class="remote-action-btn">');
                        act_btn.push('<button type="button" class="btn btn-sm btn-primary" data-action="rdp" data-id="' + acc.uni_id + '" data-sub-protocol="' + TP_PROTOCOL_TYPE_RDP_DESKTOP + '"><i class="fa fa-desktop fa-fw"></i> RDP</button>');
                        act_btn.push('</li>');
                    }
                } else if (acc.protocol_type === TP_PROTOCOL_TYPE_SSH) {
                    if ((acc.policy_.flag_ssh & TP_FLAG_SSH_SHELL) !== 0) {
                        act_btn.push('<li class="remote-action-btn">');
                        act_btn.push('<button type="button" class="btn btn-sm btn-success" data-action="ssh" data-id="' + acc.uni_id + '" data-sub-protocol="' + TP_PROTOCOL_TYPE_SSH_SHELL + '"><i class="fa fa-keyboard-o fa-fw"></i> SSH</button>');
                        act_btn.push('</li>');
                    }

                    if ((acc.policy_.flag_ssh & TP_FLAG_SSH_SFTP) !== 0) {
                        act_btn.push('<li class="remote-action-btn">');
                        act_btn.push('<button type="button" class="btn btn-sm btn-info" data-action="ssh" data-id="' + acc.uni_id + '" data-sub-protocol="' + TP_PROTOCOL_TYPE_SSH_SFTP + '"><i class="fa fa-upload fa-fw"></i> SFTP</button>');
                        act_btn.push('</li>');
                    }
                } else if (acc.protocol_type === TP_PROTOCOL_TYPE_TELNET) {
                    act_btn.push('<li class="remote-action-btn">');
                    act_btn.push('<button type="button" class="btn btn-sm btn-success" data-action="telnet" data-id="' + acc.uni_id + '" data-sub-protocol="' + TP_PROTOCOL_TYPE_TELNET_SHELL + '"><i class="fa fa-keyboard-o fa-fw"></i> TELNET</button>');
                    act_btn.push('</li>');
                }
            }

            h.push('<div class="remote-action-group" id =' + "account-id-" + acc.id + '"><ul>');
            h.push(act_btn.join(''));
            h.push('</ul></div>');
        }
        return h.join('');
    };

    render.state = function (row_id, fields) {
        // console.log(fields);
        var _prompt, _style, _state;

        if ((fields.h_state === TP_STATE_NORMAL || fields.h_state === 0)
            && (fields.gh_state === TP_STATE_NORMAL || fields.gh_state === 0)
        // && (fields.a_state === TP_STATE_NORMAL || fields.a_state === 0)
        // && (fields.ga_state === TP_STATE_NORMAL || fields.ga_state === 0)
        ) {
            return '<span class="label label-sm label-success">正常</span>'
        }

        var states = [
            {n: '主机', s: fields.h_state},
            {n: '主机组', s: fields.gh_state},
            // {n: '账号', s: fields.a_state},
            // {n: '账号组', s: fields.ga_state}
        ];

        for (var j = 0; j < states.length; ++j) {
            if (states[j].s === TP_STATE_NORMAL)
                continue;

            for (var i = 0; i < $app.obj_states.length; ++i) {
                if ($app.obj_states[i].id === states[j].s) {
                    _style = $app.obj_states[i].style;
                    _state = $app.obj_states[i].name;
                    _prompt = states[j].n;
                    return '<span class="label label-sm label-' + _style + '">' + _prompt + '被' + _state + '</span>'
                }
            }
        }

        return '<span class="label label-sm label-info"><i class="fa fa-question-circle"></i> 未知</span>'
    };

    // render.make_host_action_btn = function (row_id, fields) {
    //     var h = [];
    //     h.push('<div class="btn-group btn-group-sm">');
    //     h.push('<button type="button" class="btn btn-no-border dropdown-toggle" data-toggle="dropdown">');
    //     h.push('<span data-selected-action>操作</span> <i class="fa fa-caret-right"></i></button>');
    //     h.push('<ul class="dropdown-menu dropdown-menu-right dropdown-menu-sm">');
    //     h.push('<li><a href="javascript:;" data-action="edit"><i class="fa fa-edit fa-fw"></i> 编辑</a></li>');
    //     h.push('<li><a href="javascript:;" data-action="lock"><i class="fa fa-lock fa-fw"></i> 禁用</a></li>');
    //     h.push('<li><a href="javascript:;" data-action="unlock"><i class="fa fa-unlock fa-fw"></i> 解禁</a></li>');
    //     h.push('<li role="separator" class="divider"></li>');
    //     h.push('<li><a href="javascript:;" data-action="account"><i class="fa fa-user-secret fa-fw"></i> 管理远程账号</a></li>');
    //     h.push('<li role="separator" class="divider"></li>');
    //     h.push('<li><a href="javascript:;" data-action="duplicate"><i class="fa fa-cubes fa-fw"></i> 复制主机</a></li>');
    //     h.push('<li><a href="javascript:;" data-action="delete"><i class="fa fa-times-circle fa-fw"></i> 删除</a></li>');
    //     h.push('</ul>');
    //     h.push('</div>');
    //
    //     return h.join('');
    // };
};

$app.on_table_host_header_created = function (header) {
    $app.dom.btn_table_host_reset_filter = $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]');
    $app.dom.btn_table_host_reset_filter.click(function () {
        CALLBACK_STACK.create()
            .add(header._table_ctrl.load_data)
            .add(header._table_ctrl.reset_filters)
            .exec();
    });

    // TODO: 当过滤器不是默认值时，让“重置过滤器按钮”有呼吸效果，避免用户混淆 - 实验性质
    // var t1 = function(){
    //     $app.dom.btn_table_host_reset_filter.fadeTo(1000, 1.0, function(){
    //         $app.dom.btn_table_host_reset_filter.fadeTo(1000, 0.2, t1);
    //     });
    // };
    // $app.dom.btn_table_host_reset_filter.fadeTo(1000, 0.2, t1);

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    header._table_ctrl.get_filter_ctrl('search').on_created();
    // header._table_ctrl.get_filter_ctrl('role').on_created();
    // header._table_ctrl.get_filter_ctrl('state').on_created();
};

$app.get_selected_user = function (tbl) {
    var users = [];
    var _objs = $('#' + $app.table_host.dom_id + ' tbody tr td input[data-check-box]');
    $.each(_objs, function (i, _obj) {
        if ($(_obj).is(':checked')) {
            var _row_data = tbl.get_row(_obj);
            // _all_checked = false;
            users.push(_row_data.id);
        }
    });
    return users;
};

$app.connect_remote = function (uni_id, protocol_type, protocol_sub_type) {
    $assist.do_teleport(
        {
            auth_id: uni_id,
            protocol_type: protocol_type,
            protocol_sub_type: protocol_sub_type
        },
        function () {
            // func_success
            //$tp.notify_success('远程连接测试通过！');
        },
        function (code, message) {
            if (code === TPE_NO_ASSIST)
                $assist.alert_assist_not_found();
            else
                $tp.notify_error('远程连接失败：' + tp_error_msg(code, message));
        }
    );
};
