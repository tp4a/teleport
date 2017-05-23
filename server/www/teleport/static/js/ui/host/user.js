"use strict";

//var OS_TYPE_WINDOWS = 1;
//var OS_TYPE_LINUX = 2;
//var PROTOCOL_TYPE_RDP = 1;
//var PROTOCOL_TYPE_SSH = 2;
//var PROTOCOL_TYPE_TELNET = 3;
//var AUTH_TYPE_PASSWORD = 1;
//var AUTH_TYPE_SSHKEY = 2;
//var AUTH_NONE = 0;

var g_assist = null;

ywl.on_init = function (cb_stack, cb_args) {
    var dom_id = '#ywl_host_list';
    g_assist = ywl.create_assist();

    var last_version = $("#tp-assist-version").text();
    var req_version = $("#tp-assist-version").attr("req-version");

    teleport_init(last_version, req_version,
        function (ret) {
            $("#tp-assist-current-version").text("当前助手版本：" + ret.version);
        },
        function (ret, code, error) {
            if (code == TPE_NO_ASSIST) {
                $("#tp-assist-current-version").text("未能检测到TP助手，请您下载并启动TP助手！")
                g_assist.alert_assist_not_found();
            }
            else if (code == TPE_OLD_ASSIST) {
                ywl.notify_error(error);
                $('#tp-assist-current-version').html('当前助手版本太低（v' + ret.version + '），请<a target="_blank" href="http://teleport.eomsoft.net/download">下载最新版本</a>!');
            }
            else {
                $("#tp-assist-current-version").text(error);
                ywl.notify_error(error);

                console.log('error:', error)
            }
        });

    //===================================
    // 创建页面控件对象
    //===================================
    // 表格数据
    var host_table_options = {
        selector: dom_id + " [ywl-table='host-list']",
        data_source: {
            type: 'ajax-post',
            url: '/host/list'
        },
        column_default: {sort: false, header_align: 'center', cell_align: 'center'},
        columns: [
            {title: "主机", key: "host_id", width: 240, render: 'host_id', fields: {id: 'host_ip', host_desc: 'host_desc', host_port: 'host_port'}},
            {title: "分组", key: "group_name", width: 180},
            {title: "系统", key: "host_sys_type", width: 64, render: 'sys_type', fields: {sys_type: 'host_sys_type'}},
            {title: "状态", key: "host_lock", width: 90, render: 'host_lock', fields: {host_lock: 'host_lock'}},
            {title: "远程连接", key: "auth_list", header_align: 'left', cell_align: 'left', render: 'auth_list', fields: {id: 'host_id', protocol: 'protocol', auth_list: 'auth_list'}},
//			{title: "", key: "padding"},
//			{title: "操作", key: "action", width: 160, render: 'make_action_btn', fields: {id: 'host_id'}}
        ],
        paging: {selector: dom_id + " [ywl-paging='host-list']", per_page: paging_normal},

        // 可用的属性设置
        //have_header: true or false

        // 可用的回调函数
        on_created: ywl.on_host_table_created,

        // 可重载的函数（在on_created回调函数中重载）
        // on_render_created
        // on_header_created
        // on_paging_created
        // on_data_loaded
        // on_row_rendered
        // on_table_rendered
        // on_cell_created
        // on_begin_load
        // on_after_load

        // 可用的函数
        // load_data
        // cancel_load
        // set_data
        // add_row
        // remove_row
        // get_row
        // update_row
        // clear
        // reset_filter
    };

    var host_table = ywl.create_table(host_table_options);

    // 主机分组过滤器
    ywl.create_table_filter_host_group(host_table, dom_id + " [ywl-filter='host-group']", ywl.page_options.group_list);

    ywl.create_table_filter_system_type(host_table, dom_id + " [ywl-filter='system-type']");
    // 搜索框
    ywl.create_table_filter_search_box(host_table, dom_id + " [ywl-filter='search']");

    //======================================================
    // 事件绑定
    //======================================================

    // 将刷新按钮点击事件绑定到表格的重新加载函数上，这样，点击刷新就导致表格数据重新加载。
    $(dom_id + " [ywl-filter='reload']").click(host_table.reload);

    cb_stack
        .add(host_table.load_data)
        .add(host_table.init)
        .exec();
};

