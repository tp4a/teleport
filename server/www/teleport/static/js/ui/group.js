/**
 * Created by mi on 2016/7/4.
 */
var g_gourp_dlg_info = null;
ywl.on_init = function (cb_stack, cb_args) {
    var dom_id = '#ywl_group_list';

    //===================================
    // 创建页面控件对象
    //===================================
    // 表格数据
    var host_table_options = {
        selector: dom_id + " [ywl-table='group-list']",
        data_source: {
            type: 'ajax-post',
            url: '/group/list'
        },
        column_default: {sort: false, header_align: 'center', cell_align: 'center'},
        columns: [
            {title: "分组ID", key: "id", width: 80},
            {title: "分组名称", key: "group_name", header_align: 'left', cell_align: 'left'},
            {title: "操作", key: "action", width: 240, render: 'make_action_btn', fields: {id: 'group_id'}}
        ],
        paging: {selector: dom_id + " [ywl-paging='group-list']", per_page: paging_normal},

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
    g_gourp_dlg_info = ywl.create_group_info_dlg(host_table);
    $(dom_id + " [ywl-filter='reload']").click(host_table.reload);
    $("#btn-add-group").click(function () {
        g_gourp_dlg_info.create_show();
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
                g_gourp_dlg_info.update_show(row_data.group_name, row_data.id, row_id);
            });
            $(cell_obj).find('[ywl-btn-delete]').click(function () {
                var group_id = row_data.id;
                var _fn_sure = function (cb_stack, cb_args) {
                    ywl.ajax_post_json('/host/delete-group', {group_id: group_id},
                        function (ret) {
                            if (ret.code === TPE_OK) {
                                tbl.remove_row(row_id);
                                ywl.notify_success('删除分组成功！');
                            } else if (ret.code === -2) {
                                ywl.notify_error('因为有主机隶属此分组，因此不能删除此分组。请先将此分组中的主机设定为其他分组，然后重试！');
                            } else {
                                ywl.notify_error('删除分组失败：' + ret.message);
                            }

                        },
                        function () {
                            ywl.notify_error('网络故障，删除分组失败！');
                        }
                    );
                };
                var cb_stack = CALLBACK_STACK.create();

                ywl.dlg_confirm(cb_stack,
                    {
                        msg: '<p><strong>注意：移除操作不可恢复！！</strong></p><p>您确定要删除此分组吗？</p>',
                        fn_yes: _fn_sure
                    });


            });

        }
    };

    // 重载表格渲染器的部分渲染方式，加入本页面相关特殊操作
    tbl.on_render_created = function (render) {
        render.make_action_btn = function (row_id, fields) {
            var ret = [];
            ret.push('<a href="javascript:;" class="btn btn-primary btn-success btn-group-sm" ywl-btn-edit="' + fields.id + '">编辑</a>&nbsp');
            ret.push('<a href="javascript:;" class="btn btn-primary btn-danger btn-group-sm" ywl-btn-delete="' + fields.id + '">删除</a>');
            return ret.join('');
        }

    };
};

ywl.on_host_table_header_created = function (tbl) {
};

ywl.create_group_info_dlg = function (tbl) {
    var group_info_dlg = {};
    group_info_dlg.dom_id = "#dialog_group_info";
    group_info_dlg.update = 1;
    group_info_dlg.tbl = tbl;
    group_info_dlg.group_name = '';
    group_info_dlg.group_id = 0;
    group_info_dlg.row_id = 0;

    group_info_dlg.update_show = function (group_name, group_id, row_id) {
        group_info_dlg.update = 1;
        group_info_dlg.init(group_name, group_id, row_id);
        $(group_info_dlg.dom_id).modal();
    };
    group_info_dlg.create_show = function () {
        group_info_dlg.update = 0;
        group_info_dlg.init('', 0, 0);
        $(group_info_dlg.dom_id).modal();
    };

    group_info_dlg.hide = function () {
        $(group_info_dlg.dom_id).modal('hide');
    };

    group_info_dlg.init = function (group_name, group_id, row_id) {
        group_info_dlg.group_name = group_name;
        group_info_dlg.group_id = group_id;
        group_info_dlg.row_id = row_id;
        group_info_dlg.init_dlg();
    };
    group_info_dlg.init_dlg = function () {
        $(group_info_dlg.dom_id + ' #group_name').val(group_info_dlg.group_name);
    };

    group_info_dlg.check_args = function () {
        group_info_dlg.group_name = $(group_info_dlg.dom_id + ' #group_name').val();
        return true;
    };
    group_info_dlg.post = function () {
        if (group_info_dlg.update == 1) {
            ywl.ajax_post_json('/host/update-group', {group_id: group_info_dlg.group_id, group_name: group_info_dlg.group_name},
                function (ret) {
                    if (ret.code === TPE_OK) {
                        var update_args = {id: group_info_dlg.group_id, group_name: group_info_dlg.group_name};
                        group_info_dlg.tbl.update_row(group_info_dlg.row_id, update_args);
                        ywl.notify_success('更新分组信息成功！');
                        group_info_dlg.hide();
                    } else {
                        ywl.notify_error('更新分组失败：' + ret.message);
                    }
                },
                function () {
                    ywl.notify_error('网络故障，更新分组信息失败！');
                }
            );
        } else {
            ywl.ajax_post_json('/host/add-group', {group_name: group_info_dlg.group_name},
                function (ret) {
                    if (ret.code === TPE_OK) {
                        group_info_dlg.tbl.reload();
                        ywl.notify_success('创建分组成功！');
                        group_info_dlg.hide();
                    } else {
                        ywl.notify_error('创建分组失败：' + ret.message);
                    }
                },
                function () {
                    ywl.notify_error('网络故障，创建分组失败！');
                }
            );
        }
        //group_info_dlg.group_name = $(group_info_dlg.dom_id + ' #group_name').val();
        return true;
    };
    $(group_info_dlg.dom_id + " #btn-save").click(function () {
        if (!group_info_dlg.check_args()) {
            return;
        }
        group_info_dlg.post();
    });
    return group_info_dlg
}