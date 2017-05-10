/**
 * Created by mi on 2016/7/4.
 */

var g_user_dlg_info = null;

ywl.on_init = function (cb_stack, cb_args) {
    var dom_id = '#ywl_user_list';

    //===================================
    // 创建页面控件对象
    //===================================
    // 表格数据
    var host_table_options = {
        selector: dom_id + " [ywl-table='user-list']",
        data_source: {
            type: 'ajax-post',
            url: '/user/list'
        },
        column_default: {sort: false, header_align: 'center', cell_align: 'center'},
        columns: [
            {title: "用户ID", key: "user_id", width: 80},
            {title: "用户名", key: "user_name", width: 200},
            {title: "用户描述", key: "user_desc"},
            {title: "状态", key: "user_lock", width: 200, render: 'user_lock', fields: {user_lock: 'user_lock'}},
            {title: "操作", key: "action", width: 380, render: 'make_action_btn', fields: {user_id: 'user_id', user_lock: 'user_lock'}}
        ],
        paging: {selector: dom_id + " [ywl-paging='user-list']", per_page: paging_normal},

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
    g_user_dlg_info = ywl.create_user_info_dlg(host_table);

    $(dom_id + " [ywl-filter='reload']").click(host_table.reload);
    $("#btn-add-user").click(function () {
        g_user_dlg_info.create_show();
    });
    cb_stack
        .add(host_table.load_data)
        .add(host_table.init)
        .exec();
};

// 扩展/重载表格的功能
ywl.on_host_table_created = function (tbl) {

    tbl.on_cell_created = function (row_id, col_key, cell_obj) {
        if (col_key === 'action') {
            var row_data = tbl.get_row(row_id);
            //console.log('row_data', row_data);
            $(cell_obj).find('[ywl-btn-edit]').click(function () {
                g_user_dlg_info.update_show(row_data.user_name, row_data.user_desc, row_data.user_id, row_id);
            });

            $(cell_obj).find('[ywl-btn-reset]').click(function () {
                var user_id = row_data.user_id;
                //var user_lock = row_data.user_lock;
                var message = '此操作将用户密码重置为默认密码 <span class="mono h3">123456</span>，确定要执行吗？<br/><br/>提示：密码重置后，请通知用户立即修改默认密码！';
                var _fn_sure = function (cb_stack, cb_args) {
                    ywl.ajax_post_json('/user/reset-user', {user_id: user_id},
                        function (ret) {
                            if (ret.code === TPE_OK) {
                                ywl.notify_success('重置用户密码操作成功！');
                            } else {
                                ywl.notify_error('重置用户密码操作失败！');
                            }
                        },
                        function () {
                            ywl.notify_error('网络故障，重置用户密码操作失败！');
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

            $(cell_obj).find('[ywl-btn-lock]').click(function () {
                var user_id = row_data.user_id;
                var user_lock = row_data.user_lock;
                var message = '';
                if (user_lock === 0) {
                    user_lock = 1;
                    message = '被锁定的用户将无法登陆系统，确认要锁定该用户吗？';
                } else {
                    user_lock = 0;
                    message = '确认要解锁该用户吗？';
                }
                var _fn_sure = function (cb_stack, cb_args) {
                    ywl.ajax_post_json('/user/lock-user', {user_id: user_id, lock_status: user_lock},
                        function (ret) {
                            if (ret.code === TPE_OK) {
                                var update_args = {user_lock: user_lock};
                                tbl.update_row(row_id, update_args);
                                ywl.notify_success('操作成功！');
                            } else {
                                ywl.notify_error('操作失败！');
                            }
                        },
                        function () {
                            ywl.notify_error('网络故障，操作失败！');
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
                var user_id = row_data.user_id;
                var _fn_sure = function (cb_stack, cb_args) {
                    ywl.ajax_post_json('/user/delete-user', {user_id: user_id},
                        function (ret) {
                            if (ret.code === TPE_OK) {
                                tbl.remove_row(row_id);
                                ywl.notify_success('删除用户成功！');
                            } else {
                                ywl.notify_error('删除用户失败：' + ret.message);
                            }

                        },
                        function () {
                            ywl.notify_error('网络故障，删除用户失败！');
                        }
                    );
                };
                var cb_stack = CALLBACK_STACK.create();

                ywl.dlg_confirm(cb_stack,
                    {
                        msg: '<p><strong>注意：移除操作不可恢复！！</strong></p><p>您确定要删除此用户吗？</p>',
                        fn_yes: _fn_sure
                    });


            });
            $(cell_obj).find('[ywl-auth-allo]').click(function () {
                window.open("/user/auth/" + row_data.user_name);
            });


        }
    };

    // 重载表格渲染器的部分渲染方式，加入本页面相关特殊操作
    tbl.on_render_created = function (render) {
        render.user_lock = function (row_id, fields) {
            switch (fields.user_lock) {
                case 0:
                    return '<span class="badge badge-success">允许访问</span>';
                case 1:
                    return '<span class="badge badge-danger">禁止访问</span>';
                default:
                    return '<span class="badge badge-danger">未知</span>';
            }
        };
        render.make_action_btn = function (row_id, fields) {
            var ret = [];
            ret.push('<div class="btn-group btn-group-sm" role="group">');

            ret.push('<a href="javascript:;" class="btn btn-sm btn-primary" ywl-auth-allo="' + fields.user_id + '"><i class="fa fa-trash-o fa-fw"></i> 授权</a>');

            ret.push('</div> &nbsp;<div class="btn-group btn-group-sm" role="group">');

            ret.push('<a href="javascript:;" class="btn btn-sm btn-primary" ywl-btn-edit="' + fields.user_id + '"><i class="fa fa-edit fa-fw"></i> 编辑</a>');
            ret.push('<a href="javascript:;" class="btn btn-sm btn-success" ywl-btn-reset="' + fields.user_id + '"><i class="fa fa-circle-o fa-fw"></i> 重置密码</a>');

            ret.push('</div> &nbsp;<div class="btn-group btn-group-sm" role="group">');
            if (fields.user_lock === 0)
                ret.push('<a href="javascript:;" class="btn btn-sm btn-warning" ywl-btn-lock="' + fields.user_id + '"><i class="fa fa-lock fa-fw"></i> 锁定</a>');
            else
                ret.push('<a href="javascript:;" class="btn btn-sm btn-success" ywl-btn-lock="' + fields.user_id + '"><i class="fa fa-unlock fa-fw"></i> 解锁</a>');

            ret.push('<a href="javascript:;" class="btn btn-sm btn-danger" ywl-btn-delete="' + fields.user_id + '"><i class="fa fa-trash-o fa-fw"></i> 移除</a>');
            ret.push('</div>');
            return ret.join('');
        }

    };
};

ywl.on_host_table_header_created = function (tbl) {
};

ywl.create_user_info_dlg = function (tbl) {
    var user_info_dlg = {};
    user_info_dlg.dom_id = "#dialog_user_info";
    user_info_dlg.update = 1;
    user_info_dlg.tbl = tbl;
    user_info_dlg.user_name = '';
    user_info_dlg.user_id = 0;
    user_info_dlg.row_id = 0;
    user_info_dlg.user_desc = '';

    user_info_dlg.update_show = function (user_name, user_desc, user_id, row_id) {
        user_info_dlg.update = 1;
        user_info_dlg.init(user_name, user_desc, user_id, row_id);
        $('#dlg-notice').hide();
        $(user_info_dlg.dom_id).modal();
    };
    user_info_dlg.create_show = function () {
        user_info_dlg.update = 0;
        user_info_dlg.init('', '', 0, 0);
        $('#dlg-notice').show();
        $(user_info_dlg.dom_id).modal();
    };

    user_info_dlg.hide = function () {
        $(user_info_dlg.dom_id).modal('hide');
    };

    user_info_dlg.init = function (user_name, user_desc, user_id, row_id) {
        user_info_dlg.user_name = user_name;
        user_info_dlg.user_desc = user_desc;
        user_info_dlg.user_id = user_id;
        user_info_dlg.row_id = row_id;
        user_info_dlg.init_dlg();
    };
    user_info_dlg.init_dlg = function () {
        $(user_info_dlg.dom_id + ' #user-name').val(user_info_dlg.user_name);
        $(user_info_dlg.dom_id + ' #user-desc').val(user_info_dlg.user_desc);
        if (user_info_dlg.update === 1) {
            $(user_info_dlg.dom_id + ' #user-name').attr("disabled", "true");
        } else {
            $(user_info_dlg.dom_id + ' #user-name').removeAttr("disabled");
        }

    };

    user_info_dlg.check_args = function () {
        user_info_dlg.user_name = $(user_info_dlg.dom_id + ' #user-name').val();
        user_info_dlg.user_desc = $(user_info_dlg.dom_id + ' #user-desc').val();
        return true;
    };
    user_info_dlg.post = function () {
        if (user_info_dlg.update === 1) {
            ywl.ajax_post_json('/user/modify-user', {user_id: user_info_dlg.user_id, user_desc: user_info_dlg.user_desc},
                function (ret) {
                    if (ret.code === TPE_OK) {
                        var update_args = {user_desc: user_info_dlg.user_desc};
                        user_info_dlg.tbl.update_row(user_info_dlg.row_id, update_args);
                        ywl.notify_success('更新用户信息成功！');
                        user_info_dlg.hide();
                    } else {
                        ywl.notify_error('更新用户信息失败：' + ret.message);
                    }
                },
                function () {
                    ywl.notify_error('网络故障，更新用户信息失败！');
                }
            );
        } else {
            ywl.ajax_post_json('/user/add-user', {user_name: user_info_dlg.user_name, user_desc: user_info_dlg.user_desc},
                function (ret) {
                    if (ret.code === TPE_OK) {
                        user_info_dlg.tbl.reload();
                        ywl.notify_success('添加用户成功！');
                        user_info_dlg.hide();
                    } else if (ret.code === -100) {
                        ywl.notify_error('已经存在同名用户！');
                    } else {
                        ywl.notify_error('添加用户失败：' + ret.message);
                    }
                },
                function () {
                    ywl.notify_error('网络故障，添加用户失败！');
                }
            );
        }
        return true;
    };
    $(user_info_dlg.dom_id + " #btn-save").click(function () {
        if (!user_info_dlg.check_args()) {
            return;
        }
        user_info_dlg.post();
    });
    return user_info_dlg
};
