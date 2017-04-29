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
var g_host_table = null;
var g_cert_list = [];
var g_group_list = [];
var g_dlg_edit_host = null;
var g_dlg_edit_host_user = null;
var g_dlg_sys_user = null;
var g_join_group_dlg = null;

ywl.do_upload_file = function () {
    var param = {};
    $.ajaxFileUpload({
        url: "/host/upload-import",// 需要链接到服务器地址
        secureuri: false,
        fileElementId: "upload-file", // 文件选择框的id属性
        dataType: 'text', // 服务器返回的格式，可以是json
        data: param,
        success: function (data) {
            $('#upload-file').remove();
            var ret = JSON.parse(data);
            if (ret.code === TPE_OK) {
                g_host_table.reload();
                ywl.notify_success('批量导入主机成功！');
                if (ret.data.msg.length > 0) {
                    var html = [];
                    html.push('<ul>');
                    for (var i = 0, cnt = ret.data.msg.length; i < cnt; ++i) {
                        html.push('<li>');
                        html.push('<span style="font-weight:bold;color:#993333;">' + ret.data.msg[i].reason + '</span><br/>');
                        html.push(ret.data.msg[i].line);
                        html.push('</li>');
                    }
                    html.push('</ul>');

                    $('#batch_add_host_result').html(html.join(''));
                    $('#dialog_batch_add_host').modal({backdrop: 'static'});
                }
            } else {
                ywl.notify_error('批量导入主机失败！ 错误号：' + ret.code);
            }
        },
        error: function () {
            $('#upload-file').remove();
            ywl.notify_error('网络故障，批量导入主机失败！');
        }
    });
};

