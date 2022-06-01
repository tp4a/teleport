"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        btn_sel_group: $('#btn-sel-group button')
        , btn_refresh_host: $('#btn-refresh-host')
    };

    // console.log($app.options);
    if (!$app.options.core_cfg.detected) {
        $tp.notify_error('核心服务未启动，无法进行远程连接！');
        cb_stack.exec();
        return;
    }

    // $('#dlg-ops-token').modal({backdrop: 'static'});
    $app.dlg_ops_token = $app.create_dlg_ops_token();

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
    let table_host_options = {
        dom_id: 'table-host',
        data_source: {
            type: 'ajax-post',
            url: '/ops/get-remotes'
        },
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
                title: '主机',
                key: 'host',
                // sort: true,
                header_render: 'filter_search',
                width: 320,
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
    // 过滤器
    //-------------------------------
    $tp.create_table_header_filter_search($app.table_host, {
        name: 'search',
        place_holder: '搜索：主机IP/名称/描述/资产编号/等等...'
    });

    $tp.create_table_filter_group($app.table_host, 'host_group', '#filter-host-group', $app.options.host_groups);

    // 分页设置
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
    $app.dlg_rdp_options = $app.create_dlg_rdp_options();
    cb_stack.add($app.dlg_rdp_options.init);

    //-------------------------------
    // 页面控件事件绑定
    //-------------------------------
    $app.dom.btn_refresh_host.click(function () {
        $app.table_host.load_data();
    });

    cb_stack.exec();
};

$app.on_table_host_cell_created = function (tbl, row_id, col_key, cell_obj) {

    if (col_key === 'action') {

        // 绑定系统选择框事件
        cell_obj.find('[data-action]').click(function (e) {
            let action = $(this).attr('data-action');
            let protocol_sub_type = $(this).attr('data-sub-protocol');
            let uni_id = $(this).attr('data-id');
            let acc_id = parseInt($(this).attr('data-acc-id'));
            let host_id = parseInt($(this).attr('data-host-id'));

            if (action === 'rdp') {
                $app.connect_remote(uni_id, acc_id, host_id, TP_PROTOCOL_TYPE_RDP, TP_PROTOCOL_TYPE_RDP_DESKTOP);
            } else if (action === 'rdp-option') {
                $app.dlg_rdp_options.show(e.pageX, e.pageY, uni_id, acc_id, host_id, TP_PROTOCOL_TYPE_RDP, TP_PROTOCOL_TYPE_RDP_DESKTOP);
            } else if (action === 'ssh') {
                $app.connect_remote(uni_id, acc_id, host_id, TP_PROTOCOL_TYPE_SSH, protocol_sub_type);
            } else if (action === 'telnet') {
                $app.connect_remote(uni_id, acc_id, host_id, TP_PROTOCOL_TYPE_TELNET, TP_PROTOCOL_TYPE_TELNET_SHELL);
            } else if (action === 'ops_token') {
                let _row_data = $app.table_host.get_row(row_id);
                let _index = parseInt($(this).attr('data-index'));
                $app.dlg_ops_token.show(uni_id, _row_data.h_name, _row_data.ip, _row_data.accounts_[_index]);
            }
        });
    }
};

