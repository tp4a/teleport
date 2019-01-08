"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        btn_refresh_host: $('#btn-refresh-host'),
        btn_add_host: $('#btn-add-host'),
        chkbox_host_select_all: $('#table-host-select-all'),

        btn_lock_host: $('#btn-lock-host'),
        btn_unlock_host: $('#btn-unlock-host'),
        btn_remove_host: $('#btn-remove-host'),

        dlg_import_asset: $('#dlg-import-asset'),
        btn_import_asset: $('#btn-import-asset'),
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
    // 主机列表表格
    //-------------------------------
    var table_host_options = {
        dom_id: 'table-host',
        data_source: {
            type: 'ajax-post',
            url: '/asset/get-hosts'
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
                title: '主机',
                key: 'ip',
                sort: true,
                header_render: 'filter_search',
                render: 'host_info',
                fields: {id: 'id', ip: 'ip', router_ip: 'router_ip', router_port: 'router_port', name: 'name', desc: 'desc'}
            },
            {
                title: '系统',
                key: 'os_type',
                align: 'center',
                width: 36,
                sort: true,
                // header_render: 'filter_os',
                render: 'os_type',
                fields: {os_type: 'os_type'}
            },
            {
                title: '资产编号',
                key: 'cid',
                // align: 'center',
                // width: 36,
                sort: true
                // header_render: 'filter_os',
                // render: 'sys_type',
                // fields: {: 'os'}
            },
            {
                title: '账号数',
                key: 'acc_count',
                render: 'account',
                fields: {count: 'acc_count'}
            },
            {
                title: "状态",
                key: "state",
                sort: true,
                width: 90,
                align: 'center',
                header_render: 'filter_state',
                render: 'host_state',
                fields: {state: 'state'}
            },
            {
                title: '',
                key: 'action',
                sort: false,
                align: 'center',
                width: 70,
                render: 'make_host_action_btn',
                fields: {id: 'id', state: 'state'}
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
    // 主机列表相关过滤器
    //-------------------------------
    $tp.create_table_header_filter_search($app.table_host, {
        name: 'search',
        place_holder: '搜索：主机IP/名称/描述/资产编号/等等...'
    });
    // $app.table_host_role_filter = $tp.create_table_filter_role($app.table_host, $app.role_list);
    // 主机没有“临时锁定”状态，因此要排除掉
    $tp.create_table_header_filter_state($app.table_host, 'state', $app.obj_states, [TP_STATE_LOCKED]);

    $tp.create_table_filter_group($app.table_host, 'host_group', '#filter-host-group', $app.options.host_groups);

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
    $app.dlg_edit_host = $app.create_dlg_edit_host();
    cb_stack.add($app.dlg_edit_host.init);
    $app.dlg_accounts = $app.create_dlg_accounts();
    cb_stack.add($app.dlg_accounts.init);
    $app.dlg_edit_account = $app.create_dlg_edit_account();
    cb_stack.add($app.dlg_edit_account.init);

    //-------------------------------
    // 页面控件事件绑定
    //-------------------------------
    $app.dom.btn_add_host.click(function () {
        $app.dlg_edit_host.show_add();
    });
    $app.dom.btn_refresh_host.click(function () {
        $app.table_host.load_data();
    });
    $app.dom.btn_select_file.click($app.on_btn_select_file_click);
    $app.dom.btn_do_upload.click($app.on_btn_do_upload_click);
    $app.dom.btn_import_asset.click(function () {
        $app.dom.upload_file_info.html('- 尚未选择文件 -');
        $app.dom.btn_do_upload.hide();
        $app.dom.upload_file_message.html('').hide();
        $app.dom.dlg_import_asset.modal({backdrop: 'static'});
    });
    $app.dom.chkbox_host_select_all.click(function () {
        var _objects = $('#' + $app.table_host.dom_id + ' tbody').find('[data-check-box]');
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
    $app.dom.btn_lock_host.click(function () {
        $app.on_btn_lock_host_click();
    });
    $app.dom.btn_unlock_host.click(function () {
        $app.on_btn_unlock_host_click();
    });
    $app.dom.btn_remove_host.click(function () {
        $app.on_btn_remove_host_click();
    });

    cb_stack.exec();
};


//-------------------------------
// 主机表格相关
//-------------------------------

$app.on_table_host_cell_created = function (tbl, row_id, col_key, cell_obj) {
    if (col_key === 'chkbox') {
        cell_obj.find('[data-check-box]').click(function () {
            $app.check_host_all_selected();
        });
    } else if (col_key === 'action') {
        // 绑定系统选择框事件
        cell_obj.find('[data-action]').click(function () {
            var host = $app.table_host.get_row(row_id);
            var action = $(this).attr('data-action');
            if (action === 'edit') {
                $app.dlg_edit_host.show_edit(row_id);
            } else if (action === 'account') {
                $app.dlg_accounts.show(row_id);
            } else if (action === 'lock') {
                $app._lock_hosts([host.id]);
            } else if (action === 'unlock') {
                $app._unlock_hosts([host.id]);
            } else if (action === 'remove') {
                $app._remove_hosts([host.id]);
            } else if (action === 'duplicate') {
                $app._duplicate_host(host.id);
            }
        });
    } else if (col_key === 'ip') {
        cell_obj.find('[data-toggle="popover"]').popover({trigger: 'hover'});
        // } else if (col_key === 'account') {
        //     cell_obj.find('[data-action="add-account"]').click(function () {
        //         $app.dlg_accounts.show(row_id);
        //     });
    } else if (col_key === 'acc_count') {
        cell_obj.find('[data-action="edit-account"]').click(function () {
            $app.dlg_accounts.show(row_id);
        });
    }
};

$app.on_table_host_render_created = function (render) {

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
        return '<span><input type="checkbox" data-check-box="' + fields.id + '" data-row-id="' + row_id + '"></span>';
    };

    render.host_info = function (row_id, fields) {
        var title, sub_title;

        title = fields.name;
        sub_title = fields.ip;

        if (title.length === 0) {
            title = fields.ip;
        }

        var desc = [];
        if (fields.desc.length > 0) {
            desc.push(fields.desc.replace(/\r/ig, "").replace(/\n/ig, "<br/>"));
        }
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

    // render.os = function (row_id, fields) {
    //     return fields.os;
    // };
    //

    render.account = function (row_id, fields) {
        return '<a href="javascript:;" data-action="edit-account"><i class="fa fa-edit fa-fw"></i></a> ' + fields.count;
    };

    render.host_state = function (row_id, fields) {
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

    render.make_host_action_btn = function (row_id, fields) {
        var h = [];
        h.push('<div class="btn-group btn-group-sm">');
        h.push('<button type="button" class="btn btn-no-border dropdown-toggle" data-toggle="dropdown">');
        h.push('<span data-selected-action>操作</span> <i class="fa fa-caret-right"></i></button>');
        h.push('<ul class="dropdown-menu dropdown-menu-right dropdown-menu-sm">');
        h.push('<li><a href="javascript:;" data-action="edit"><i class="fa fa-edit fa-fw"></i> 编辑</a></li>');
        h.push('<li><a href="javascript:;" data-action="lock"><i class="fa fa-lock fa-fw"></i> 禁用</a></li>');
        h.push('<li><a href="javascript:;" data-action="unlock"><i class="fa fa-unlock fa-fw"></i> 解禁</a></li>');
        h.push('<li role="separator" class="divider"></li>');
        h.push('<li><a href="javascript:;" data-action="account"><i class="fa fa-user-secret fa-fw"></i> 管理远程账号</a></li>');
        h.push('<li role="separator" class="divider"></li>');
        h.push('<li><a href="javascript:;" data-action="duplicate"><i class="fa fa-cubes fa-fw"></i> 复制主机</a></li>');
        h.push('<li><a href="javascript:;" data-action="remove"><i class="fa fa-times-circle fa-fw"></i> 删除</a></li>');
        h.push('</ul>');
        h.push('</div>');

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
    header._table_ctrl.get_filter_ctrl('state').on_created();
};

$app.check_host_all_selected = function (cb_stack) {
    var _all_checked = true;
    var _objs = $('#' + $app.table_host.dom_id + ' tbody').find('[data-check-box]');
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
        $app.dom.chkbox_host_select_all.prop('checked', true);
    } else {
        $app.dom.chkbox_host_select_all.prop('checked', false);
    }

    if (cb_stack)
        cb_stack.exec();
};

$app.on_btn_select_file_click = function () {

    var html = '<input id="file-selector" type="file" name="csvfile" accept=".csv,text/csv,text/comma-separated-values" class="hidden" value="" style="display: none;"/>';
    $('body').after($(html));
    var btn_file_selector = $("#file-selector");

    btn_file_selector.change(function () {
        $app.dom.upload_file_message.hide();
        // var dom_file_name = $('#upload-file-name');

        var file = null;
        if (btn_file_selector[0].files && btn_file_selector[0].files[0]) {
            file = btn_file_selector[0].files[0];
        } else if (btn_file_selector[0].files && btn_file_selector[0].files.item(0)) {
            file = btn_file_selector[0].files.item(0);
        }

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
        url: "/asset/upload-import",// 需要链接到服务器地址
        fileElementId: "file-selector", // 文件选择框的id属性
        timeout: 60000,
        secureuri: false,
        dataType: 'text',
        data: param,
        success: function (data) {
            console.log(data);
            $('#file-selector').remove();

            var ret = JSON.parse(data);
            console.log(ret);

            if (ret.code === TPE_OK) {
                $app.dom.upload_file_message
                    .removeClass('alert-info')
                    .addClass('alert-success')
                    .html('<i class="far fa-check-square fa-fw"></i> 资产导入成功：' + ret.message);

                $app.table_host.load_data();
            } else {
                var err_msg = ['<i class="far fa-times-circle fa-fw"></i> 资产导入失败：' + ret.message];
                if (!_.isUndefined(ret.data)) {
                    err_msg.push('<div style="max-height:280px;overflow:auto;margin-left:20px;">');
                    var err_lines = [];
                    $.each(ret.data, function (i, item) {
                        err_lines.push('第' + item.line + '行：' + item.error);
                    });
                    err_msg.push(err_lines.join('<br/>'));
                    err_msg.push('</div>');

                    $app.table_host.load_data();
                }

                $app.dom.upload_file_message
                    .removeClass('alert-info')
                    .addClass('alert-danger')
                    .html(err_msg.join(''));
            }
        },
        error: function () {
            $('#file-selector').remove();
            $tp.notify_error('网络故障，批量导入资产失败！');
        }
    });
};

$app.show_user_info = function (row_id) {
    $app.dlg_user_info.show(row_id);
};

$app.get_selected_host = function (tbl) {
    var items = [];
    var _objs = $('#' + $app.table_host.dom_id + ' tbody tr td input[data-check-box]');
    $.each(_objs, function (i, _obj) {
        if ($(_obj).is(':checked')) {
            var _row_data = tbl.get_row(_obj);
            // _all_checked = false;
            items.push(_row_data.id);
        }
    });
    return items;
};

$app._lock_hosts = function (host_ids) {
    $tp.ajax_post_json('/asset/update-hosts', {action: 'lock', hosts: host_ids},
        function (ret) {
            if (ret.code === TPE_OK) {
                $app.table_host.load_data();
                $tp.notify_success('禁用主机操作成功！');
            } else {
                $tp.notify_error('禁用主机操作失败：' + tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $tp.notify_error('网络故障，禁用主机操作失败！');
        }
    );
};

$app.on_btn_lock_host_click = function () {
    var items = $app.get_selected_host($app.table_host);
    if (items.length === 0) {
        $tp.notify_error('请选择要禁用的主机！');
        return;
    }

    $app._lock_hosts(items);
};

$app._unlock_hosts = function (host_ids) {
    $tp.ajax_post_json('/asset/update-hosts', {action: 'unlock', hosts: host_ids},
        function (ret) {
            if (ret.code === TPE_OK) {
                $app.table_host.load_data();
                $tp.notify_success('解禁主机操作成功！');
            } else {
                $tp.notify_error('解禁主机操作失败：' + tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $tp.notify_error('网络故障，解禁主机操作失败！');
        }
    );
};

$app.on_btn_unlock_host_click = function () {
    var items = $app.get_selected_host($app.table_host);
    if (items.length === 0) {
        $tp.notify_error('请选择要解禁的主机！');
        return;
    }

    $app._unlock_hosts(items);
};

$app._remove_hosts = function (host_ids) {
    var _fn_sure = function (cb_stack) {
        $tp.ajax_post_json('/asset/update-hosts', {action: 'remove', hosts: host_ids},
            function (ret) {
                if (ret.code === TPE_OK) {
                    cb_stack.add($app.check_host_all_selected);
                    cb_stack.add($app.table_host.load_data);
                    $tp.notify_success('删除主机操作成功！');
                } else {
                    $tp.notify_error('删除主机操作失败：' + tp_error_msg(ret.code, ret.message));
                }

                cb_stack.exec();
            },
            function () {
                $tp.notify_error('网络故障，删除主机操作失败！');
                cb_stack.exec();
            }
        );
    };

    var cb_stack = CALLBACK_STACK.create();
    $tp.dlg_confirm(cb_stack, {
        msg: '<div class="alert alert-danger"><p><strong>注意：删除操作不可恢复！！</strong></p><p>删除主机将同时删除与之相关的账号，并将主机和账号从所在分组中移除，同时删除所有相关授权！</p></div><p>如果您希望临时禁止登录指定主机，可将其“禁用”！</p><p>您确定要移除选定的' + host_ids.length + '个主机吗？</p>',
        fn_yes: _fn_sure
    });
};

$app.on_btn_remove_host_click = function () {
    var items = $app.get_selected_host($app.table_host);
    if (items.length === 0) {
        $tp.notify_error('请选择要删除的主机！');
        return;
    }

    $app._remove_hosts(items);
};

$app.create_dlg_edit_host = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-edit-host';
    dlg.field_id = -1;  // 主机id（仅编辑模式）
    // dlg.field_type = -1;
    dlg.field_os_type = -1;
    dlg.field_ip = '';
    dlg.field_conn_mode = -1;
    dlg.field_router_ip = '';
    dlg.field_router_port = 0;
    dlg.field_name = '';
    dlg.field_cid = '';
    dlg.field_desc = '';

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        dlg_title: $('#' + dlg.dom_id + ' [data-field="dlg-title"]'),
        hlp_conn_mode: $('#help-host-conn-mode'),
        hlp_cid: $('#help-host-cid'),
        // select_type: $('#edit-host-type'),
        edit_os_type: $('#edit-host-os-type'),
        edit_ip: $('#edit-host-ip'),
        edit_conn_mode: $('#edit-host-conn-mode'),
        block_router_mode: $('#block-router-mode'),
        edit_router_ip: $('#edit-host-router-ip'),
        edit_router_port: $('#edit-host-router-port'),
        edit_name: $('#edit-host-name'),
        edit_cid: $('#edit-host-cid'),
        edit_desc: $('#edit-host-desc'),
        msg: $('#edit-host-message'),
        btn_save: $('#btn-edit-host-save'),
    };

    dlg.init = function (cb_stack) {
        var html = [];
        // // 创建类型选择框
        // html.push('<button type="button" class="btn btn-sm dropdown-toggle" data-toggle="dropdown">');
        // html.push('<span data-selected-type>选择主机类型</span> <i class="fa fa-caret-right"></i></button>');
        // html.push('<ul class="dropdown-menu dropdown-menu-sm">');
        // $.each($app.host_types, function (i, t) {
        //     html.push('<li><a href="javascript:;" data-type-selector="' + t.id + '"><i class="fa fa-angle-right fa-fw"></i> ' + t.name + '</a></li>');
        // });
        // html.push('</ul>');
        // dlg.dom.select_type.after($(html.join('')));
        // dlg.dom.selected_type = $('#' + dlg.dom_id + ' span[data-selected-type]');
        //
        // // 绑定类型选择框事件
        // $('#' + dlg.dom_id + ' li a[data-type-selector]').click(function () {
        //     var select = parseInt($(this).attr('data-type-selector'));
        //     if (dlg.field_type === select)
        //         return;
        //     var name = $app.id2name($app.host_types, select);
        //     if (_.isUndefined(name)) {
        //         name = '选择主机类型角色';
        //         dlg.field_type = -1;
        //     } else {
        //         dlg.field_type = select;
        //     }
        //
        //     dlg.dom.selected_type.text(name);
        // });

        // 创建系统选择框
        // html.push('<button type="button" class="btn btn-sm dropdown-toggle" data-toggle="dropdown">');
        // html.push('<span data-selected-os>选择操作系统</span> <i class="fa fa-caret-right"></i></button>');
        // html.push('<ul class="dropdown-menu dropdown-menu-sm">');
        // $.each($app.host_os, function (i, t) {
        //     html.push('<li><a href="javascript:;" data-os-selector="' + t.id + '"><i class="fa fa-angle-right fa-fw"></i> ' + t.name + '</a></li>');
        // });
        // html.push('</ul>');

        // html.push('<option value="-1">请选择远程主机操作系统</option>');
        $.each($app.host_os_type, function (i, t) {
            html.push('<option value="' + t.id + '">' + t.name + '</option>');
        });

        dlg.dom.edit_os_type.append(html.join(''));
        // dlg.dom.selected_os = $('#' + dlg.dom_id + ' span[data-selected-os]');

        dlg.dom.edit_conn_mode.change(dlg.on_conn_mode_change);

        dlg.dom.btn_save.click(dlg.on_save);

        dlg.dom.hlp_conn_mode.popover({trigger: 'hover'});
        dlg.dom.hlp_cid.popover({trigger: 'hover'});

        cb_stack.exec();
    };

    dlg.init_fields = function (host) {
        // var type_name = '选择主机类型';
        // dlg.field_type = -1;
        // var os_name = '选择操作系统';
        dlg.field_id = -1;
        dlg.field_os_type = -1;

        if (_.isUndefined(host)) {
            dlg.dom.dlg_title.html('添加主机');

            dlg.dom.edit_ip.val('');
            dlg.dom.edit_conn_mode.val('0');
            dlg.dom.edit_router_ip.val('');
            dlg.dom.edit_router_port.val('');
            dlg.dom.edit_name.val('');
            dlg.dom.edit_cid.val('');
            dlg.dom.edit_desc.val('');
        } else {
            dlg.field_id = host.id;
            dlg.dom.dlg_title.html('编辑主机：');

            var _name = $app.id2name($app.host_os_type, host.os_type);
            if (!_.isUndefined(_name)) {
                // os_name = _name;
            }
            dlg.field_os_type = host.os_type;

            if (host.router_ip.length > 0) {
                dlg.dom.edit_router_ip.val(host.router_ip);
                dlg.dom.edit_router_port.val(host.router_port);
                dlg.dom.edit_conn_mode.val('1');
            } else {
                dlg.dom.edit_conn_mode.val('0');
            }

            dlg.dom.edit_ip.val(host.ip);
            dlg.dom.edit_name.val(host.name);
            dlg.dom.edit_cid.val(host.cid);
            dlg.dom.edit_desc.val(host.desc);
        }
        // dlg.dom.selected_type.text(type_name);
        // dlg.dom.selected_os.text(os_name);
        dlg.dom.edit_os_type.val('' + dlg.field_os_type);
        dlg.on_conn_mode_change();
    };

    dlg.on_conn_mode_change = function () {
        if (dlg.dom.edit_conn_mode.val() === '0') {
            dlg.dom.block_router_mode.hide();
        } else {
            dlg.dom.block_router_mode.show();
        }
    };

    dlg.show_add = function () {
        dlg.init_fields();
        dlg.dom.dialog.modal({backdrop: 'static'});
    };

    dlg.show_edit = function (row_id) {
        var host = $app.table_host.get_row(row_id);
        dlg.init_fields(host);
        dlg.dom.dialog.modal({backdrop: 'static'});
    };

    // dlg.show_error = function (error) {
    //     dlg.dom.msg.removeClass().addClass('alert alert-danger').html(error).show();
    // };
    // dlg.hide_error = function () {
    //     dlg.dom.msg.hide();
    // };

    dlg.check_input = function () {
        dlg.field_os_type = parseInt(dlg.dom.edit_os_type.val());
        dlg.field_ip = dlg.dom.edit_ip.val();
        dlg.field_conn_mode = parseInt(dlg.dom.edit_conn_mode.val());
        dlg.field_router_ip = dlg.dom.edit_router_ip.val();
        dlg.field_router_port = parseInt(dlg.dom.edit_router_port.val());
        dlg.field_name = dlg.dom.edit_name.val();
        dlg.field_cid = dlg.dom.edit_cid.val();
        dlg.field_desc = dlg.dom.edit_desc.val();

        if (_.isNaN(dlg.field_os_type) || dlg.field_os_type === -1) {
            $tp.notify_error('请指定远程主机的操作系统！');
            return false;
        }

        if (dlg.field_ip.length === 0) {
            dlg.dom.edit_ip.focus();
            $tp.notify_error('请指定远程主机IP地址！');
            return false;
        }

        if (!tp_is_ip(dlg.field_ip)) {
            dlg.dom.edit_ip.focus();
            $tp.notify_error('远程主机IP地址格式有误！');
            return false;
        }

        if (dlg.field_conn_mode === 1) {
            // 端口映射
            if (dlg.field_router_ip.length === 0) {
                dlg.dom.edit_router_ip.focus();
                $tp.notify_error('请指定路由主机IP地址！');
                return false;
            }

            if (!tp_is_ip(dlg.field_router_ip)) {
                dlg.dom.edit_router_ip.focus();
                $tp.notify_error('路由主机IP地址格式有误！');
                return false;
            }

            if (dlg.dom.edit_router_port.val().length === 0) {
                dlg.dom.edit_router_port.focus();
                $tp.notify_error('请指定路由主机映射端口！');
                return false;
            }

            if (_.isNaN(dlg.field_router_port) || dlg.field_router_port <= 0 || dlg.field_router_port > 65535) {
                dlg.dom.edit_router_port.focus();
                $tp.notify_error('路由主机映射端口有误！');
                return false;
            } else {
                dlg.dom.edit_router_port.val('' + dlg.field_router_port);
            }
        } else {
            dlg.field_router_ip = '';
            dlg.field_router_port = 0;
        }

        return true;
    };

    dlg.on_save = function () {
        if (!dlg.check_input())
            return;

        var action = (dlg.field_id === -1) ? '添加' : '更新';

        // var router_addr = '';
        // if (dlg.field_conn_mode === 1) {
        //     router_addr = dlg.field_router_ip + ':' + dlg.field_router_port;
        // }

        var args = {
            id: dlg.field_id,
            os_type: dlg.field_os_type,
            ip: dlg.field_ip,
            router_ip: dlg.field_router_ip,
            router_port: dlg.field_router_port,
            name: dlg.field_name,
            cid: dlg.field_cid,
            desc: dlg.field_desc
        };

        // 如果id为-1表示创建，否则表示更新
        $tp.ajax_post_json('/asset/update-host', args,
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('远程主机' + action + '成功！');
                    $app.table_host.load_data();
                    dlg.dom.dialog.modal('hide');
                } else {
                    $tp.notify_error('远程主机' + action + '失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，远程主机' + action + '失败！');
            }
        );
    };

    return dlg;
};

$app.create_dlg_accounts = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-accounts';
    dlg.host_row_id = -1;
    dlg.host = null;

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        dlg_title: $('#' + dlg.dom_id + ' [data-field="dlg-title"]'),

        btn_refresh_acc: $('#btn-refresh-acc'),
        btn_add_acc: $('#btn-add-acc'),
        chkbox_acc_select_all: $('#table-acc-select-all'),

        btn_lock_acc: $('#btn-lock-acc'),
        btn_unlock_acc: $('#btn-unlock-acc'),
        btn_remove_acc: $('#btn-remove-acc')
    };

    dlg.init = function (cb_stack) {
        // dlg.dom.dialog.on('hidden.bs.modal', function () {
        //     if (!dlg.show_edit_account)
        //         return;
        //     $app.dlg_edit_account.show_edit(dlg.row_id);
        // });

        //-------------------------------
        // 账号列表表格
        //-------------------------------

        var table_acc_options = {
            dom_id: 'table-acc',
            data_source: {
                type: 'none'
            },
            column_default: {sort: false, align: 'left'},
            columns: [
                {
                    //title: '<input type="checkbox" id="user-list-select-all" value="">',
                    // title: '<a href="javascript:;" data-reset-filter><i class="fa fa-undo fa-fw"></i></a>',
                    title: '',
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
                    //sort: true,
                    //header_render: 'filter_search',
                    render: 'acc_info',
                    fields: {username: 'username'}
                },
                {
                    title: "协议",
                    key: "protocol_type",
                    //sort: true,
                    width: 60,
                    align: 'center',
                    render: 'protocol',
                    fields: {protocol_type: 'protocol_type'}
                },
                {
                    title: "认证方式",
                    key: "auth_type",
                    width: 60,
                    align: 'center',
                    render: 'auth_type',
                    fields: {auth_type: 'auth_type'}
                },
                {
                    title: "状态",
                    key: "state",
                    //sort: true,
                    width: 60,
                    align: 'center',
                    render: 'acc_state',
                    fields: {state: 'state'}
                },
                {
                    title: '',
                    key: 'action',
                    sort: false,
                    width: 180,
                    align: 'center',
                    //width: 70,
                    render: 'make_host_action_btn',
                    fields: {id: 'id', state: 'state'}
                }
            ],

            // 重载回调函数
            on_header_created: dlg.on_table_acc_header_created,
            on_render_created: dlg.on_table_acc_render_created,
            on_cell_created: dlg.on_table_acc_cell_created
        };

        $app.table_acc = $tp.create_table(table_acc_options);
        cb_stack.add($app.table_acc.init);

        dlg.dom.btn_add_acc.click(function () {
            $app.dlg_edit_account.show_add(dlg.host_row_id);
        });

        dlg.dom.btn_refresh_acc.click(function () {
            dlg.load_accounts();
        });

        dlg.dom.btn_lock_acc.click(function () {
            dlg.on_btn_lock_acc_click();
        });
        dlg.dom.btn_unlock_acc.click(function () {
            dlg.on_btn_unlock_acc_click();
        });
        dlg.dom.btn_remove_acc.click(function () {
            dlg.on_btn_remove_acc_click();
        });

        dlg.dom.chkbox_acc_select_all.click(function () {
            var _objects = $('#' + $app.table_acc.dom_id + ' tbody').find('[data-check-box]');
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

        cb_stack.exec();
    };

    dlg.get_selected_acc = function (tbl) {
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

    dlg._lock_acc = function (acc_ids) {
        $tp.ajax_post_json('/asset/update-accounts', {action: 'lock', host_id: dlg.host.id, accounts: acc_ids},
            function (ret) {
                if (ret.code === TPE_OK) {
                    CALLBACK_STACK.create()
                        .add(dlg.check_acc_all_selected)
                        .add(dlg.load_accounts)
                        .exec();
                    $tp.notify_success('禁用账号操作成功！');
                } else {
                    $tp.notify_error('禁用账号操作失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，禁用账号操作失败！');
            }
        );
    };

    dlg.on_btn_lock_acc_click = function () {
        var items = dlg.get_selected_acc($app.table_acc);
        if (items.length === 0) {
            $tp.notify_error('请选择要禁用的账号！');
            return;
        }

        dlg._lock_acc(items);
    };

    dlg._unlock_acc = function (acc_ids) {
        $tp.ajax_post_json('/asset/update-accounts', {action: 'unlock', host_id: dlg.host.id, accounts: acc_ids},
            function (ret) {
                if (ret.code === TPE_OK) {
                    CALLBACK_STACK.create()
                        .add(dlg.check_acc_all_selected)
                        .add(dlg.load_accounts)
                        .exec();
                    dlg.load_accounts();
                    $tp.notify_success('解禁账号操作成功！');
                } else {
                    $tp.notify_error('解禁账号操作失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，解禁账号操作失败！');
            }
        );
    };

    dlg.on_btn_unlock_acc_click = function () {
        var items = dlg.get_selected_acc($app.table_acc);
        if (items.length === 0) {
            $tp.notify_error('请选择要解禁的账号！');
            return;
        }

        dlg._unlock_acc(items);
    };

    dlg._remove_acc = function (acc_ids) {
        var _fn_sure = function (cb_stack) {
            $tp.ajax_post_json('/asset/update-accounts', {action: 'remove', host_id: dlg.host.id, accounts: acc_ids},
                function (ret) {
                    if (ret.code === TPE_OK) {
                        cb_stack
                            .add(dlg.check_acc_all_selected)
                            .add(dlg.load_accounts)
                            .exec();
                        $tp.notify_success('删除主机操作成功！');

                        var update_args = {
                            acc_count: dlg.host.acc_count - acc_ids.length
                        };
                        $app.table_host.update_row(dlg.host_row_id, update_args);

                    } else {
                        $tp.notify_error('删除主机操作失败：' + tp_error_msg(ret.code, ret.message));
                    }

                    cb_stack.exec();
                },
                function () {
                    $tp.notify_error('网络故障，删除主机操作失败！');
                    cb_stack.exec();
                }
            );
        };

        var cb_stack = CALLBACK_STACK.create();
        $tp.dlg_confirm(cb_stack, {
            msg: '<div class="alert alert-danger"><p><strong>注意：删除操作不可恢复！！</strong></p></div><p>如果您希望临时禁止以指定账号登录远程主机，可将其“禁用”！</p><p>您确定要移除选定的' + acc_ids.length + '个账号吗？</p>',
            fn_yes: _fn_sure
        });
    };

    dlg.on_btn_remove_acc_click = function () {
        var items = dlg.get_selected_acc($app.table_acc);
        if (items.length === 0) {
            $tp.notify_error('请选择要删除的账号！');
            return;
        }

        dlg._remove_acc(items);
    };

    dlg.show = function (host_row_id) {
        dlg.host_row_id = host_row_id;
        dlg.host = $app.table_host.get_row(host_row_id);
        dlg.dom.dialog.modal();
        dlg.load_accounts();
    };

    dlg.load_accounts = function (cb_stack) {
        cb_stack = cb_stack || CALLBACK_STACK.create();

        $tp.ajax_post_json('/asset/get-accounts', {host_id: dlg.host.id},
            function (ret) {
                if (ret.code === TPE_OK) {
                    $app.table_acc.set_data(cb_stack, {}, {total: ret.data.length, page_index: 1, data: ret.data});
                } else {
                    $app.table_acc.set_data(cb_stack, {}, {total: 0, page_index: 1, data: {}});
                    console.error('failed.', tp_error_msg(ret.code, ret.message));
                }
                cb_stack.exec();
            },
            function () {
                $tp.notify_error('网络故障，获取账号信息失败！');
                cb_stack.exec();
            }
        );
    };

    //-------------------------------
    // 账号表格相关
    //-------------------------------

    dlg.on_table_acc_cell_created = function (tbl, row_id, col_key, cell_obj) {
        if (col_key === 'chkbox') {
            cell_obj.find('[data-check-box]').click(function () {
                dlg.check_acc_all_selected();
            });
        } else if (col_key === 'action') {
            // 绑定系统选择框事件
            cell_obj.find('[data-action]').click(function () {

                var action = $(this).attr('data-action');
                var acc_id = $(this).attr('data-id');
                var acc = tbl.get_row(row_id);

                if (action === 'edit') {
                    $app.dlg_edit_account.show_edit(dlg.host_row_id, acc);
                } else if (action === 'lock') {
                    dlg._lock_acc([acc_id]);
                } else if (action === 'unlock') {
                    dlg._unlock_acc([acc_id]);
                } else if (action === 'remove') {
                    dlg._remove_acc([acc_id]);
                }
            });
        }
    };

    dlg.on_table_acc_render_created = function (render) {

        // render.filter_state = function (header, title, col) {
        //     var _ret = ['<div class="tp-table-filter tp-table-filter-' + col.cell_align + '">'];
        //     _ret.push('<div class="tp-table-filter-inner">');
        //     _ret.push('<div class="search-title">' + title + '</div>');
        //
        //     // 表格内嵌过滤器的DOM实体在这时生成
        //     var filter_ctrl = header._table_ctrl.get_filter_ctrl('state');
        //     _ret.push(filter_ctrl.render());
        //
        //     _ret.push('</div></div>');
        //
        //     return _ret.join('');
        // };
        //
        // render.filter_search = function (header, title, col) {
        //     var _ret = ['<div class="tp-table-filter tp-table-filter-input">'];
        //     _ret.push('<div class="tp-table-filter-inner">');
        //     _ret.push('<div class="search-title">' + title + '</div>');
        //
        //     // 表格内嵌过滤器的DOM实体在这时生成
        //     var filter_ctrl = header._table_ctrl.get_filter_ctrl('search');
        //     _ret.push(filter_ctrl.render());
        //
        //     _ret.push('</div></div>');
        //
        //     return _ret.join('');
        // };

        render.make_check_box = function (row_id, fields) {
            return '<span><input type="checkbox" data-check-box="' + fields.id + '" data-row-id="' + row_id + '"></span>';
        };

        render.acc_info = function (row_id, fields) {
            return fields.username;
            // var ret = [];
            //
            // ret.push('<span class="user-surname">' + fields.username + '@' + fields.host_ip + '</span>');
            // if (fields.router_ip.length > 0)
            //     ret.push('<span class="user-account">由 ' + fields.router_ip + ':' + fields.router_port + ' 路由</span>');
            //
            // return ret.join('');
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

        render.acc_state = function (row_id, fields) {
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

        render.make_host_action_btn = function (row_id, fields) {
            // var h = [];
            // h.push('<div class="btn-group btn-group-sm">');
            // h.push('<button type="button" class="btn btn-no-border dropdown-toggle" data-toggle="dropdown">');
            // h.push('<span data-selected-action>操作</span> <i class="fa fa-caret-right"></i></button>');
            // h.push('<ul class="dropdown-menu dropdown-menu-right dropdown-menu-sm">');
            // h.push('<li><a href="javascript:;" data-action="edit"><i class="fa fa-edit fa-fw"></i> 编辑</a></li>');
            // h.push('<li><a href="javascript:;" data-action="lock"><i class="fa fa-lock fa-fw"></i> 禁用</a></li>');
            // h.push('<li><a href="javascript:;" data-action="unlock"><i class="fa fa-unlock fa-fw"></i> 解禁</a></li>');
            // h.push('<li role="separator" class="divider"></li>');
            // h.push('<li><a href="javascript:;" data-action="account"><i class="fa fa-user-secret fa-fw"></i> 管理远程账号</a></li>');
            // h.push('<li role="separator" class="divider"></li>');
            // h.push('<li><a href="javascript:;" data-action="duplicate"><i class="fa fa-cubes fa-fw"></i> 复制主机</a></li>');
            // h.push('<li><a href="javascript:;" data-action="remove"><i class="fa fa-times-circle fa-fw"></i> 删除</a></li>');
            // h.push('</ul>');
            // h.push('</div>');
            //
            // return h.join('');


            var ret = [];
            ret.push('<div class="btn-group btn-group-sm" role="group">');
            ret.push('<btn class="btn btn-primary" data-action="edit" data-id="' + fields.id + '"><i class="fa fa-edit"></i> 编辑</btn>');

            if (fields.state === TP_STATE_NORMAL) {
                ret.push('<btn class="btn btn-warning" data-action="lock" data-id="' + fields.id + '"><i class="fa fa-lock fa-fw"></i> 禁用</btn>');
            } else {
                ret.push('<btn class="btn btn-info" data-action="unlock" data-id="' + fields.id + '"><i class="fa fa-unlock fa-fw"></i> 解禁</btn>');
            }

            ret.push('<btn class="btn btn-danger" data-action="remove" data-id="' + fields.id + '"><i class="fas fa-trash-alt"></i> 删除</btn>');
            ret.push('</div>');
            return ret.join('');
        };
    };

    dlg.on_table_acc_header_created = function (header) {
        // $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
        //     CALLBACK_STACK.create()
        //         .add(header._table_ctrl.load_data)
        //         .add(header._table_ctrl.reset_filters)
        //         .exec();
        // });
        //
        // // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
        // header._table_ctrl.get_filter_ctrl('search').on_created();
        // // header._table_ctrl.get_filter_ctrl('role').on_created();
        // header._table_ctrl.get_filter_ctrl('state').on_created();
    };

    dlg.check_acc_all_selected = function (cb_stack) {
        var _all_checked = true;
        var _objs = $('#' + $app.table_acc.dom_id + ' tbody').find('[data-check-box]');
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
            dlg.dom.chkbox_acc_select_all.prop('checked', true);
        } else {
            dlg.dom.chkbox_acc_select_all.prop('checked', false);
        }

        if (cb_stack)
            cb_stack.exec();
    };


    return dlg;
};

$app.create_dlg_edit_account = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-edit-account';
    dlg.host_row_id = -1;
    dlg.host = null;
    dlg.account = null;
    dlg.field_id = -1;  // 账户id（仅编辑模式）
    dlg.field_protocol = -1;
    dlg.field_auth = -1;
    dlg.field_username = '';
    dlg.field_password = '';
    dlg.field_pri_key = '';
    dlg.field_prompt_username = '';
    dlg.field_prompt_password = '';
    dlg.protocol_sub_type = 0;

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        dlg_title: $('#' + dlg.dom_id + ' [data-field="dlg-title"]'),
        protocol_type: $('#account-protocol-type'),
        protocol_port: $('#account-protocol-port'),
        auth_type: $('#account-auth-type'),
        username: $('#account-username'),
        password: $('#account-password'),
        ssh_prikey: $('#account-ssh-pri'),
        block_ssh_param: $('#block-ssh-param'),
        block_rdp_param: $('#block-rdp-param'),
        block_prompt: $('#block-prompt'),
        block_username: $('#block-username'),
        block_password: $('#block-password'),
        block_sshkey: $('#block-sshkey'),
        prompt_username: $('#account-username-prompt'),
        prompt_password: $('#account-password-prompt'),
        btn_show_password: $('#btn-show-account-password'),
        btn_show_password_icon: $('#btn-show-account-password i'),
        btn_test: $('#btn-edit-account-test'),
        btn_save: $('#btn-edit-account-save')
    };

    dlg.init = function (cb_stack) {
        dlg.dom.protocol_type.change(dlg.on_protocol_change);
        dlg.dom.auth_type.change(dlg.on_auth_change);

        dlg.dom.btn_save.click(dlg.on_save);
        dlg.dom.btn_test.click(dlg.on_test);

        dlg.dom.btn_show_password.click(function () {
            if ('password' === dlg.dom.password.attr('type')) {
                dlg.dom.password.attr('type', 'text');
                dlg.dom.btn_show_password_icon.removeClass('fa-eye').addClass('fa-eye-slash')
            } else {
                dlg.dom.password.attr('type', 'password');
                dlg.dom.btn_show_password_icon.removeClass('fa-eye-slash').addClass('fa-eye')
            }
        });

        cb_stack.exec();
    };

    dlg.init_fields = function (account) {
        dlg.dom.password.val('');
        dlg.dom.ssh_prikey.val('');

        if (_.isUndefined(account)) {
            dlg.account = null;
            dlg.field_id = -1;
            dlg.dom.dlg_title.html('添加远程账号');

            if (dlg.host.os_type === TP_OS_TYPE_LINUX) {
                dlg.dom.protocol_type.val(TP_PROTOCOL_TYPE_SSH);
            } else if (dlg.host.os_type === TP_OS_TYPE_WINDOWS) {
                dlg.dom.protocol_type.val(TP_PROTOCOL_TYPE_RDP);
            } else {
            }

            dlg.dom.username.val('');

        } else {
            dlg.account = account;
            dlg.field_id = account.id;
            dlg.dom.dlg_title.html('编辑：' + account.username);

            dlg.dom.username.val(account.username);

            dlg.dom.protocol_type.val(account.protocol_type);
            dlg.dom.protocol_port.val(account.protocol_port);
        }

        if (dlg.host.router_ip.length === 0) {
            dlg.dom.protocol_port.removeAttr('disabled');
        } else {
            dlg.dom.protocol_port.val('端口映射：' + dlg.host.router_ip + ':' + dlg.host.router_port).attr('disabled', 'disabled');
        }

        dlg.on_protocol_change();
    };

    dlg.on_protocol_change = function () {
        dlg.field_protocol = parseInt(dlg.dom.protocol_type.val());

        var html = [];
        if (dlg.field_protocol === TP_PROTOCOL_TYPE_RDP) {
            dlg.dom.block_rdp_param.show();
            dlg.dom.block_ssh_param.hide();
            dlg.dom.block_prompt.hide();

            html.push('<option value="1">用户名/密码 认证</option>');

            if (dlg.host.router_ip.length === 0) {
                if (_.isNull(dlg.account))
                    dlg.dom.protocol_port.val(3389);
                else
                    dlg.dom.protocol_port.val(dlg.account.protocol_port);
            }

            dlg.protocol_sub_type = TP_PROTOCOL_TYPE_RDP_DESKTOP;
        } else if (dlg.field_protocol === TP_PROTOCOL_TYPE_SSH) {
            dlg.dom.block_rdp_param.hide();
            dlg.dom.block_ssh_param.show();
            dlg.dom.block_prompt.hide();

            html.push('<option value="1">用户名/密码 认证</option>');
            html.push('<option value="2">SSH私钥 认证</option>');

            if (dlg.host.router_ip.length === 0) {
                if (_.isNull(dlg.account))
                    dlg.dom.protocol_port.val(22);
                else
                    dlg.dom.protocol_port.val(dlg.account.protocol_port);
            }

            dlg.protocol_sub_type = TP_PROTOCOL_TYPE_SSH_SHELL;
        } else if (dlg.field_protocol === TP_PROTOCOL_TYPE_TELNET) {
            dlg.dom.block_rdp_param.hide();
            dlg.dom.block_ssh_param.hide();
            dlg.dom.block_prompt.show();

            html.push('<option value="1">用户名/密码 认证</option>');
            html.push('<option value="0">无需认证</option>');

            if (dlg.host.router_ip.length === 0) {
                if (_.isNull(dlg.account)) {
                    dlg.dom.protocol_port.val(23);
                    dlg.dom.prompt_username.val('ogin:');
                    dlg.dom.prompt_password.val('assword:');
                }
                else {
                    dlg.dom.protocol_port.val(dlg.account.protocol_port);
                    dlg.dom.prompt_username.val(dlg.account.username_prompt);
                    dlg.dom.prompt_password.val(dlg.account.password_prompt);
                }
            }

            dlg.protocol_sub_type = TP_PROTOCOL_TYPE_TELNET_SHELL;
        } else {
            dlg.dom.protocol_port.val('');
        }

        dlg.dom.auth_type.empty().append($(html.join('')));

        if(!_.isNull(dlg.account))
            dlg.dom.auth_type.val(dlg.account.auth_type);

        dlg.on_auth_change();
    };

    dlg.on_auth_change = function () {
        dlg.field_auth = parseInt(dlg.dom.auth_type.val());
        if (dlg.field_auth === TP_AUTH_TYPE_PASSWORD) {
            dlg.dom.block_password.show();
            dlg.dom.block_sshkey.hide();
            if (dlg.field_protocol === TP_PROTOCOL_TYPE_TELNET) {
                dlg.dom.block_prompt.show();
                if (dlg.dom.prompt_username.val().length === 0 && dlg.account.username_prompt.length === 0)
                    dlg.dom.prompt_username.val('ogin:');
                if (dlg.dom.prompt_password.val().length === 0 && dlg.account.password_prompt.length === 0)
                    dlg.dom.prompt_password.val('assword:');
            }
        } else if (dlg.field_auth === TP_AUTH_TYPE_PRIVATE_KEY) {
            dlg.dom.block_password.hide();
            dlg.dom.block_sshkey.show();
        } else if (dlg.field_auth === TP_AUTH_TYPE_NONE) {
            dlg.dom.block_password.hide();
            dlg.dom.block_sshkey.hide();
            dlg.dom.block_prompt.hide();
        }
    };

    dlg.show_add = function (host_row_id) {
        dlg.host_row_id = host_row_id;
        dlg.host = $app.table_host.get_row(host_row_id);
        dlg.init_fields();
        dlg.show();
    };

    dlg.show_edit = function (host_row_id, account) {
        dlg.host_row_id = host_row_id;
        dlg.host = $app.table_host.get_row(host_row_id);
        dlg.init_fields(account);
        dlg.show();
    };

    dlg.show = function () {
        if ($(document.body).find('.modal-backdrop').length > 0)
            dlg.dom.dialog.modal({backdrop: false});
        else
            dlg.dom.dialog.modal({backdrop: 'static'});
    };

    dlg.check_input = function () {
        dlg.field_protocol = parseInt(dlg.dom.protocol_type.val());
        dlg.field_port = 0;
        dlg.field_auth_type = parseInt(dlg.dom.auth_type.val());
        dlg.field_username = dlg.dom.username.val();
        dlg.field_password = dlg.dom.password.val();
        dlg.field_pri_key = dlg.dom.ssh_prikey.val();
        dlg.field_prompt_username = dlg.dom.prompt_username.val();
        dlg.field_prompt_password = dlg.dom.prompt_password.val();

        if (dlg.host.router_ip.length === 0) {
            if (dlg.dom.protocol_port.val().length === 0) {
                $tp.notify_error('请设定远程访问的端口号！');
                dlg.dom.protocol_port.focus();
                return false;
            }

            dlg.field_port = parseInt(dlg.dom.protocol_port.val());

            if (_.isNaN(dlg.field_port) || dlg.field_port <= 0 || dlg.field_port > 65535) {
                dlg.dom.protocol_port.focus();
                $tp.notify_error('端口有误！');
                return false;
            } else {
                dlg.dom.protocol_port.val('' + dlg.field_port);
            }
        }

        if (dlg.field_username.length === 0) {
            dlg.dom.username.focus();
            $tp.notify_error('请填写登录远程主机的账号名称！');
            return false;
        }

        if (dlg.field_protocol !== TP_PROTOCOL_TYPE_TELNET) {
            dlg.field_prompt_username = '';
            dlg.field_prompt_password = '';
        }

        if (dlg.field_auth_type === TP_AUTH_TYPE_PASSWORD) {
            if (dlg.field_id === -1 && dlg.field_password.length === 0) {
                dlg.dom.password.focus();
                $tp.notify_error('请填写登录远程主机的密码！');
                return false;
            }
            dlg.field_pri_key = '';
        } else if (dlg.field_auth_type === TP_AUTH_TYPE_PRIVATE_KEY) {
            if (dlg.field_id === -1 && dlg.field_pri_key.length === 0) {
                dlg.dom.ssh_prikey.focus();
                $tp.notify_error('请填写登录远程主机的SSH私钥！');
                return false;
            }
            dlg.field_password = '';
        } else if (dlg.field_auth_type === TP_AUTH_TYPE_NONE) {
            dlg.field_prompt_username = '';
            dlg.field_prompt_password = '';
            dlg.field_password = '';
            dlg.field_pri_key = '';
        }

        return true;
    };

    dlg.on_save = function () {
        if (!dlg.check_input())
            return;

        var action = (dlg.field_id === -1) ? '添加' : '更新';

        // 如果id为-1表示创建，否则表示更新
        $tp.ajax_post_json('/asset/update-account', {
                host_id: dlg.host.id,
                acc_id: dlg.field_id,
                param: {
                    host_ip: dlg.host.ip,
                    router_ip: dlg.host.router_ip,
                    router_port: dlg.host.router_port,
                    protocol: dlg.field_protocol,
                    port: dlg.field_port,
                    auth_type: dlg.field_auth_type,
                    username: dlg.field_username,
                    password: dlg.field_password,
                    pri_key: dlg.field_pri_key,
                    username_prompt: dlg.field_prompt_username,
                    password_prompt: dlg.field_prompt_password
                }
            },
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('远程账号' + action + '成功！');

                    if (dlg.field_id === -1) {
                        // 新建账号成功了，更新界面上对应主机的账号数
                        var update_args = {
                            acc_count: dlg.host.acc_count + 1
                        };
                        $app.table_host.update_row(dlg.host_row_id, update_args);
                    }

                    // 更新上一级对话框中的数据
                    $app.dlg_accounts.load_accounts();

                    dlg.dom.dialog.modal('hide');
                } else {
                    $tp.notify_error('远程账号' + action + '失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，远程账号' + action + '失败！');
            }
        );
    };

    dlg.on_test = function () {
        if (!dlg.check_input())
            return;

        $assist.do_teleport(
            {
                mode: 0,
                auth_id: 'none',
                acc_id: dlg.field_id,
                host_id: dlg.host.id,
                protocol_type: dlg.field_protocol,
                protocol_sub_type: dlg.protocol_sub_type,
                protocol_port: dlg.field_port,
                auth_type: dlg.field_auth_type,
                username: dlg.field_username,
                password: dlg.field_password,
                pri_key: dlg.field_pri_key,
                username_prompt: dlg.field_prompt_username,
                password_prompt: dlg.field_prompt_password
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

    return dlg;
};
