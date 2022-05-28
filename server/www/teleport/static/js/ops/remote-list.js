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
            } else if (action === 'get_config') {
                $app.get_remote_connection_config(acc_id, host_id);
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

        // console.log('acc', fields);
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
        // console.log('action', fields);

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

            if (!is_disabled) {
                h.push('<div class="remote-config">');
                h.push('<button type="button" class="btn btn-default" data-action="get_config" data-acc-id=' + acc.a_id + ' data-host-id=' + acc.h_id + '><i class="fa fa-key fa-fw"></i> 获取远程连接配置</button>');
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

$app.get_remote_connection_config = function (acc_id, host_id) {
    console.log(acc_id, host_id);
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
        args.extends({
            rdp_width: $app.dlg_rdp_options.rdp_w,
            rdp_height: $app.dlg_rdp_options.rdp_h,
            rdp_console: $app.dlg_rdp_options.rdp_console
        });
    }

    if (uni_id === 'none')
        args.mode = 2;

    // 根据acc_id判断此远程账号是否有预设密码，如果没有，则需要设置interactive模式。
    $tp.ajax_post_json('/asset/get-account-interactive-mode',
        {acc_id: acc_id},
        function (ret) {
            console.log('ajax: /asset/get-account-interactive-mode', ret);
            if (ret.code === TPE_OK) {
                args.is_interactive = ret.data.is_interactive;
                console.log('--s--', args);

                $assist.do_teleport(
                    args,
                    function () {
                        // func_success
                        //$tp.notify_success('远程连接测试通过！');
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