$app.on_table_host_render_created = function (render) {

    render.filter_state = function (header, title, col) {
        let _ret = ['<div class="tp-table-filter tp-table-filter-' + col.cell_align + '">'];
        _ret.push('<div class="tp-table-filter-inner">');
        _ret.push('<div class="search-title">' + title + '</div>');

        // 表格内嵌过滤器的DOM实体在这时生成
        let filter_ctrl = header._table_ctrl.get_filter_ctrl('state');
        _ret.push(filter_ctrl.render());

        _ret.push('</div></div>');

        return _ret.join('');
    };

    render.filter_search = function (header, title, col) {
        let _ret = ['<div class="tp-table-filter tp-table-filter-input">'];
        _ret.push('<div class="tp-table-filter-inner">');
        _ret.push('<div class="search-title">' + title + '</div>');

        // 表格内嵌过滤器的DOM实体在这时生成
        let filter_ctrl = header._table_ctrl.get_filter_ctrl('search');
        _ret.push(filter_ctrl.render());

        _ret.push('</div></div>');

        return _ret.join('');
    };

    render.host_info = function (row_id, fields) {
        let title, sub_title;

        title = fields.h_name;
        sub_title = fields.ip;

        if (title.length === 0) {
            title = fields.ip;
        }

        // title = fields.a_name + '@' + title;

        // let desc = [];
        if (fields.router_ip.length > 0) {
            sub_title += '，由 ' + fields.router_ip + ':' + fields.router_port + ' 路由';
        }

        let ret = [];
        // if (desc.length > 0) {
        //     ret.push('<div><a class="host-name host-name-desc" data-toggle="popover" data-placement="right"');
        //     ret.push(' data-html="true"');
        //     ret.push(' data-content="' + desc.join('') + '"');
        //     ret.push('>' + title + '</a>');
        // } else {
        //     ret.push('<div><span class="host-name">' + title + '</span>');
        // }

        ret.push('<div><span class="host-name">' + title + '</span>');
        ret.push('</div><div class="host-ip" href="javascript:;" data-host-desc="' + sub_title + '">' + sub_title + '</div>');
        return ret.join('');
    };

    render.account = function (row_id, fields) {
        let h = [];

        if (fields.h_state !== TP_STATE_NORMAL || (fields.gh_state !== TP_STATE_NORMAL && fields.gh_state !== 0)) {
            // 1. 主机已经被禁用，不显示相关账号。
            // 2. 主机所在分组已经被禁用，不显示相关账号。
            return;
        }

        for (let i = 0; i < fields.accs.length; ++i) {
            let acc = fields.accs[i];
            h.push('<div class="remote-info-group"><ul>');
            h.push('<li>' + acc.a_name + '</li>');
            h.push('</ul></div>');
        }

        return h.join('');
    };
    render.action = function (row_id, fields) {
        let is_disabled = false;
        let disable_msg = '';

        if (fields.h_state !== TP_STATE_NORMAL) {
            is_disabled = true;
            disable_msg = '无可用远程连接，主机已被禁用';
        }
        if (fields.gh_state !== TP_STATE_NORMAL && fields.gh_state !== 0) {
            is_disabled = true;
            disable_msg = '无可用远程连接，主机所在分组已被禁用';
        }
        if (is_disabled) {
            let h = [];
            h.push('<div><div class="remote-action-group"><div class="btn-group btn-group-sm">');
            h.push('<button type="button" class="btn btn-disabled" disabled><i class="fa fa-ban fa-fw"></i> ');
            h.push(disable_msg);
            h.push('</button></div></div>');
            return h.join('');
        }


        let h = [];
        for (let i = 0; i < fields.accs.length; ++i) {
            let acc = fields.accs[i];
            let act_btn = [];

            is_disabled = false;
            disable_msg = '';

            if (acc.a_state !== TP_STATE_NORMAL)
                disable_msg = '账号已被禁用';
            if (disable_msg.length === 0 && (acc.policy_auth_type === TP_POLICY_AUTH_USER_gACC || acc.policy_auth_type === TP_POLICY_AUTH_gUSER_gACC) && acc.ga_state !== TP_STATE_NORMAL)
                disable_msg = '账号所在分组已被禁用';
            // if (disable_msg.length === 0 && fields.h_state !== TP_STATE_NORMAL)
            //     disable_msg = '主机已被禁用';
            // if (disable_msg.length === 0 && (acc.policy_auth_type === TP_POLICY_AUTH_USER_gHOST || acc.policy_auth_type === TP_POLICY_AUTH_gUSER_gHOST) && fields.gh_state !== TP_STATE_NORMAL)
            //     disable_msg = '主机所在组已被禁用';

            if (disable_msg.length > 0)
                is_disabled = true;

            if (acc.protocol_type === TP_PROTOCOL_TYPE_RDP) {
                if (!is_disabled) {
                    if (!$app.options.core_cfg.rdp.enable) {
                        is_disabled = true;
                        disable_msg = 'RDP协议未启用';
                    } else {
                        if ((acc.policy_.flag_rdp & TP_FLAG_RDP_DESKTOP) !== 0) {
                            act_btn.push('<div class="btn-group btn-group-sm">');
                            act_btn.push('<button type="button" class="btn btn-primary" data-action="rdp" data-id="' + acc.uni_id + '" data-acc-id="' + acc.a_id + '" data-host-id="' + acc.h_id + '" data-sub-protocol="' + TP_PROTOCOL_TYPE_RDP_DESKTOP + '"><i class="fa fa-desktop fa-fw"></i> RDP</button>');
                            act_btn.push('<button type="button" class="btn btn-primary dropdown-toggle" data-action="rdp-option" data-id="' + acc.uni_id + '" data-acc-id="' + acc.a_id + '" data-host-id="' + acc.h_id + '" data-sub-protocol="' + TP_PROTOCOL_TYPE_RDP_DESKTOP + '">');
                            act_btn.push('<i class="fa fa-cog"></i>');
                            act_btn.push('</button>');
                            act_btn.push('</div>');
                        }
                    }
                } else {
                    disable_msg = 'RPD' + disable_msg;
                }
            } else if (acc.protocol_type === TP_PROTOCOL_TYPE_SSH) {
                if (!is_disabled) {
                    if (!$app.options.core_cfg.ssh.enable) {
                        is_disabled = true;
                        disable_msg = 'SSH协议未启用';
                    } else {
                        act_btn.push('<div class="btn-group btn-group-sm">');
                        if ((acc.policy_.flag_ssh & TP_FLAG_SSH_SHELL) !== 0) {
                            act_btn.push('<button type="button" class="btn btn-success" data-action="ssh" data-id="' + acc.uni_id + '" data-acc-id="' + acc.a_id + '" data-host-id="' + acc.h_id + '" data-sub-protocol="' + TP_PROTOCOL_TYPE_SSH_SHELL + '"><i class="far fa-keyboard fa-fw"></i> SSH</button>');
                        }

                        if ((acc.policy_.flag_ssh & TP_FLAG_SSH_SFTP) !== 0) {
                            act_btn.push('<button type="button" class="btn btn-info" data-action="ssh" data-id="' + acc.uni_id + '" data-acc-id="' + acc.a_id + '" data-host-id="' + acc.h_id + '" data-sub-protocol="' + TP_PROTOCOL_TYPE_SSH_SFTP + '"><i class="fa fa-upload fa-fw"></i> SFTP</button>');
                        }
                        act_btn.push('</div>');
                    }
                } else {
                    disable_msg = 'SSH' + disable_msg;
                }
            } else if (acc.protocol_type === TP_PROTOCOL_TYPE_TELNET) {
                if (!is_disabled) {
                    if (!$app.options.core_cfg.telnet.enable) {
                        is_disabled = true;
                        disable_msg = 'TELNET协议未启用';
                    } else {
                        act_btn.push('<div class="btn-group btn-group-sm">');
                        act_btn.push('<button type="button" class="btn btn-warning" data-action="telnet" data-id="' + acc.uni_id + '" data-acc-id="' + acc.a_id + '" data-host-id="' + acc.h_id + '" data-sub-protocol="' + TP_PROTOCOL_TYPE_TELNET_SHELL + '"><i class="far fa-keyboard fa-fw"></i> TELNET</button>');
                        act_btn.push('</div>');
                    }
                } else {
                    disable_msg = 'TELNET' + disable_msg;
                }
            }

            if (disable_msg.length > 0) {
                is_disabled = true;
                act_btn.push('<div class="btn-group btn-group-sm">');
                act_btn.push('<button type="button" class="btn btn-disabled" disabled><i class="fa fa-ban fa-fw"></i> ');
                act_btn.push(disable_msg);
                act_btn.push('</button>');
                act_btn.push('</div>');
            }


            h.push('<div>');
            h.push('<div class="remote-action-group">');
            h.push(act_btn.join(''));
            h.push('</div>');

            // 目前仅支持SSH可以使用远程连接授权码
            if (!is_disabled && acc.protocol_type === TP_PROTOCOL_TYPE_SSH) {
                h.push('<div class="remote-config">');
                h.push('<button type="button" class="btn btn-default" data-action="ops_token" data-index="' + i + '" data-id="' + acc.uni_id + '" data-acc-id=' + acc.a_id + ' data-host-id=' + acc.h_id + '><i class="fa fa-key fa-fw"></i> 获取远程连接配置</button>');
                h.push('</div>');
            }

            h.push('</div>');
        }

        return h.join('');
    };
};