ywl.on_init = function (cb_stack, cb_args) {

    g_assist = ywl.create_assist();

    var _ver_obj = $("#tp-assist-version");
    var last_version = _ver_obj.text();
    var req_version = _ver_obj.attr("req-version");

    teleport_init(last_version, req_version,
        function (ret) {
            $("#tp-assist-current-version").text("当前助手版本：" + ret.version);
        },
        function (ret, code, error) {
            if (code === TPE_NO_ASSIST) {
                $("#tp-assist-current-version").text("未能检测到TP助手，请您下载并启动TP助手！");
                g_assist.alert_assist_not_found();
            } else if (code === TPE_OLD_ASSIST) {
                ywl.notify_error(error);
                $('#tp-assist-current-version').html('当前助手版本太低（v' + ret.version + '），请<a target="_blank" href="http://teleport.eomsoft.net/download">下载最新版本</a>!');
            } else {
                $("#tp-assist-current-version").text('检测TP助手版本时发生错误！');
                ywl.notify_error(error);
            }
        });

    //===================================
    // 创建页面控件对象
    //===================================
    var tbl_dom_id = '#ywl_host_list';
    // 表格数据
    var host_table_options = {
        selector: tbl_dom_id + " [ywl-table='host-list']",
        data_source: {
            type: 'ajax-post',
            url: '/host/list'
        },
        //render: ywl.create_table_render(ywl.on_host_table_render_created),//ywl_TableRender.create();
        column_default: {sort: false, header_align: 'center', cell_align: 'center'},
        columns: [
            {
                title: '<input type="checkbox" id="host-select-all" value="">',
                key: 'select_all',
                sort: false,
                width: 24,
                render: 'make_check_box',
                fields: {id: 'host_id'}
            },
            {title: "主机", key: "host_id", width: 200, render: 'host_id', fields: {id: 'host_ip', host_port: 'host_port', host_desc: 'host_desc'}},
            {title: "分组", key: "group_name"},
            {title: "系统", key: "host_sys_type", width: 36, render: 'sys_type', fields: {sys_type: 'host_sys_type'}},
            // {title: "协议", key: "protocol", width: 40, render: 'protocol', fields: {protocol: 'protocol', host_port: 'host_port'}},
            {title: "状态", key: "host_lock", render: 'host_lock', fields: {host_lock: 'host_lock'}},
            {title: "远程连接", key: "auth_list", width: 390, header_align: 'left', cell_align: 'left', render: 'auth_list', fields: {id: 'host_id', protocol: 'protocol', auth_list: 'auth_list'}},
            {
                title: "系统用户",
                sort: false,
                key: "action",
                //width: 60,
                render: 'make_user_btn',
                fields: {id: 'host_id'}
            },
            {
                title: "操作",
                sort: false,
                key: "action",
                width: 150,
                render: 'make_action_btn',
                fields: {id: 'host_id', host_lock: 'host_lock'}
            }
        ],
        paging: {selector: tbl_dom_id + " [ywl-paging='host-list']", per_page: paging_normal},

        // 可用的属性设置
        //have_header: true or false

        // 可用的回调函数
        on_created: ywl.on_host_table_created,
        on_header_created: ywl.on_host_table_header_created

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
    g_host_table = host_table;
    // 主机分组过滤器
    g_cert_list = ywl.page_options.cert_list;
    g_group_list = ywl.page_options.group_list;
    ywl.create_table_filter_host_group(host_table, tbl_dom_id + " [ywl-filter='host-group']", g_group_list);

    ywl.create_table_filter_system_type(host_table, tbl_dom_id + " [ywl-filter='system-type']");
    // 搜索框
    ywl.create_table_filter_search_box(host_table, tbl_dom_id + " [ywl-filter='search']");

    g_dlg_edit_host = ywl.create_host_edit_dlg(host_table);
    g_dlg_edit_host.init();

    g_dlg_edit_host_user = ywl.create_host_user_edit_dlg(host_table);
    g_dlg_edit_host_user.init();


    g_dlg_sys_user = ywl.create_sys_user(host_table);
    g_dlg_sys_user.init();

    g_join_group_dlg = ywl.create_batch_join_group_dlg(host_table);
    g_join_group_dlg.init();


    //======================================================
    // 事件绑定
    //======================================================
    $("#btn-add-host").click(function () {
        g_dlg_edit_host.create_show();
    });

    $("#btn-delete-host").click(function () {
        var host_list = [];
        var _objs = $(host_table.selector + " tbody tr td [data-check-box]");
        $.each(_objs, function (i, _obj) {
            if ($(_obj).is(':checked')) {
                var _row_data = host_table.get_row(_obj);
                host_list.push(_row_data.host_id);
            }
        });

        if (host_list.length === 0) {
            ywl.notify_error('请选择要批量删除的主机！');
            return;
        }

        var _fn_sure = function (cb_stack, cb_args) {
            ywl.ajax_post_json('/host/delete-host', {host_list: host_list},
                function (ret) {
                    if (ret.code === TPE_OK) {
                        g_host_table.reload();
                        ywl.notify_success('删除主机操作成功！');
                    } else {
                        ywl.notify_error('删除主机操作失败：' + ret.message);
                    }
                },
                function () {
                    ywl.notify_error('网络故障，删除主机操作失败！');
                }
            );
        };

        var cb_stack = CALLBACK_STACK.create();
        ywl.dlg_confirm(cb_stack, {
            msg: '<p><strong>注意：移除操作不可恢复！！</strong></p><p>如果您只是希望临时禁用某个远程主机，可对其进行“锁定”操作！</p><p>您确定要移除所有选定的远程主机吗？</p>',
            fn_yes: _fn_sure
        });
    });

    $('#btn-batch-add-host').click(function (e) {
        var html = '<input id="upload-file" type="file" name="csvfile" class="hidden" value="" style="display: none;"/>';
        $(this).after($(html));
        var update_file = $("#upload-file");

        update_file.change(function () {
            var file_path = $(this).val();
            if (file_path === null || file_path === undefined || file_path === '') {
                return;
            }
            ywl.do_upload_file();
        });

        update_file.trigger('click');
    });

    $('#btn-batch-export-host').click(function (e) {
        window.location.href = '/host/export-host';
//		ywl.ajax_post_json('/host/export-host', {},
//			function (ret) {
//				console.log('ret', ret);
//				if (ret.code == 0) {
//					var url = ret.data.url;
//					window.location.href = url;
//					ywl.notify_success('操作成功');
//				} else {
//					ywl.notify_error('操作失败');
//				}
//			},
//			function () {
//				ywl.notify_error('操作失败');
//			}
//		);
    });

    $("#btn-apply-group").click(function () {
        var _data_list = [];
        var _objs = $(host_table.selector + " tbody tr td [data-check-box]");
        $.each(_objs, function (i, _obj) {
            if ($(_obj).is(':checked')) {
                var _row_data = host_table.get_row(_obj);
                var data = {host_id: _row_data.host_id, row_id: _row_data.ywl_row_id};
                _data_list.push(data);
            }
        });
        if (_data_list.length === 0) {
            ywl.notify_error('请选择要批量设置分组的主机！');
            return;
        }
        g_join_group_dlg.show(_data_list);
    });


    // 将刷新按钮点击事件绑定到表格的重新加载函数上，这样，点击刷新就导致表格数据重新加载。
    $(tbl_dom_id + " [ywl-filter='reload']").click(host_table.reload);

    cb_stack
        .add(host_table.load_data)
        .add(host_table.init)
        .exec();
};

// 扩展/重载表格的功能
ywl.on_host_table_created = function (tbl) {

    tbl.on_cell_created = function (row_id, col_key, cell_obj) {
        var row_data;

        if (col_key == 'select_all') {
            // 选择
            $('#host-select-' + row_id).click(function () {
                var _all_checked = true;
                var _objs = $(tbl.selector + ' tbody').find('[data-check-box]');
                $.each(_objs, function (i, _obj) {
                    if (!$(_obj).is(':checked')) {
                        _all_checked = false;
                        return false;
                    }
                });

                var select_all_dom = $('#host-select-all');
                if (_all_checked) {
                    select_all_dom.prop('checked', true);
                } else {
                    select_all_dom.prop('checked', false);
                }
            });

        } else if (col_key == 'host_id') {
            // 为主机描述绑定点击事件
            var _link = $(cell_obj).find(" [ywl-host-desc]");
            _link.click(function () {
                var row_data = tbl.get_row(row_id);
                ywl.create_dlg_modify_host_desc(tbl, row_data.ywl_row_id, row_data.host_id, row_data.host_ip, row_data.host_desc).show(_link);
            });
        } else if (col_key == 'action') {
            row_data = tbl.get_row(row_id);
            //console.log('row_data', row_data);
            $(cell_obj).find('[ywl-btn-edit]').click(function () {
                g_dlg_edit_host.update_show(row_id, row_data);
            });
            $(cell_obj).find('[ywl-btn-user-edit]').click(function () {
                g_dlg_edit_host_user.update_show(row_id, row_data);
            });

            $(cell_obj).find('[ywl-btn-lock]').click(function () {
                var host_id = row_data.host_id;
                var host_lock = row_data.host_lock;
                var message = '';
                if (host_lock === 0) {
                    host_lock = 1;
                    message = '确认要锁定该主机吗?';
                } else {
                    host_lock = 0;
                    message = '确认要解锁该主机吗?';
                }
                var _fn_sure = function (cb_stack, cb_args) {
                    ywl.ajax_post_json('/host/lock-host', {host_id: host_id, lock: host_lock},
                        function (ret) {
                            if (ret.code === TPE_OK) {
                                var update_args = {host_lock: host_lock};
                                tbl.update_row(row_id, update_args);
                                ywl.notify_success('锁定主机操作成功！');
                            } else {
                                ywl.notify_error('锁定主机操作失败：' + ret.message);
                            }
                        },
                        function () {
                            ywl.notify_error('网络故障，锁定主机操作失败！');
                        }
                    );
                };
                var cb_stack = CALLBACK_STACK.create();

                ywl.dlg_confirm(cb_stack,
                    {
                        msg: '<p>' + message + '</p>',
                        fn_yes: _fn_sure
                    });

            });

            $(cell_obj).find('[ywl-btn-delete]').click(function () {
                var host_id = row_data.host_id;
                var _fn_sure = function (cb_stack, cb_args) {
                    var host_list = [];
                    host_list.push(host_id);
                    ywl.ajax_post_json('/host/delete-host', {host_list: host_list},
                        function (ret) {
                            if (ret.code === TPE_OK) {
                                tbl.remove_row(row_id);
                                ywl.notify_success('删除主机操作成功！');
                            } else {
                                ywl.notify_error('删除主机操作失败：' + ret.message);
                            }
                        },
                        function () {
                            ywl.notify_error('网络故障，删除主机操作失败！');
                        }
                    );
                };
                var cb_stack = CALLBACK_STACK.create();

                ywl.dlg_confirm(cb_stack,
                    {
                        msg: '<p><strong>注意：移除操作不可恢复！！</strong></p><p>如果您只是希望临时禁用此主机，可以执行“锁定”操作！</p><p>您确定要移除此远程主机吗？</p>',
                        fn_yes: _fn_sure
                    });


            });

        } else if (col_key === 'auth_list') {
            row_data = tbl.get_row(row_id);
            $(cell_obj).find('[data-action="remote"]').click(function () {
                var ts_rdp_port = ywl.page_options.core.rdp_port;
                var ts_ssh_port = ywl.page_options.core.ssh_port;
                var ts_telnet_port = ywl.page_options.core.telnet_port;
                var host_ip = row_data.host_ip;
                var host_port = 0;
                var pro_type = parseInt($(this).attr('data-protocol'));
                var pro_sub = parseInt($(this).attr('data-sub-protocol'));
                var host_auth_id = parseInt($(this).attr('host-auth-id'));
                var size = 0;
                var rdp_console = 0;
                var pro_port;
                if (typeof row_data.pro_port === 'string') {
                    pro_port = $.parseJSON(row_data.pro_port);
                } else {
                    pro_port = row_data.pro_port;
                }


                if (pro_type === PROTOCOL_TYPE_RDP) {
                    host_port = ts_rdp_port;
                    size = parseInt($(this).parent().parent().find('#dlg-rdp-size select').val())
                    if ($(this).parent().parent().find('#dlg-action-rdp-console').is(':checked')) {
                        rdp_console = 1;
                    } else {
                        rdp_console = 0;
                    }
                } else if (pro_type === PROTOCOL_TYPE_SSH) {
                    host_port = ts_ssh_port;
                } else if (pro_type === PROTOCOL_TYPE_TELNET) {
                    host_port = ts_telnet_port;
                } else {
                    ywl.notify_error("未知的服务器端口号" + pro_port);
                    return;
                }
                var args = {};
                args.host_auth_id = host_auth_id;
                args.server_ip = ywl.server_ip;
                args.server_port = host_port;
                args.pro_type = pro_type;
                args.pro_sub = pro_sub;
                args.host_ip = host_ip;
                args.console = rdp_console;
                args.size = size;
                to_admin_teleport(
                    '/host/admin-get-session-id',
                    args,
                    function () {
                        console.log('远程连接建立成功！')
                    },
                    function (code, error) {
                        if (code === TPE_NO_ASSIST)
                            g_assist.alert_assist_not_found();
                        else {
                            ywl.notify_error(error);
                            console.log('error:', error)
                        }
                    }
                );
            });

            $(cell_obj).find('[data-action="remote-rdp-advance"]').click(function () {
                ywl.create_dlg_show_rdp_advance(row_data).show($(this));
            });
        }
    };

    // 重载表格渲染器的部分渲染方式，加入本页面相关特殊操作
    tbl.on_render_created = function (render) {

        render.host_id = function (row_id, fields) {
            var ret = [];
//			ret.push('<span class="host-id" href="javascript:;">' + fields.id + '<span class="badge badge-sm badge-sup" style="margin-left:-2px;margin-top:-14px">' + fields.host_port + '</span></span>');
            ret.push('<span class="host-id" href="javascript:;">' + fields.id + ':' + fields.host_port + '</span>');
            ret.push('<a class="host-desc" href="javascript:;" ywl-host-desc="' + fields.id + '">' + fields.host_desc + '</a>');
            return ret.join('');
        };

        render.protocol = function (row_id, fields) {
            var ret = [];
            switch (fields.protocol) {
                case 1:
                    return '<span class="badge badge-success">RDP:' + fields.host_port + '</span>';
                case 2:
                    return '<span class="badge badge-success">SSH:' + fields.host_port + '</span>';
                case 3:
                    return '<span class="badge badge-success">TELNET:' + fields.host_port + '</span>';
                default:
                    return '<span class="badge badge-danger">未知</span>';
            }
        };
        render.auth_list = function (row_id, fields) {

            var auth_list = fields.auth_list;
            var ret = [];
            if (auth_list.length === 0) {
                ret.push('<span class="badge badge-danger">尚未添加系统用户</span>');
                return ret.join('');
            }
            var protocol = fields.protocol;
            for (var i = 0; i < auth_list.length; i++) {
                var auth = auth_list[i];

                ret.push('<div class="remote-action-group">');
                ret.push('<ul>');

                if (auth.user_name.length > 0)
                    ret.push('<li class="remote-action-username">' + auth.user_name + '</li>');
                else
                    ret.push('<li class="remote-action-username">- 未指定 -</li>');

                if (auth.auth_mode === AUTH_TYPE_PASSWORD) {
                    ret.push('<li class="remote-action-password">密码</li>');
                } else if (auth.auth_mode === AUTH_TYPE_SSHKEY) {
                    ret.push('<li class="remote-action-sshkey">私钥</li>');
                } else if (auth.auth_mode === AUTH_NONE) {
                    ret.push('<li class="remote-action-noauth">无</li>');
                } else {
                    ret.push('<li class="remote-action-noauth">未知</li>');
                }

                switch (protocol) {
                    case PROTOCOL_TYPE_RDP:
                        ret.push('<li class="remote-action-btn"><a href="javascript:;" class="btn btn-primary" data-action="remote" host-auth-id=' + auth.host_auth_id + ' data-protocol="1" data-sub-protocol="1"><i class="fa fa-desktop fa-fw"></i> RDP</a></li>');
                        ret.push('<li class="remote-action-input" id="dlg-rdp-size"><select>');
                        ret.push('<option value=1>800x600</option>');
                        ret.push('<option value=2 selected="selected">1024x768</option>');
                        ret.push('<option value=3 >1280x1024</option>');
                        ret.push('<option value=0>全屏</option>');
                        ret.push('</select></li>');
                        ret.push('<li><label><input type="checkbox" id="dlg-action-rdp-console"> Console</label></li>');
                        break;
                    case PROTOCOL_TYPE_SSH:
                        ret.push('<li class="remote-action-btn"><a href="javascript:;" class="btn btn-sm btn-primary" data-action="remote" host-auth-id=' + auth.host_auth_id + ' data-protocol="2" data-sub-protocol="1"><i class="fa fa-keyboard-o fa-fw"></i> SSH</a></li>');
                        ret.push('<li class="remote-action-btn"><a href="javascript:;" class="btn btn-sm btn-success" data-action="remote" host-auth-id=' + auth.host_auth_id + ' data-protocol="2" data-sub-protocol="2"><i class="fa fa-upload fa-fw"></i> SFTP</a></li>');
                        break;
                    case PROTOCOL_TYPE_TELNET:
                        ret.push('<li class="remote-action-btn"><a href="javascript:;" class="btn btn-sm btn-primary" data-action="remote" host-auth-id=' + auth.host_auth_id + ' data-protocol="3" data-sub-protocol="1"><i class="fa fa-keyboard-o fa-fw"></i> TELNET</a></li>');
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
        render.make_check_box = function (row_id, fields) {
            return '<span><input type="checkbox" data-check-box="' + fields.id + '" id="host-select-' + row_id + '"></span>';
        };
        render.make_action_btn = function (row_id, fields) {
            var ret = [];
            ret.push('<div class="btn-group btn-group-sm" role="group">');
            ret.push('<a href="javascript:;" class="btn btn-sm btn-primary" ywl-btn-edit="' + fields.id + '"><i class="fa fa-edit fa-fw"></i> 编辑</a>');
//			if (fields.host_lock === 0)
//				ret.push('<a href="javascript:;" class="btn btn-sm btn-warning" ywl-btn-lock="' + fields.id + '"><i class="fa fa-lock fa-fw"></i> 锁定</a>');
//			else
//				ret.push('<a href="javascript:;" class="btn btn-sm btn-success" ywl-btn-lock="' + fields.id + '"><i class="fa fa-unlock fa-fw"></i> 解锁</a>');

            ret.push('<a href="javascript:;" class="btn btn-sm btn-danger" ywl-btn-delete="' + fields.id + '"><i class="fa fa-trash-o fa-fw"></i> 移除</a>');

//            ret.push('<a href="javascript:;" class="btn btn-sm btn-primary" ywl-btn-remote="' + fields.id + '"><i class="fa fa-desktop fa-fw"></i> 远程</a>');
            ret.push('</div>');
            return ret.join('');
        };
        render.make_user_btn = function (row_id, fields) {
            var ret = [];
            ret.push('<div class="btn-group btn-group-sm" role="group">');
            ret.push('<a href="javascript:;" class="btn btn-sm btn-success" ywl-btn-user-edit="' + fields.id + '">用户管理</a>');
            ret.push('</div>');
            return ret.join('');
        }
    };
};

ywl.on_host_table_header_created = function (tbl) {
    $('#host-select-all').click(function () {
        var _is_selected = $(this).is(':checked');
        $(tbl.selector + ' tbody').find('[data-check-box]').prop('checked', _is_selected);
    });
};

ywl.create_host_edit_dlg = function (tbl) {
    var dlg_edit_host = {};
    dlg_edit_host.dom_id = "#dialog-host-edit";
    dlg_edit_host.update = 0;
    dlg_edit_host.tbl = tbl;
    dlg_edit_host.host_id = 0;
    dlg_edit_host.row_id = "";
    dlg_edit_host.sys_type = 1;
    dlg_edit_host.group_id = 0;
    dlg_edit_host.group_name = '默认分组';
    dlg_edit_host.host_desc = '';
    dlg_edit_host.ip = '';
    dlg_edit_host.protocol = 0;
    dlg_edit_host.host_port = 0;
//	dlg_edit_host.pro_port = {};

    dlg_edit_host.init = function () {
        $('#auth-sys-type').change(dlg_edit_host.on_sys_type_change);
        $('#host-protocol-type').change(dlg_edit_host.on_protocol_change);
//		$('#auth-protocol-type').change(dlg_edit_host.on_protocol_change);
//		$('#auth-auth-type').change(dlg_edit_host.on_auth_type_change);

//		$("#dlg-edit-host-allow-ssh").change(dlg_edit_host.on_ssh_allow);
//		$("#dlg-edit-host-allow-rdp").change(dlg_edit_host.on_rdp_allow);
//
//		$("#dlg-edit-host-ssh-port").change(dlg_edit_host.on_ssh_port);
//		$("#dlg-edit-host-rdp-port").change(dlg_edit_host.on_rdp_port);


        var obj_group = $('#dlg-edit-host-group');
        obj_group.change(dlg_edit_host.on_group_change);

        var i, cnt;
        // 分组选择
        var html_group = [];
        html_group.push('<option value="0">默认分组</option>');
        for (i = 0, cnt = g_group_list.length; i < cnt; ++i) {
            html_group.push('<option value="' + g_group_list[i].id + '">' + g_group_list[i].group_name + '</option>');
        }
        obj_group.append($(html_group.join('')));
        // 对话框按钮事件绑定

        $("#host-btn-save").click(function () {
            if (!dlg_edit_host.check_args())
                return;
            //console.log("dlg_edit_host");
            if (dlg_edit_host.update === 1) {
                dlg_edit_host.update_post();
            } else {
                dlg_edit_host.create_post();
            }
//
        });

//		// SSH密钥选择
//		var html_sshkey = [];
//		for (i = 0, cnt = g_cert_list.length; i < cnt; ++i) {
//			html_sshkey.push('<option value="' + g_cert_list[i].cert_id + '">' + g_cert_list[i].cert_name + '</option>');
//		}
//		$('#auth-sshkey-list').append($(html_sshkey.join('')));


//		// 对话框按钮事件绑定
//		$("#test-btn-connect").click(function () {
//			if (!dlg_edit_host.check_args())
//				return;
//			if (dlg_edit_host.update === 1) {
//				dlg_edit_host.update_connect();
//			} else {
//				dlg_edit_host.create_connect();
//			}
//
//		});
//
//
//		$("#btn-add-user").click(function () {
//			$('#dialog_test').modal({backdrop: 'static'});
//		});

    };
    dlg_edit_host.on_sys_type_change = function () {
        dlg_edit_host.sys_type = parseInt($('#auth-sys-type').val());
        if (dlg_edit_host.sys_type === OS_TYPE_WINDOWS) {// && dlg_edit_host.protocol === 0) {
            dlg_edit_host.protocol = PROTOCOL_TYPE_RDP;
        }
        else if (dlg_edit_host.sys_type === OS_TYPE_LINUX) {// && dlg_edit_host.protocol === 0) {
            dlg_edit_host.protocol = PROTOCOL_TYPE_SSH;
        }

        $('#host-protocol-type').val(dlg_edit_host.protocol);

        dlg_edit_host.on_protocol_change();
    };

    dlg_edit_host.on_protocol_change = function () {
        dlg_edit_host.protocol = parseInt($('#host-protocol-type').val());
        if (dlg_edit_host.protocol === PROTOCOL_TYPE_RDP)
            $('#dlg-edit-host-protocol-port').val('3389');
        else if (dlg_edit_host.protocol === PROTOCOL_TYPE_SSH)
            $('#dlg-edit-host-protocol-port').val('22');
        else if (dlg_edit_host.protocol === PROTOCOL_TYPE_TELNET)
            $('#dlg-edit-host-protocol-port').val('23');
        else
            $('#dlg-edit-host-protocol-port').val(0);
    };

    dlg_edit_host.on_group_change = function () {
        //console.log('group-change.');
        var obj = $('#group-host-group');
        dlg_edit_host.group_id = parseInt(obj.val());
        dlg_edit_host.group_name = obj.find('option:selected').text();
    };


    dlg_edit_host.init_dlg = function (row_id, args) {
        if (dlg_edit_host.update === 1) {
            dlg_edit_host.sys_type = args.host_sys_type;
            dlg_edit_host.ip = args.host_ip;
            dlg_edit_host.host_id = args.host_id;
            dlg_edit_host.group_id = args.group_id;
            dlg_edit_host.host_desc = args.host_desc;
            dlg_edit_host.protocol = args.protocol;
            dlg_edit_host.host_port = args.host_port;
            dlg_edit_host.init_fields();
            dlg_edit_host.row_id = row_id;
        } else {
            // 新建主机默认设置
            dlg_edit_host.host_id = 0;
            dlg_edit_host.row_id = "";
            dlg_edit_host.sys_type = OS_TYPE_LINUX;
            dlg_edit_host.ip = '';
            dlg_edit_host.group_id = 0;
            dlg_edit_host.group_name = '默认分组';
            dlg_edit_host.host_desc = '';
            dlg_edit_host.protocol = 0;
            dlg_edit_host.host_port = 0;
            dlg_edit_host.init_fields();
        }
    };

    dlg_edit_host.clear_fields = function () {
        $("#auth-host-ip").val('');
        $("#auth-host-desc").val('');
        $('#auth-sys-type').val(OS_TYPE_LINUX);
    };

    dlg_edit_host.init_fields = function () {
        dlg_edit_host.clear_fields();

        $('#auth-sys-type').val(dlg_edit_host.sys_type);
        dlg_edit_host.on_sys_type_change();

        $("#auth-host-ip").val(dlg_edit_host.ip);
        $("#auth-host-desc").val(dlg_edit_host.host_desc);

        var obj_group = $('#dlg-edit-host-group');
        obj_group.val(dlg_edit_host.group_id);

        if (dlg_edit_host.host_port !== 0) {
            $("#dlg-edit-host-protocol-port").val(dlg_edit_host.host_port);
        }
    };

    dlg_edit_host.check_args = function () {
        dlg_edit_host.sys_type = parseInt($('#auth-sys-type').val());
        var obj_group = $('#dlg-edit-host-group');
        dlg_edit_host.group_id = parseInt(obj_group.val());
        dlg_edit_host.group_name = obj_group.find('option:selected').text();
        dlg_edit_host.ip = $("#auth-host-ip").val();

        dlg_edit_host.host_desc = $("#auth-host-desc").val();

        dlg_edit_host.host_port = $("#dlg-edit-host-protocol-port").val();
        if (dlg_edit_host.ip.length === 0) {
            ywl.notify_error('请设定远程主机的地址！');
            return false;
        }

        if (dlg_edit_host.host_port.length === 0) {
            ywl.notify_error('请设定协议端口号！');
            return false;
        }
        return true;
    };

    dlg_edit_host.update_show = function (row_id, args) {
        dlg_edit_host.update = 1;
        dlg_edit_host.init_dlg(row_id, args);
        $(dlg_edit_host.dom_id).modal({backdrop: 'static'});
    };

    dlg_edit_host.create_show = function () {
        dlg_edit_host.update = 0;
        dlg_edit_host.init_dlg();
        $(dlg_edit_host.dom_id).modal({backdrop: 'static'});
    };

    dlg_edit_host.hide = function () {
        $(dlg_edit_host.dom_id).modal('hide');
    };

    dlg_edit_host.update_post = function () {
        var host_sys_type = parseInt(dlg_edit_host.sys_type);
        var protocol = parseInt(dlg_edit_host.protocol);
        var host_port = parseInt(dlg_edit_host.host_port);
        var host_ip = dlg_edit_host.ip;
        var host_id = dlg_edit_host.host_id;
        var args = {
            group_id: dlg_edit_host.group_id,
            host_sys_type: host_sys_type,
            host_ip: host_ip,
            protocol: protocol,
            host_port: host_port,
            host_desc: dlg_edit_host.desc
        };
        ywl.ajax_post_json('/host/update', {host_id: host_id, kv: args},
            function (ret) {
                if (ret.code === TPE_OK) {
                    var update_args = {
                        host_ip: dlg_edit_host.ip,
                        group_name: dlg_edit_host.group_name,
                        group_id: dlg_edit_host.group_id,
                        host_desc: dlg_edit_host.host_desc,
                        host_sys_type: dlg_edit_host.sys_type,
                        protocol: protocol,
                        host_port: host_port
                    };

                    dlg_edit_host.tbl.update_row(dlg_edit_host.row_id, update_args);
                    ywl.notify_success('主机 ' + dlg_edit_host.ip + ' 信息已保存！');
                    dlg_edit_host.hide();
                } else {
                    ywl.notify_error('主机 ' + self.host_ip + ' 信息更新失败：' + ret.message);
                }
            },
            function () {
                ywl.notify_error('网络故障，主机 ' + self.host_ip + ' 信息更新失败！');
            }
        );
    };

    dlg_edit_host.create_post = function () {
        var protocol = parseInt(dlg_edit_host.protocol);
        var host_port = parseInt(dlg_edit_host.host_port);

        var args = {
            host_ip: dlg_edit_host.ip,
            host_port: host_port,
            protocol: protocol,
            host_sys_type: dlg_edit_host.sys_type,
            group_id: dlg_edit_host.group_id,
            host_desc: dlg_edit_host.host_desc
        };

        ywl.ajax_post_json('/host/add-host', args,
            function (ret) {
                if (ret.code === TPE_OK) {
                    dlg_edit_host.tbl.reload();
                    ywl.notify_success('主机 ' + dlg_edit_host.ip + ' 信息已添加！');
                    dlg_edit_host.hide();
                }
                else {
                    if (ret.code === -100) {
                        ywl.notify_error('主机 ' + dlg_edit_host.ip + ' 已存在，请不要重复添加主机！');
                    } else {
                        ywl.notify_error('主机 ' + dlg_edit_host.ip + ' 信息保存失败！' + ret.message);
                    }

                }
            },
            function () {
                ywl.notify_error('网络故障，主机 ' + dlg_edit_host.ip + ' 信息保存失败！', '');
            }
        );
    };

    return dlg_edit_host;
};

ywl.create_host_user_edit_dlg = function (tbl) {
    var dlg_user_edit_host = {};
    dlg_user_edit_host.dom_id = "#dialog-host-user-edit";
    dlg_user_edit_host.update = 0;
    dlg_user_edit_host.tbl = tbl;
    dlg_user_edit_host.host_id = 0;
    dlg_user_edit_host.row_id = "";
    dlg_user_edit_host.host_ip = '';
    dlg_user_edit_host.pro_port = {};

    dlg_user_edit_host.auth_list = [];

    dlg_user_edit_host.init = function () {

        $("#host-user-btn-save").click(function () {
            dlg_user_edit_host.hide();
        });

    };

    dlg_user_edit_host.create_user_html = function (host_auth_id, index, user_name, pro_name, auth_name) {
        if (user_name.length === 0)
            user_name = '- 未指定 -';
        var html = [];
        html.push('<div class="remote-action-group" id =' + "user-auth-id-" + host_auth_id + '"><ul>');
        html.push('<li class="remote-action-name">' + user_name + ' </li>');
        html.push('<li class="remote-action-protocol">' + pro_name + '</li>');
        html.push('<li class="remote-action-noauth">' + auth_name + '</li>');
        html.push('<li class="remote-action-btn">');
        html.push('<button type="button" class="btn btn-sm btn-primary"  user-data-action="modify" id =' + "user-modify-btn-" + host_auth_id + '" data-sub-protocol="1" index=' + index + '><i class="fa fa-edit fa-fw"></i> 修改</button>');
        html.push('</li><li class="remote-action-btn">');
        html.push('<button type="button" class="btn btn-sm btn-danger" user-data-action="delete" auth-id=' + host_auth_id + ' data-sub-protocol="2" index=' + index + '><i class="fa fa-trash-o fa-fw"></i> 删除</button>');
        html.push('</li></ul></div>');
        return html.join('');
    };

    dlg_user_edit_host.sync_user_info = function (host_id) {
        ywl.ajax_post_json('/host/sys-user/list', {host_id: host_id},
            function (ret) {
                if (ret.code !== TPE_OK) {
                    ywl.notify_error('获取主机用户列表失败：' + ret.message);
                    return;
                }

                var data = ret.data;

                dlg_user_edit_host.auth_list = data;
                var update_args = {
                    auth_list: dlg_user_edit_host.auth_list
                };

                dlg_user_edit_host.tbl.update_row(dlg_user_edit_host.row_id, update_args);
                var row_data = tbl.get_row(dlg_user_edit_host.row_id);
                var protocol = row_data.protocol;
                var arr = dlg_user_edit_host.auth_list;
                var html = "";

                for (var i = 0; i < arr.length; i++) {

                    var user_name = arr[i].user_name;
                    var host_auth_id = arr[i].host_auth_id;
                    var pro_name = '未知';
                    if (protocol === PROTOCOL_TYPE_RDP) {
                        pro_name = 'RDP';
                    } else if (protocol === PROTOCOL_TYPE_SSH) {
                        pro_name = 'SSH';
                    } else if (protocol === PROTOCOL_TYPE_TELNET) {
                        pro_name = 'TELNET';
                    }
                    var auth_name = "未知";
                    if (arr[i].auth_mode === AUTH_NONE) {
                        auth_name = '无';
                    } else if (arr[i].auth_mode === AUTH_TYPE_PASSWORD) {
                        auth_name = '密码';
                    } else if (arr[i].auth_mode === AUTH_TYPE_SSHKEY) {
                        auth_name = '私钥';
                    }
                    html += dlg_user_edit_host.create_user_html(host_auth_id, i, user_name, pro_name, auth_name);
                }
                html += '<button type="button" class="btn btn-sm btn-primary" id="btn-add-sys-user"><i class="fa fa-plus fa-fw"></i> 添加登录账号</button>';
                $("#sys-user-list").html(html);

                $("#btn-add-sys-user").click(function () {
                    var row_data = tbl.get_row(dlg_user_edit_host.row_id);
                    g_dlg_sys_user.create_show(row_data);
                });

                $('[user-data-action="modify"]').click(function () {
                    var index = parseInt($(this).attr("index"));
                    var data = dlg_user_edit_host.auth_list[index];
                    var row_data = tbl.get_row(dlg_user_edit_host.row_id);
                    g_dlg_sys_user.update_show(row_data, data);
                });
                $('[user-data-action="delete"]').click(function () {
                    var host_auth_id = parseInt($(this).attr("auth-id"));
                    ywl.ajax_post_json('/host/sys-user/delete', {host_auth_id: host_auth_id},
                        function (ret) {
                            if (ret.code === TPE_OK) {
                                ywl.notify_success('系统用户删除成功！');
                                g_dlg_edit_host_user.sync_user_info(host_id);
                            } else {
                                ywl.notify_error('系统用户删除失败：' + ret.message);
                            }
                        },
                        function () {
                            ywl.notify_error('网络故障：系统用户删除失败！');
                        }
                    );
                });
            },
            function () {
                ywl.notify_error('网络故障，无法获取远程主机认证信息！');
            }
        );
    };
    dlg_user_edit_host.init_dlg = function (row_id, args) {
        dlg_user_edit_host.row_id = row_id;
        if (dlg_user_edit_host.update === 1) {
            var host_id = args.host_id;
            dlg_user_edit_host.host_ip = args.host_ip;
            dlg_user_edit_host.pro_port = args.pro_port;

            dlg_user_edit_host.sync_user_info(host_id);
        }
    };

    dlg_user_edit_host.clear_fields = function () {

    };

    dlg_user_edit_host.init_fields = function () {

    };

    dlg_user_edit_host.check_args = function () {
        return true;
    };

    dlg_user_edit_host.update_show = function (row_id, args) {
        dlg_user_edit_host.update = 1;
        dlg_user_edit_host.init_dlg(row_id, args);
        $(dlg_user_edit_host.dom_id).modal({backdrop: 'static'});
    };

    dlg_user_edit_host.create_show = function () {
        dlg_user_edit_host.update = 0;
        dlg_user_edit_host.init_dlg();
        $(dlg_user_edit_host.dom_id).modal({backdrop: 'static'});
    };

    dlg_user_edit_host.hide = function () {
        $(dlg_user_edit_host.dom_id).modal('hide');
    };

    return dlg_user_edit_host;
};

ywl.create_sys_user = function (tbl) {

    var dlg_sys_user = {};
    dlg_sys_user.dom_id = "#dialog_user";
    dlg_sys_user.update = 0;
    dlg_sys_user.tbl = tbl;
    dlg_sys_user.row_id = '';
    dlg_sys_user.sys_type = 0;
    dlg_sys_user.host_id = 0;
    dlg_sys_user.host_ip = '';
    dlg_sys_user.auth_mode = 0;
    dlg_sys_user.protocol = 0;
    dlg_sys_user.host_auth_id = 0;
    dlg_sys_user.user_name = '';
    dlg_sys_user.user_pswd = '';
    dlg_sys_user.cert_id = 0;
    dlg_sys_user.user_param = '';


    dlg_sys_user.init = function () {
        dlg_sys_user.update = 0;
        dlg_sys_user.host_id = 0;
        dlg_sys_user.host_ip = '';
        dlg_sys_user.sys_type = 0;
        dlg_sys_user.auth_mode = 1;
        dlg_sys_user.host_auth_id = 0;
        dlg_sys_user.user_name = '';
        dlg_sys_user.user_pswd = '';
        dlg_sys_user.cert_id = 0;
        dlg_sys_user.protocol = 0;
        dlg_sys_user.host_port = 0;

        $("#sys-user-btn-save").click(function () {
            if (!dlg_sys_user.check_args())
                return;

            if (dlg_sys_user.update === 1) {
                dlg_sys_user.update_post();
            } else {
                dlg_sys_user.create_post();
            }
        });
        $("#test-btn-connect").click(function () {
            if (!dlg_sys_user.check_args())
                return;

            var ts_rdp_port = ywl.page_options.core.rdp_port;
            var ts_ssh_port = ywl.page_options.core.ssh_port;
            var ts_telnet_port = ywl.page_options.core.telnet_port;
            var server_port = 0;
            var host_port = dlg_sys_user.host_port;
            var protocol = dlg_sys_user.protocol;
            if (protocol === PROTOCOL_TYPE_RDP) {
                server_port = ts_rdp_port;
            } else if (protocol === PROTOCOL_TYPE_SSH) {
                server_port = ts_ssh_port;
            } else if (protocol === PROTOCOL_TYPE_TELNET) {
                server_port = ts_telnet_port;
            } else {
                ywl.notify_error('未知协议！');
                return;
            }

            var args = {};
            args.server_ip = ywl.server_ip;
            args.server_port = parseInt(server_port);
            args.host_port = parseInt(host_port);
            args.protocol = parseInt(protocol);
            args.protocol_sub = 1;
            args.sys_type = parseInt(dlg_sys_user.sys_type);
            args.host_ip = dlg_sys_user.host_ip;
            args.auth_mode = parseInt(dlg_sys_user.auth_mode);
            args.user_name = dlg_sys_user.user_name;
            args.user_pswd = dlg_sys_user.user_pswd;
            args.cert_id = dlg_sys_user.cert_id;
            args.host_auth_id = dlg_sys_user.host_auth_id;
            args.user_param = dlg_sys_user.user_param;
            args.size = 2;
            to_admin_fast_teleport(
                '/host/admin-fast-get-session-id',
                args,
                function () {
                    console.log('远程连接建立成功！')
                },
                function (code, error) {
                    if (code === TPE_NO_ASSIST)
                        g_assist.alert_assist_not_found();
                    else {
                        ywl.notify_error(error);
                        console.log('error:', error)
                    }
                }
            );

        });


//		// SSH密钥选择
        var html_sshkey = [];
        var i, cnt = 0;
        for (i = 0, cnt = g_cert_list.length; i < cnt; ++i) {
            html_sshkey.push('<option value="' + g_cert_list[i].cert_id + '">' + g_cert_list[i].cert_name + '</option>');
        }
        $('#auth-user-sshkey-list').append($(html_sshkey.join('')));
    };

    dlg_sys_user.init_dlg = function (row_data, args) {
        dlg_sys_user.row_id = row_data.row_id;
        dlg_sys_user.host_id = row_data.host_id;
        dlg_sys_user.host_ip = row_data.host_ip;
        dlg_sys_user.sys_type = row_data.host_sys_type;
        dlg_sys_user.protocol = row_data.protocol;
        dlg_sys_user.host_port = row_data.host_port;
        if (dlg_sys_user.update === 1) {
            dlg_sys_user.auth_mode = args.auth_mode;
            dlg_sys_user.host_auth_id = args.host_auth_id;
            dlg_sys_user.user_name = args.user_name;
            dlg_sys_user.user_pswd = args.user_pswd;
            dlg_sys_user.cert_id = args.cert_id;
            dlg_sys_user.user_param = args.user_param;
            if (dlg_sys_user.user_param.length === 0)
                dlg_sys_user.user_param = 'ogin:\nassword:';

            $('#auth-user-host-pswd').attr('placeholder', '不填写则使用已存储的密码');
        } else {
            if (dlg_sys_user.sys_type === OS_TYPE_WINDOWS) {
                dlg_sys_user.user_name = 'administrator';
            } else if (dlg_sys_user.sys_type === OS_TYPE_LINUX) {
                dlg_sys_user.user_name = 'root';
            } else {
                dlg_sys_user.user_name = '';
            }
            dlg_sys_user.auth_mode = 1;
            dlg_sys_user.host_auth_id = 0;
            dlg_sys_user.user_pswd = '';
            dlg_sys_user.cert_id = 0;
            dlg_sys_user.user_param = 'ogin:\nassword:';
            $('#auth-user-host-pswd').attr('placeholder', '请输入登录远程主机的密码');
        }
        dlg_sys_user.init_fields();
    };

    dlg_sys_user.clear_fields = function () {

    };

    dlg_sys_user.init_fields = function () {

        var info;
        var combox_html = [];
        if (dlg_sys_user.protocol === PROTOCOL_TYPE_RDP) {
            info = "RDP协议";
            $('#auth-user-block-telnet').hide();
            combox_html.push('<select id="auth-user-type" class="form-control">');
            combox_html.push('<option value="1">用户名/密码 认证</option>');
            combox_html.push('<option value="0">无需认证</option>');
            combox_html.push('</select>');
        } else if (dlg_sys_user.protocol === PROTOCOL_TYPE_SSH) {
            info = "SSH协议";
            $('#auth-user-block-telnet').hide();
            combox_html.push('<select id="auth-user-type" class="form-control">');
            combox_html.push('<option value="1">用户名/密码 认证</option>');
            combox_html.push('<option value="2">SSH私钥 认证</option>');
            combox_html.push('</select>');
        } else if (dlg_sys_user.protocol === PROTOCOL_TYPE_TELNET) {
            info = "TELNET协议";
            $('#auth-user-block-telnet').show();
            combox_html.push('<select id="auth-user-type" class="form-control">');
            combox_html.push('<option value="1">用户名/密码 认证</option>');
            combox_html.push('<option value="0">无需认证</option>');
            combox_html.push('</select>');

            var user_param = dlg_sys_user.user_param.split("\n");
            var param1 = '';
            var param2 = '';
            if (user_param.length === 1) {
                param1 = user_param[0];
            } else if (user_param.length === 2) {
                param1 = user_param[0];
                param2 = user_param[1];
            }

            $('#auth-user-telnet-username-prompt').val(param1);
            $('#auth-user-telnet-pswd-prompt').val(param2);
        } else {
            info = "未知协议";
        }

        $('#auth-sys-user-type-combox').html(combox_html.join(''));
        $('#auth-user-type').change(dlg_sys_user.on_user_auth_mode_change);
        $('#auth-user-protocol-type').text(info);

        info = dlg_sys_user.host_ip + ':' + dlg_sys_user.host_port;
        $('#add-user-host-ip').text(info);
        $('#auth-user-type').val(dlg_sys_user.auth_mode);
        $('#auth-user-host-username').val(dlg_sys_user.user_name);

        if (dlg_sys_user.auth_mode === AUTH_TYPE_PASSWORD) {
            $('#auth-user-block-name').show();
            $('#auth-user-block-pswd').show();
            $('#auth-user-block-sshkey').hide();
            $('#auth-user-host-pswd').val("");
            $('#auth-user-host-pswd-confirm').val("");
        } else if (dlg_sys_user.auth_mode === AUTH_TYPE_SSHKEY) {
            $('#auth-user-block-name').show();
            $('#auth-user-block-pswd').hide();
            $('#auth-user-block-sshkey').show();
            var cert_id = parseInt(dlg_sys_user.cert_id);
            $('#auth-user-sshkey-list').val(cert_id);
        } else if (dlg_sys_user.auth_mode === AUTH_NONE) {
            $('#auth-user-block-telnet').hide();
            $('#auth-user-block-pswd').hide();
            $('#auth-user-block-name').hide();
            $('#auth-user-block-sshkey').hide();
        }
    };

    dlg_sys_user.on_user_auth_mode_change = function () {
        dlg_sys_user.auth_mode = parseInt($('#auth-user-type').val());
        if (dlg_sys_user.auth_mode === AUTH_TYPE_PASSWORD) {
            if (dlg_sys_user.protocol === PROTOCOL_TYPE_RDP) {

            } else if (dlg_sys_user.protocol === PROTOCOL_TYPE_SSH) {

            } else if (dlg_sys_user.protocol === PROTOCOL_TYPE_TELNET) {
                $('#auth-user-block-telnet').show();
            }
            $('#auth-user-block-pswd').show();
            $('#auth-user-block-name').show();
            $('#auth-user-block-sshkey').hide();
        } else if (dlg_sys_user.auth_mode === AUTH_TYPE_SSHKEY) {
            $('#auth-user-block-telnet').hide();
            $('#auth-user-block-pswd').hide();
            $('#auth-user-block-sshkey').show();
            $('#auth-user-block-name').show();
        } else if (dlg_sys_user.auth_mode === AUTH_NONE) {
            $('#auth-user-block-telnet').hide();
            $('#auth-user-block-pswd').hide();
            $('#auth-user-block-name').hide();
            $('#auth-user-block-sshkey').hide();
        }
    };

    dlg_sys_user.check_args = function () {

        dlg_sys_user.auth_mode = parseInt($('#auth-user-type').val());
        dlg_sys_user.user_name = $('#auth-user-host-username').val();
        if (dlg_sys_user.auth_mode !== AUTH_NONE &&
            dlg_sys_user.user_name.length === 0) {
            ywl.notify_error('请输入系统用户名！');
            return false;
        }

        if (dlg_sys_user.auth_mode === AUTH_TYPE_PASSWORD) {
            if (dlg_sys_user.update !== 1) {
                var temp1 = $('#auth-user-host-pswd').val();
                var temp2 = $('#auth-user-host-pswd-confirm').val();
                if (temp1.length === 0) {
                    ywl.notify_error('请输入密码！');
                    return false;
                }
                if (temp2.length === 0) {
                    ywl.notify_error('请输入确认密码！');
                    return false;
                }
                if (temp1 !== temp2) {
                    ywl.notify_error('两次密码输入不一致！');
                    return false;
                }
                dlg_sys_user.user_pswd = temp1;
            } else {
                var temp1 = $('#auth-user-host-pswd').val();
                var temp2 = $('#auth-user-host-pswd-confirm').val();
                if (temp1 !== temp2) {
                    ywl.notify_error('两次密码输入不一致！');
                    return false;
                }
                dlg_sys_user.user_pswd = temp1;
            }
            if (dlg_sys_user.protocol === PROTOCOL_TYPE_TELNET) {
                var param1 = $('#auth-user-telnet-username-prompt').val();
                var param2 = $('#auth-user-telnet-pswd-prompt').val();
                dlg_sys_user.user_param = param1 + "\n" + param2;
            }

        } else if (dlg_sys_user.auth_mode === AUTH_TYPE_SSHKEY) {
            dlg_sys_user.cert_id = $('#auth-user-sshkey-list').val();
        } else if (dlg_sys_user.auth_mode === AUTH_NONE) {
            dlg_sys_user.user_name = '';
            dlg_sys_user.user_pswd = '';
            dlg_sys_user.cert_id = 0;
        } else {
            ywl.notify_error('未知认证模式！');
            return false;
        }
        return true;
    };

    dlg_sys_user.update_show = function (row_id, args) {
        dlg_sys_user.update = 1;
        dlg_sys_user.init_dlg(row_id, args);
        $(dlg_sys_user.dom_id).modal({backdrop: 'static'});
    };

    dlg_sys_user.create_show = function (row_data) {
        dlg_sys_user.update = 0;
        dlg_sys_user.init_dlg(row_data);
        $(dlg_sys_user.dom_id).modal({backdrop: 'static'});
    };

    dlg_sys_user.hide = function () {
        $(dlg_sys_user.dom_id).modal('hide');
    };

    dlg_sys_user.update_post = function () {
        var auth_mode = parseInt(dlg_sys_user.auth_mode);
        var user_pswd = '';
        var cert_id = 0;
        if (auth_mode === AUTH_TYPE_PASSWORD) {
            user_pswd = dlg_sys_user.user_pswd;
        } else if (auth_mode === AUTH_TYPE_SSHKEY) {
            cert_id = parseInt(dlg_sys_user.cert_id);
        } else {

        }
        var host_id = parseInt(dlg_sys_user.host_id);
        var host_auth_id = parseInt(dlg_sys_user.host_auth_id);
        var args = {
            auth_mode: auth_mode,
            host_id: host_id,
            user_name: dlg_sys_user.user_name,
            user_pswd: user_pswd,
            cert_id: cert_id,
            user_param: dlg_sys_user.user_param
        };

        ywl.ajax_post_json('/host/sys-user/update', {host_auth_id: host_auth_id, kv: args},
            function (ret) {
                if (ret.code === TPE_OK) {
                    ywl.notify_success('系统用户信息更新成功！');
                    g_dlg_edit_host_user.sync_user_info(host_id);
                    dlg_sys_user.hide();
                } else {
                    ywl.notify_error('系统用户信息更新失败：' + ret.message);
                }
            },
            function () {
                ywl.notify_error('网络故障，系统用户信息更新失败！');
            }
        );
    };

    dlg_sys_user.create_post = function () {
        if (!dlg_sys_user.check_args()) {
            ywl.notify_error("参数输入有错误");
            return;
        }
        var auth_mode = parseInt(dlg_sys_user.auth_mode);
        var user_pswd = '';
        var cert_id = 0;
        if (auth_mode === AUTH_TYPE_PASSWORD) {
            user_pswd = dlg_sys_user.user_pswd;
        } else {
            cert_id = parseInt(dlg_sys_user.cert_id);
        }
        var host_id = parseInt(dlg_sys_user.host_id);
        var args = {
            host_id: host_id,
            auth_mode: auth_mode,
            user_name: dlg_sys_user.user_name,
            user_pswd: user_pswd,
            cert_id: cert_id,
            user_param: dlg_sys_user.user_param
        };

        ywl.ajax_post_json('/host/sys-user/add', args,
            function (ret) {
                if (ret.code === TPE_OK) {
                    ywl.notify_success('系统用户添加成功！');
                    g_dlg_edit_host_user.sync_user_info(host_id);
                    dlg_sys_user.hide();
                } else {
                    ywl.notify_error('系统用户添加失败：' + ret.message);
                }
            },
            function () {
                ywl.notify_error('网络故障，系统用户信息更新失败！');
            }
        );
    };

    return dlg_sys_user;

};

ywl.create_batch_join_group_dlg = function (tbl) {
    var batch_join_dlg = {};

    batch_join_dlg.tbl = tbl;
    batch_join_dlg.dom_id = "#dialog_batch_join_group";
    batch_join_dlg.host_list = [];

    batch_join_dlg.init = function () {
        // 分组选择
        var html_group = [];
        html_group.push('<option value="0">默认分组</option>');
        for (var i = 0, cnt = g_group_list.length; i < cnt; ++i) {
            html_group.push('<option value="' + g_group_list[i].id + '">' + g_group_list[i].group_name + '</option>');
        }
        $('#group-host-group').append($(html_group.join('')));


        batch_join_dlg.init_dlg();
    };

    batch_join_dlg.init_dlg = function () {
    };

    batch_join_dlg.check_args = function () {
        return true;
    };

    batch_join_dlg.show = function (data_list) {
        batch_join_dlg.host_list = data_list;
        $(batch_join_dlg.dom_id).modal({backdrop: 'static'});
    };

    batch_join_dlg.hide = function () {
        $(batch_join_dlg.dom_id).modal('hide');
    };

    batch_join_dlg.post = function () {

        var data_list = [];
        for (var i = 0; i < batch_join_dlg.host_list.length; i++) {
            var host_id = batch_join_dlg.host_list[i].host_id;
            data_list.push(host_id);
        }

        var obj = $('#group-host-group');
        var group_id = parseInt(obj.val());
        var group_name = obj.find('option:selected').text();

        ywl.ajax_post_json('/host/add-host-to-group', {host_list: data_list, group_id: group_id},
            function (ret) {
                if (ret.code === TPE_OK) {
                    var update_args = {group_name: group_name};
                    for (var i = 0; i < batch_join_dlg.host_list.length; i++) {
                        var row_id = batch_join_dlg.host_list[i].row_id;
                        batch_join_dlg.tbl.update_row(row_id, update_args);
                    }

                    ywl.notify_success("成功设定主机分组信息！");
                    batch_join_dlg.hide();
                } else {
                    ywl.notify_error("设定主机分组信息失败：" + ret.message);
                }
            },
            function () {
                ywl.notify_error("网络故障，设定主机分组信息失败！");
            }
        );
    };

    $("#group-btn-save").click(function () {
        if (!batch_join_dlg.check_args()) {
            return;
        }
        batch_join_dlg.post();
    });

    return batch_join_dlg;
};