// 扩展/重载表格的功能
ywl.on_host_table_created = function (tbl) {

    tbl.on_cell_created = function (row_id, col_key, cell_obj) {
        var row_data = tbl.get_row(row_id);
        if (col_key == 'host_pro_type') {
            console.log('row-data', row_data);
            $(cell_obj).find('[data-action="remote"]').click(function () {
                var ts_rdp_port = ywl.page_options.core.rdp_port;
                var ts_ssh_port = ywl.page_options.core.ssh_port;
                var port = 0;
                var pro_type = row_data.host_pro_type;
                if (pro_type === 1) {
                    port = ts_rdp_port;
                } else if (pro_type === 2) {
                    port = ts_ssh_port;
                } else {
                    return;
                }
                var args = {};
                args.auth_id = row_data.auth_id;
                args.server_ip = ywl.server_ip;
                args.port = port;
                args.pro_type = pro_type;
                args.pro_sub = $(this).attr('data-sub-protocol');
                args.host_ip = row_data.host_ip;
                args.size = 2;
                to_teleport(
                    '/host/get-session-id',
                    args,
                    function () {
                        console.log('远程连接建立成功！')
                    },
                    function (code, error) {
                        if (code == TPE_NO_ASSIST)
                            g_assist.alert_assist_not_found();
                        else {
                            ywl.notify_error(error);
                            console.log('error:', error)
                        }
                    }
                );
            });
        } else if (col_key == 'auth_list') {
//			console.log('row-data', row_data);
            $(cell_obj).find('[data-action="remote"]').click(function () {
                var ts_rdp_port = ywl.page_options.core.rdp_port;
                var ts_ssh_port = ywl.page_options.core.ssh_port;
                var ts_telnet_port = ywl.page_options.core.telnet_port;
//				console.log("row_data", row_data);
//				console.log('page-option', ywl.page_options);
                var pro_type = parseInt($(this).attr('data-protocol'));
                var pro_sub = parseInt($(this).attr('data-sub-protocol'));
                var auth_id = parseInt($(this).attr('auth-id'));
                var host_ip = row_data.host_ip;
                var server_port = 0;
                var size = 0;
                var rdp_console = 0;
                if (pro_type == 1) {
                    server_port = ts_rdp_port;
                    size = parseInt($(this).parent().parent().find('#dlg-rdp-size select').val())
                    if ($(this).parent().parent().find('#dlg-action-rdp-console').is(':checked')) {
                        rdp_console = 1;
                    } else {
                        rdp_console = 0;
                    }
                } else if (pro_type == 2) {
                    server_port = ts_ssh_port;
                } else if (pro_type == 3) {
                    server_port = ts_telnet_port;
                } else {
                    ywl.notify_error("未知的服务器端口号" + row_data.pro_port);
                    return;
                }
                var args = {};
                args.auth_id = auth_id;
                args.server_ip = ywl.server_ip;
                args.server_port = server_port;
                args.pro_type = pro_type;
                args.pro_sub = pro_sub;
                args.host_ip = host_ip;
                args.size = size;
                args.console = rdp_console;
//				console.log('args', args);
                to_teleport('/host/get-session-id', args,
                    function () {
                        console.log('远程连接建立成功！')
                    },
                    function (code, error) {
                        if (code == TPE_NO_ASSIST)
                            g_assist.alert_assist_not_found();
                        else {
                            ywl.notify_error(error);
                            console.log('error:', error)
                        }
                    }
                );
            });
        }
    };

    // 重载表格渲染器的部分渲染方式，加入本页面相关特殊操作
    tbl.on_render_created = function (render) {
        render.host_id = function (row_id, fields) {
            var ret = [];
            ret.push('<span class="host-id" href="javascript:;">' + fields.id + ':' + fields.host_port + '</span>');
            ret.push('<a class="host-desc" href="javascript:;" ywl-host-desc="' + fields.id + '">' + fields.host_desc + '</a>');
            return ret.join('');
        };

        render.auth_list = function (row_id, fields) {
            var auth_list = fields.auth_list;
            var ret = [];
            var protocol = fields.protocol;
            for (var i = 0; i < auth_list.length; i++) {
                var auth = auth_list[i];

                ret.push('<div class="remote-action-group">');
                ret.push('<ul>');

                if (auth.user_name.length > 0)
                    ret.push('<li class="remote-action-username">' + auth.user_name + '</li>');
                else
                    ret.push('<li class="remote-action-username">- 未指定 -</li>');

                switch (protocol) {
                    case PROTOCOL_TYPE_RDP:
                        ret.push('<li class="remote-action-btn"><a href="javascript:;" class="btn btn-primary" data-action="remote" auth-id=' + auth.auth_id + ' host-auth-id=' + auth.host_auth_id + ' data-protocol="1" data-sub-protocol="1"><i class="fa fa-desktop fa-fw"></i> RDP</a></li>');
                        ret.push('<li class="remote-action-input" id="dlg-rdp-size"><select>');
                        ret.push('<option value=1>800x600</option>');
                        ret.push('<option value=2 selected="selected">1024x768</option>');
                        ret.push('<option value=3>1280x1024</option>');
                        ret.push('<option value=0>全屏</option>');
                        ret.push('</select></li>');
                        ret.push('<li><label><input type="checkbox" id="dlg-action-rdp-console"> Console</label></li>');
                        break;
                    case PROTOCOL_TYPE_SSH:
                        ret.push('<li class="remote-action-btn"><a href="javascript:;" class="btn btn-sm btn-primary" data-action="remote"  auth-id=' + auth.auth_id + ' host-auth-id=' + auth.host_auth_id + ' data-protocol="2" data-sub-protocol="1"><i class="fa fa-keyboard-o fa-fw"></i> SSH</a></li>');
                        ret.push('<li class="remote-action-btn"><a href="javascript:;" class="btn btn-sm btn-success" data-action="remote" auth-id=' + auth.auth_id + ' host-auth-id=' + auth.host_auth_id + ' data-protocol="2" data-sub-protocol="2"><i class="fa fa-upload fa-fw"></i> SFTP</a></li>');
                        break;
                    case PROTOCOL_TYPE_TELNET:
                        ret.push('<li class="remote-action-btn"><a href="javascript:;" class="btn btn-sm btn-primary" data-action="remote"  auth-id=' + auth.auth_id + ' host-auth-id=' + auth.host_auth_id + ' data-protocol="3" data-sub-protocol="1"><i class="fa fa-keyboard-o fa-fw"></i> TELNET</a></li>');
                        break;
                    default:
                        ret.push('<li>未知协议类型</li>');
                }
                ret.push('</ul>');
                ret.push('</div>');
            }


            return ret.join('');
        };

        render.host_lock = function (row_id, fields) {
            switch (fields.host_lock) {
                case 0:
                    return '<span class="badge badge-success">正常</span>';
                case 1:
                    return '<span class="badge badge-danger">禁止连接</span>';
                default:
                    return '<span class="badge badge-danger">未知</span>';
            }
        };
        render.pro_type = function (row_id, fields) {
            switch (fields.pro_type) {
                case 1:
                    return '<a href="javascript:;" class="btn btn-sm btn-primary" data-action="remote" data-sub-protocol="1"><i class="fa fa-desktop fa-fw"></i> RDP</a>';
                case 2:
                    var ret = [];
                    ret.push('<div class="btn-group btn-group-sm" role="group">');
                    ret.push('<a href="javascript:;" class="btn btn-sm btn-primary" data-action="remote" data-sub-protocol="1"><i class="fa fa-keyboard-o fa-fw"></i> SSH</a>');
                    ret.push('<a href="javascript:;" class="btn btn-sm btn-success" data-action="remote" data-sub-protocol="2"><i class="fa fa-upload fa-fw"></i> SFTP</a>');
                    ret.push('</div>');
                    return ret.join('');
                default:
                    return '<span class="badge badge-danger">未知协议</span>';
            }
        };

        render.make_action_btn = function (row_id, fields) {
            var ret = [];

            ret.push('<div class="btn-group btn-group-sm">');
            ret.push('<a href="javascript:;" class="btn btn-primary" ywl-btn-action="' + fields.id + '"><i class="fa fa-desktop fa-fw"></i> 远程连接</a>');
            ret.push('</div>');
            return ret.join('');
        }

    };
};