$app.on_table_host_header_created = function (header) {
    $app.dom.btn_table_host_reset_filter = $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]');
    $app.dom.btn_table_host_reset_filter.click(function () {
        CALLBACK_STACK.create()
            .add(header._table_ctrl.load_data)
            .add(header._table_ctrl.reset_filters)
            .exec();
    });

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    header._table_ctrl.get_filter_ctrl('search').on_created();
};

$app.create_dlg_rdp_options = function () {
    let dlg = {};
    dlg.dom_id = 'dlg-rdp-options';
    dlg.uni_id = '';
    dlg.acc_id = 0;
    dlg.host_id = 0;
    dlg.protocol_type = TP_PROTOCOL_TYPE_RDP;
    dlg.protocol_sub_type = TP_PROTOCOL_TYPE_RDP_DESKTOP;
    dlg.rdp_w = 0;
    dlg.rdp_h = 0;
    dlg.rdp_console = false;

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        screen_size: $('#' + dlg.dom_id + ' [data-field="screen-size"]'),
        console_mode: $('#' + dlg.dom_id + ' input[data-field="console-mode"]'),
        btn_connect: $('#' + dlg.dom_id + ' [data-field="do-rdp-connect"]')
    };
    dlg.timer = null;

    dlg.init = function (cb_stack) {
        dlg.dom.dialog.mouseleave(function () {
            dlg.timer = setTimeout(function () {
                dlg.hide();
            }, 800);
        });
        dlg.dom.dialog.mouseenter(function () {
            if (dlg.timer !== null) {
                clearTimeout(dlg.timer);
                dlg.timer = null;
            }
        });

        dlg.dom.btn_connect.click(function () {
            dlg.hide();

            let _size_obj = $('#' + dlg.dom_id + ' input[name="screen-size"]:checked');
            let _console = dlg.dom.console_mode.is(':checked');
            let _w = parseInt(_size_obj.attr('data-w'));
            let _h = parseInt(_size_obj.attr('data-h'));

            dlg.rdp_w = _w;
            dlg.rdp_h = _h;
            dlg.rdp_console = _console;
            Cookies.set('rdp_options', {w: _w, h: _h, 'c': _console}, {path: '/ops/remote'});

            $app.connect_remote(dlg.uni_id, dlg.acc_id, dlg.host_id, dlg.protocol_type, dlg.protocol_sub_type);
        });

        let ops = Cookies.getJSON('rdp_options');
        dlg.rdp_w = 0;
        dlg.rdp_h = 0;
        dlg.rdp_console = false;
        if (!_.isUndefined(ops)) {
            dlg.rdp_w = ops.w;
            dlg.rdp_h = ops.h;
            dlg.rdp_console = ops.c;
        }
        if (_.isUndefined(dlg.rdp_w) || _.isUndefined(dlg.rdp_h)) {
            dlg.rdp_w = 0;
            dlg.rdp_h = 0;
        }
        if (_.isUndefined(dlg.rdp_console))
            dlg.rdp_console = false;

        let ss = [
            {w: 800, h: 600},
            {w: 1024, h: 768},
            {w: 1280, h: 1024},
            {w: 1366, h: 768},
            {w: 1440, h: 900}
        ];

        let h = [];
        h.push('<div class="radio">');
        h.push('<div><label><input type="radio" name="screen-size" data-w="0" data-h="0"');
        if (dlg.rdp_w === 0 && dlg.rdp_h === 0)
            h.push(' checked');
        h.push('> 全屏</label></div>');

        for (let i = 0; i < ss.length; ++i) {
            let _w = ss[i].w;
            let _h = ss[i].h;
            h.push('<div><label><input type="radio" name="screen-size" data-w="' + _w + '" data-h="' + _h + '"');
            if (dlg.rdp_w === _w && dlg.rdp_h === _h)
                h.push(' checked');
            h.push('> ' + _w + ' x ' + _h + '</label></div>');
        }
        h.push('</div>');
        dlg.dom.screen_size.html($(h.join('')));

        if (dlg.rdp_console)
            dlg.dom.console_mode.prop('checked', true);

        cb_stack.exec();
    };

    dlg.show = function (x, y, uni_id, acc_id, host_id, protocol_type, protocol_sub_type) {
        if (dlg.timer !== null) {
            clearTimeout(dlg.timer);
            dlg.timer = null;
        }

        dlg.uni_id = uni_id;
        dlg.acc_id = acc_id;
        dlg.host_id = host_id;
        dlg.protocol_type = protocol_type;
        dlg.protocol_sub_type = protocol_sub_type;

        let w = dlg.dom.dialog.width();
        x -= w / 3;
        y -= 12;
        dlg.dom.dialog.css({left: x, top: y});
        dlg.dom.dialog.fadeIn();
    };

    dlg.hide = function () {
        dlg.dom.dialog.fadeOut();
    };

    return dlg;
};

$app.get_ops_token = function (uni_id, acc_id) {
    uni_id = uni_id || "";
    $tp.ajax_post_json('/ops/get-ops-token',
        {uni_id: uni_id, acc_id: acc_id},
        function (ret) {
            if (ret.code === TPE_OK) {

            } else {
                $tp.notify_error('无法获取远程连接配置：' + tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $tp.notify_error('网络故障，无法获取远程连接配置！');
        }
    );
}

$app.connect_remote = function (uni_id, acc_id, host_id, protocol_type, protocol_sub_type) {

    let args = {
        mode: 1,
        auth_id: uni_id,
        acc_id: acc_id,
        host_id: host_id,
        protocol_type: protocol_type,
        protocol_sub_type: protocol_sub_type,
        is_interactive: false,
    };
    if (protocol_type === TP_PROTOCOL_TYPE_RDP) {
        args.rdp_width = $app.dlg_rdp_options.rdp_w;
        args.rdp_height = $app.dlg_rdp_options.rdp_h;
        args.rdp_console = $app.dlg_rdp_options.rdp_console;
    }

    if (uni_id === 'none' || uni_id === '')
        args.mode = 2;

    // 根据acc_id判断此远程账号是否有预设密码，如果没有，则需要设置interactive模式。
    $tp.ajax_post_json('/asset/get-account-interactive-mode',
        {acc_id: acc_id},
        function (ret) {
            if (ret.code === TPE_OK) {
                args.is_interactive = ret.data.is_interactive;

                $assist.do_teleport(
                    args,
                    function () {
                        // func_success
                    },
                    function (code, message) {
                        if (code === TPE_NO_ASSIST)
                            $assist.alert_assist_not_found(code);
                        else
                            $tp.notify_error('远程连接失败：' + tp_error_msg(code, message));
                    }
                );

            } else {
                $tp.notify_error('无法获取远程账号信息：' + tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $tp.notify_error('网络故障，无法获取远程账号信息！');
        }
    );
};

$app.create_dlg_ops_token = function () {
    let dlg = {};
    dlg.dom_id = 'dlg-ops-token';
    dlg.uni_id = '';
    dlg.acc_id = 0;
    dlg.user_token = '';
    dlg.temp_token = '';
    dlg.user_token_action = 'none';
    dlg.temp_token_action = 'none';
    dlg.user_token_info = null;
    dlg.temp_token_info = null;

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),

        target_name: $('#' + dlg.dom_id + ' [data-field="target-name"]'),
        target_acc: $('#' + dlg.dom_id + ' [data-field="target-acc"]'),
        target_protocol: $('#' + dlg.dom_id + ' [data-field="target-protocol"]'),
        remote_addr: $('#' + dlg.dom_id + ' [data-field="remote-addr"]'),
        remote_port: $('#' + dlg.dom_id + ' [data-field="remote-port"]'),

        user_token_state: $('#' + dlg.dom_id + ' [data-field="user-token-state"]'),
        btn_user_token_action: $('#btn-user-token-action'),
        btn_remove_user_token: $('#btn-remove-user-token'),
        block_user_token: $('#block-user-token'),
        user_acc: $('#' + dlg.dom_id + ' [data-field="user-acc"]'),

        // block_user_token_password: $('#block-user-token-password'),
        block_user_token_password_desc: $('#block-user-token-password-desc'),
        user_password: $('#' + dlg.dom_id + ' [data-field="user-password"]'),

        temp_token_state: $('#' + dlg.dom_id + ' [data-field="temp-token-state"]'),
        btn_temp_token_action: $('#btn-temp-token-action'),
        btn_remove_temp_token: $('#btn-remove-temp-token'),
        block_temp_token: $('#block-temp-token'),
        temp_acc: $('#' + dlg.dom_id + ' [data-field="temp-acc"]'),

        // block_temp_token_password: $('#block-temp-token-password'),
        block_temp_token_password_desc: $('#block-temp-token-password-desc'),
        block_temp_token_password_state: $('#block-temp-token-password-state'),
        btn_regenerate_temp_password: $('#btn-regenerate-temp-password'),
        temp_password: $('#' + dlg.dom_id + ' [data-field="temp-password"]'),
    };


    dlg.show = function (uni_id, target_name, target_addr, target_acc) {
        uni_id = uni_id || "";
        dlg.uni_id = uni_id;
        dlg.acc_id = target_acc.a_id;
        dlg.user_token = '';
        dlg.temp_token = '';
        dlg.user_token_action = 'none';
        dlg.temp_token_action = 'none';

        let _name = target_addr;
        if (target_name.length !== 0)
            _name += ' (' + target_name + ')';
        dlg.dom.target_name.text(_name);
        dlg.dom.target_acc.text(target_acc.a_name);

        dlg.dom.remote_addr.text(window.location.hostname);

        if (target_acc.protocol_type === TP_PROTOCOL_TYPE_RDP) {
            dlg.dom.target_protocol.text('RDP远程桌面');
            dlg.dom.remote_port.text($app.options.core_cfg.rdp.port);
        } else if (target_acc.protocol_type === TP_PROTOCOL_TYPE_SSH) {
            dlg.dom.target_protocol.text('SSH');
            dlg.dom.remote_port.text($app.options.core_cfg.ssh.port);
        } else if (target_acc.protocol_type === TP_PROTOCOL_TYPE_TELNET) {
            dlg.dom.target_protocol.text('TELNET');
            dlg.dom.remote_port.text($app.options.core_cfg.telnet.port);
        } else {
            dlg.dom.target_protocol.text('未知协议');
            $tp.notify_error('未知的远程协议，无法获取远程连接配置！');
            return;
        }

        dlg.dom.block_user_token.hide();
        dlg.dom.user_token_state.hide();
        dlg.dom.btn_user_token_action.hide();
        dlg.dom.btn_remove_user_token.hide();
        dlg.dom.block_temp_token.hide();
        dlg.dom.temp_token_state.hide();
        dlg.dom.btn_temp_token_action.hide();
        dlg.dom.btn_remove_temp_token.hide();

        dlg.dom.dialog.modal({backdrop: 'static'});

        $tp.ajax_post_json('/ops/get-ops-tokens',
            {uni_id: uni_id, acc_id: target_acc.a_id},
            function (ret) {
                if (ret.code === TPE_OK) {
                    dlg._update_token_info(ret.data);
                } else if (ret.code === TPE_NOT_EXISTS) {
                    dlg._update_token_info(null);
                } else {
                    $tp.notify_error('获取远程连接配置时发生错误：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，无法获取远程连接配置！');
            }
        );

    };

    dlg._update_token_info = function (tokens) {
        if (!tokens) {
            dlg._update_user_token_info(null);
            dlg._update_temp_token_info(null);
            return;
        }

        for (let i in tokens) {
            if (tokens[i].mode === TP_OPS_TOKEN_USER)
                dlg._update_user_token_info(tokens[i]);
            else if (tokens[i].mode === TP_OPS_TOKEN_TEMP)
                dlg._update_temp_token_info(tokens[i]);
            else
                $tp.notify_error('服务端返回了错误数据！');
        }
        if (!dlg.user_token_info)
            dlg._update_user_token_info(null);
        if (!dlg.temp_token_info)
            dlg._update_temp_token_info(null);
    };

    dlg._update_user_token_info = function (token_info) {
        if (!token_info) {
            dlg.user_token = '';
            dlg.user_token_info = null;
            dlg.user_token_action = 'create';

            // 尚未设置远程连接配置token
            dlg.dom.user_token_state.hide();
            dlg.dom.block_user_token.hide();
            dlg.dom.btn_user_token_action.html('<i class="fa fa-cog fa-fw"></i> 立即创建配置项');
            dlg.dom.btn_user_token_action.show();
            dlg.dom.btn_remove_user_token.hide();
        } else {
            dlg.user_token = token_info.token;
            dlg.user_token_info = token_info;
            dlg.user_token_action = 'renew_valid';

            // dlg.dom.block_remove.show();
            dlg.dom.user_acc.html(token_info.token);

            let now = tp_timestamp_sec();
            if (token_info.valid_to === 0 || now <= token_info.valid_to) {
                dlg.dom.user_token_state.html('有效期至 ' + tp_format_datetime(token_info.valid_to));
                dlg.dom.user_token_state.removeClass('badge-warning').addClass('badge-info');
                dlg.dom.btn_user_token_action.html('<i class="fa fa-clock fa-fw"></i> 延长有效期');
            } else {
                dlg.dom.user_token_state.html('已过期，有效期至 ' + tp_format_datetime(token_info.valid_to));
                dlg.dom.user_token_state.removeClass('badge-info').addClass('badge-warning');
                dlg.dom.btn_user_token_action.html('<i class="fa fa-redo fa-fw"></i> 重设有效期');
            }
            dlg.dom.user_token_state.show();
            dlg.dom.btn_user_token_action.show();
            dlg.dom.btn_remove_user_token.show();

            if (token_info._interactive) {
                dlg.dom.user_password.text('您的teleport密码--目标主机账号的密码');
                dlg.dom.block_user_token_password_desc.show();
            } else {
                dlg.dom.user_password.text('您的teleport密码');
                dlg.dom.block_user_token_password_desc.hide();
            }

            // dlg.dom.block_user_token_password.show();
            dlg.dom.block_user_token.show();
        }
    };

    dlg._update_temp_token_info = function (token_info) {
        if (!token_info) {
            dlg.temp_token = '';
            dlg.temp_token_info = null;
            dlg.temp_token_action = 'create';

            // 尚未设置远程连接配置token
            dlg.dom.temp_token_state.hide();
            dlg.dom.block_temp_token.hide();
            dlg.dom.btn_temp_token_action.html('<i class="fa fa-cog fa-fw"></i> 立即创建配置项');
            dlg.dom.btn_temp_token_action.show();
            dlg.dom.btn_remove_temp_token.hide();
        } else {
            dlg.temp_token = token_info.token;
            dlg.temp_token_info = token_info;
            dlg.temp_token_action = 'renew_valid';

            // dlg.dom.block_remove.show();
            dlg.dom.temp_acc.html(token_info.token);

            let now = tp_timestamp_sec();
            if (token_info.valid_to === 0 || now <= token_info.valid_to) {
                dlg.dom.temp_token_state.html('有效期至 ' + tp_format_datetime(token_info.valid_to));
                dlg.dom.temp_token_state.removeClass('badge-warning').addClass('badge-info');
                dlg.dom.btn_temp_token_action.html('<i class="fa fa-clock fa-fw"></i> 延长有效期');
            } else {
                dlg.dom.temp_token_state.html('已过期，有效期至 ' + tp_format_datetime(token_info.valid_to));
                dlg.dom.temp_token_state.removeClass('badge-info').addClass('badge-warning');
                dlg.dom.btn_temp_token_action.html('<i class="fa fa-redo fa-fw"></i> 重设有效期');
            }
            dlg.dom.temp_token_state.show();
            dlg.dom.btn_temp_token_action.show();
            dlg.dom.btn_remove_temp_token.show();

            dlg.dom.temp_password.text('');
            if (token_info._interactive) {
                if (!_.isUndefined(token_info._password)) {
                    dlg.dom.temp_password.text(token_info._password + '--目标主机账号的密码');
                    dlg.dom.btn_regenerate_temp_password.hide();
                    dlg.dom.block_temp_token_password_state.show();
                } else {
                    dlg.dom.btn_regenerate_temp_password.show();
                    dlg.dom.block_temp_token_password_state.hide();
                }
                dlg.dom.block_temp_token_password_desc.show();
            } else {
                if (!_.isUndefined(token_info._password)) {
                    dlg.dom.temp_password.text(token_info._password);
                    dlg.dom.btn_regenerate_temp_password.hide();
                    dlg.dom.block_temp_token_password_state.show();
                } else {
                    dlg.dom.btn_regenerate_temp_password.show();
                    dlg.dom.block_temp_token_password_state.hide();
                }
                dlg.dom.block_temp_token_password_desc.hide();
            }

            // dlg.dom.block_temp_token_password.show();
            dlg.dom.block_temp_token.show();
        }
    };

    dlg._on_create_token = function (mode) {
        $tp.ajax_post_json('/ops/create-ops-token',
            // mode: TP_OPS_TOKEN_USER=长期有效，例如一个月； TP_OPS_TOKEN_TEMP=临时有效，一般不超过7天。
            {mode: mode, uni_id: dlg.uni_id, acc_id: dlg.acc_id},
            function (ret) {
                if (ret.code === TPE_OK) {
                    if (mode === TP_OPS_TOKEN_USER)
                        dlg._update_user_token_info(ret.data);
                    else if (mode === TP_OPS_TOKEN_TEMP)
                        dlg._update_temp_token_info(ret.data);
                } else {
                    $tp.notify_error('创建远程连接配置时发生错误：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，无法创建远程连接配置！');
            }
        );
    };

    dlg._on_renew_token = function (mode, token) {
        $tp.ajax_post_json('/ops/renew-ops-token',
            // mode: TP_OPS_TOKEN_USER=长期有效，例如一个月； TP_OPS_TOKEN_TEMP=临时有效，一般不超过7天。
            {mode: mode, token: token, 'acc_id': dlg.acc_id},
            function (ret) {
                if (ret.code === TPE_OK) {
                    if (mode === TP_OPS_TOKEN_USER)
                        dlg._update_user_token_info(ret.data);
                    else if (mode === TP_OPS_TOKEN_TEMP)
                        dlg._update_temp_token_info(ret.data);
                } else {
                    $tp.notify_error('创建远程连接配置时发生错误：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，无法创建远程连接配置！');
            }
        );
    };

    dlg._on_remove_token = function (mode, token) {
        let _fn_sure = function (cb_stack, cb_args) {
            $tp.ajax_post_json('/ops/remove-ops-token',
                // mode: TP_OPS_TOKEN_USER=长期有效，例如一个月； TP_OPS_TOKEN_TEMP=临时有效，一般不超过7天。
                {token: token},
                function (ret) {
                    if (ret.code === TPE_OK) {
                        if (mode === TP_OPS_TOKEN_USER)
                            dlg._update_user_token_info(null);
                        else if (mode === TP_OPS_TOKEN_TEMP)
                            dlg._update_temp_token_info(null);
                    } else {
                        $tp.notify_error('创建删除远程连接配置时发生错误：' + tp_error_msg(ret.code, ret.message));
                    }

                    cb_stack.exec();
                },
                function () {
                    $tp.notify_error('网络故障，无法删除远程连接配置！');
                    cb_stack.exec();
                }
            );
        };

        let cb_stack = CALLBACK_STACK.create();
        let _msg_remove = '您确定要删除此项配置吗？';
        $tp.dlg_confirm(cb_stack, {
            msg: '<div class="alert alert-danger"><p><strong>注意：删除操作不可恢复！！</strong></p><p>删除远程连接配置后，使用此项配置的客户端将无法直接进行远程连接！但不影响通过页面进行远程连接。</p></div><p>' + _msg_remove + '</p>',
            fn_yes: _fn_sure
        });

    };

    dlg.dom.btn_user_token_action.click(function () {
        if (dlg.user_token_action === 'create') {
            dlg._on_create_token(TP_OPS_TOKEN_USER);
        } else if (dlg.user_token_action === 'renew_valid') {
            dlg._on_renew_token(TP_OPS_TOKEN_USER, dlg.user_token);
        }
    });

    dlg.dom.btn_remove_user_token.click(function () {
        dlg._on_remove_token(TP_OPS_TOKEN_USER, dlg.user_token);
    });

    dlg.dom.btn_temp_token_action.click(function () {
        if (dlg.temp_token_action === 'create') {
            dlg._on_create_token(TP_OPS_TOKEN_TEMP);
        } else if (dlg.temp_token_action === 'renew_valid') {
            dlg._on_renew_token(TP_OPS_TOKEN_TEMP, dlg.temp_token);
        }
    });

    dlg.dom.btn_remove_temp_token.click(function () {
        dlg._on_remove_token(TP_OPS_TOKEN_TEMP, dlg.temp_token);
    });

    dlg.dom.btn_regenerate_temp_password.click(function () {
        $tp.ajax_post_json('/ops/create-ops-token-temp-password',
            // mode: TP_OPS_TOKEN_USER=长期有效，例如一个月； TP_OPS_TOKEN_TEMP=临时有效，一般不超过7天。
            {token: dlg.temp_token, 'acc_id': dlg.acc_id},
            function (ret) {
                if (ret.code === TPE_OK) {
                    dlg._update_temp_token_info(ret.data);
                } else {
                    $tp.notify_error('生成临时密码时发生错误：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，无法生成临时密码！');
            }
        );
    });

    return dlg;
};
