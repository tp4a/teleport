"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        btn_refresh_policy: $('#btn-refresh-policy'),
        btn_create_policy: $('#btn-create-policy'),
        select_all_policy: $('#table-auz-select-all'),

        btn_lock: $('#btn-lock'),
        btn_unlock: $('#btn-unlock'),
        btn_remove: $('#btn-remove')
    };

    $app.drag = {
        dragging: false,
        drag_row_id: '0',
        hover_row_id: '0',
        drag_index: -1,
        hover_index: -1,
        insert_before: true,   // 是插入到拖放目标之前还是之后
        items: [],

        dom: {}
    };

    $('#btn-rebuild').click(function () {
        $app.on_rebuild();
    });

    // $app.dragging = false;
    // $app.drag_row_id = 0;
    // $app.drag_to_insert = [];
    $(document).mousemove(function (e) {
        $app.on_dragging(e);
    }).mouseup(function (e) {
        $app.on_drag_end(e);
    });

    cb_stack
        .add($app.create_controls)
        .add($app.load_role_list);

    cb_stack.exec();
};

$app.on_rebuild = function () {
    $tp.ajax_post_json('/ops/build-auz-map', {},
        function (ret) {
            if (ret.code === TPE_OK) {
                $tp.notify_success('重建授权映射成功！');
            } else {
                $tp.notify_error('重建授权映射失败：' + tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $tp.notify_error('网络故障，重建授权映射失败！');
        }
    );
};

//===================================
// 创建页面控件对象
//===================================
$app.create_controls = function (cb_stack) {

    //-------------------------------
    // 资产列表表格
    //-------------------------------
    var table_policy_options = {
        dom_id: 'table-policy',
        data_source: {
            type: 'ajax-post',
            url: '/ops/get-policies'
        },
        column_default: {sort: false, align: 'left'},
        columns: [
            {
                //title: '<a href="javascript:;" data-reset-filter><i class="fa fa-undo fa-fw"></i></a>',
                title: '',
                key: 'chkbox',
                sort: false,
                width: 36,
                align: 'center',
                render: 'make_check_box',
                fields: {id: 'id'}
            },
            {
                title: '顺序',
                key: 'rank',
                // sort: true,
                align: 'center',
                width: 60,
                // header_render: 'filter_search',
                render: 'rank',
                fields: {rank: 'rank'}
            },
            {
                title: '授权策略',
                key: 'name',
                // sort: true,
                // header_render: 'filter_search',
                render: 'policy_info',
                fields: {id: 'id', name: 'name', desc: 'desc'}
            },
            {
                title: "状态",
                key: "state",
                // sort: true,
                width: 90,
                align: 'center',
                //header_render: 'filter_state',
                render: 'state',
                fields: {state: 'state'}
            },
            {
                title: '',
                key: 'action',
                // sort: false,
                align: 'center',
                width: 80,
                render: 'make_action_btn',
                fields: {id: 'id', state: 'state'}
            }
        ],

        // 重载回调函数
        on_header_created: $app.on_table_policy_header_created,
        on_render_created: $app.on_table_policy_render_created,
        on_cell_created: $app.on_table_policy_cell_created
    };

    $app.table_policy = $tp.create_table(table_policy_options);
    cb_stack
        .add($app.table_policy.load_data)
        .add($app.table_policy.init);

    //-------------------------------
    // 用户列表相关过滤器
    //-------------------------------
    $tp.create_table_header_filter_search($app.table_policy, {
        name: 'search',
        place_holder: '搜索：授权策略名称/描述/等等...'
    });
    $tp.create_table_header_filter_state($app.table_policy, 'state', $app.obj_states, [TP_STATE_LOCKED]);
    // 从cookie中读取用户分页限制的选择
    $tp.create_table_paging($app.table_policy, 'table-auz-paging',
        {
            per_page: Cookies.get($app.page_id('ops_auz') + '_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('ops_auz') + '_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_policy, 'table-auz-pagination');

    //-------------------------------
    // 对话框
    //-------------------------------
    $app.dlg_edit_policy = $app.create_dlg_edit_policy();
    cb_stack.add($app.dlg_edit_policy.init);

    //-------------------------------
    // 页面控件事件绑定
    //-------------------------------
    $app.dom.btn_create_policy.click(function () {
        // $app.dom.dlg_edit_user.modal();
        $app.dlg_edit_policy.show_add();
    });
    $app.dom.btn_refresh_policy.click(function () {
        $app.table_policy.load_data();
    });
    $app.dom.select_all_policy.click(function () {
        var _objects = $('#' + $app.table_policy.dom_id + ' tbody').find('[data-check-box]');
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
    $app.dom.btn_lock.click($app.on_btn_lock_click);
    $app.dom.btn_unlock.click($app.on_btn_unlock_click);
    $app.dom.btn_remove.click($app.on_btn_remove_click);

    cb_stack.exec();
};

$app.on_table_policy_cell_created = function (tbl, row_id, col_key, cell_obj) {
    if (col_key === 'chkbox') {
        cell_obj.find('[data-check-box]').click(function () {
            $app.check_host_all_selected();
        });
    } else if (col_key === 'rank') {
        cell_obj.find('.reorder').mousedown(function (e) {
            $app.on_drag_begin(e, row_id);
        });
    } else if (col_key === 'action') {
        // 绑定系统选择框事件
        cell_obj.find('[data-action]').click(function () {
            var action = $(this).attr('data-action');
            if (action === 'edit') {
                $app.dlg_edit_policy.show_edit(row_id);
                // } else if (action === 'account') {
                //     $app.dlg_accounts.show(row_id);
            }
        });
    } else if (col_key === 'name') {
        cell_obj.find('[data-action="edit-policy"]').click(function () {
            $app.dlg_accounts.show(row_id);
        });
    }
};

$app.on_drag_begin = function (e, row_id) {
    $(document).bind('selectstart', function () {
        return false;
    });

    $app.drag = {
        dragging: false,
        drag_row_id: '0',
        hover_row_id: '0',
        drag_index: -1,
        hover_index: -1,
        items: [],

        dom: {}
    };

    $app.drag.drag_row_id = row_id;

    var body = $('body');
    // create a drag-div
    var policy = $app.table_policy.get_row(row_id);

    body.after($('<div id="tp-drag-move-box" style="display:none;position:absolute;font-size:13px;cursor:move;opacity:0.7;padding:5px;background:#999;border:1px solid #666;"><i class="fas fa-bars fa-fw"></i> ' + policy.rank + ' ' + policy.name + '</div>'));

    $app.drag.dom.move_box = $('#tp-drag-move-box');
    $app.drag.move_box_height = $app.drag.dom.move_box.height();
    $app.drag.dom.move_box.css({left: e.pageX - 5, top: e.pageY - $app.drag.move_box_height / 2}).show();

    // create a location-pointer
    body.after($('<div id="tp-drag-insert" style="display:none;position:absolute;color:#97d262"><i class="fa fa-chevron-right fa-fw"></i></div>'));
    $app.drag.dom.loc_insert = $('#tp-drag-insert');

    var tr_item = $('tr[data-row-id]');
    for (var i = 0; i < tr_item.length; ++i) {
        var item = $(tr_item[i]);
        var _row_id = item.attr('data-row-id');
        if (_row_id === row_id)
            $app.drag.drag_index = i;
        $app.drag.items.push([item.offset().top, item.offset().top + item.height(), _row_id]);
    }

    $app.drag.dragging = true;
};

$app.on_dragging = function (e) {
    if (!$app.drag.dragging)
        return;

    $app.drag.dom.move_box.css({left: e.pageX - 5, top: e.pageY - $app.drag.move_box_height / 2});

    // check which <tr> we are moving on.
    $app.drag.hover_row_id = null;
    for (var i = 0; i < $app.drag.items.length; ++i) {
        if (e.pageY < $app.drag.items[i][0])
            continue;
        if (e.pageY > $app.drag.items[i][1])
            continue;
        if ($app.drag_row_id === $app.drag.items[i][2])
            continue;

        if ($app.drag.drag_row_id === $app.drag.items[i][2])
            break;

        var idx = -1;
        if (e.pageY <= $app.drag.items[i][0] + ($app.drag.items[i][1] - $app.drag.items[i][0]) / 2) {
            $app.drag.insert_before = true;
            idx = i - 1;
        }
        else {
            $app.drag.insert_before = false;
            idx = i + 1;
        }

        if (idx === $app.drag.drag_index)
            break;

        $app.drag.hover_row_id = $app.drag.items[i][2];

        break;
    }

    if ($app.drag.hover_row_id === null) {
        $app.drag.dom.loc_insert.hide();
        return;
    } else {
        $app.drag.dom.loc_insert.show();
    }

    var hover_obj = $('tr[data-row-id="' + $app.drag.hover_row_id + '"]');


    var x = hover_obj.offset().left - $app.drag.dom.loc_insert.width();
    var y = 0;
    if ($app.drag.insert_before)
        y = hover_obj.offset().top - $app.drag.dom.loc_insert.height() / 2;
    else
        y = hover_obj.offset().top + hover_obj.height() - $app.drag.dom.loc_insert.height() / 2;
    $app.drag.dom.loc_insert.css({left: x, top: y});
};

$app.on_drag_end = function (e) {
    if (!$app.drag.dragging)
        return;

    $app.drag.dom.move_box.remove();
    $app.drag.dom.loc_insert.remove();
    $(document).unbind('selectstart');
    $app.drag.dragging = false;

    if ($app.drag.hover_row_id === null)
        return;

    var policy_drag = $app.table_policy.get_row($app.drag.drag_row_id);
    var policy_target = $app.table_policy.get_row($app.drag.hover_row_id);

    var direct = -1; // 移动方向，-1=向前移动，1=向后移动
    var start_rank = 0, end_rank = 0; // 导致rank变化的范围：  start_rank <= rank <= end_rank
    var new_rank = 0;//policy_target.rank;  // 被移动的条目的新rank

    if (policy_drag.rank > policy_target.rank) {
        // 这是向前移动
        direct = 1;
        end_rank = policy_drag.rank - 1;
        if ($app.drag.insert_before) {
            new_rank = policy_target.rank;
            start_rank = policy_target.rank;
        }
        else {
            new_rank = policy_target.rank + 1;
            start_rank = policy_target.rank + 1;
        }
    } else {
        // 这是向后移动
        direct = -1;
        start_rank = policy_drag.rank + 1;
        if ($app.drag.insert_before) {
            new_rank = policy_target.rank - 1;
            end_rank = policy_target.rank - 1;
        }
        else {
            new_rank = policy_target.rank;
            end_rank = policy_target.rank;
        }
    }

    $tp.ajax_post_json('/ops/policy/rank-reorder', {
            pid: policy_drag.id,
            new_rank: new_rank,
            start_rank: start_rank,
            end_rank: end_rank,
            direct: direct
        },
        function (ret) {
            if (ret.code === TPE_OK) {
                $tp.notify_success('授权策略顺序调整成功！');
                $app.table_policy.load_data();
            } else {
                $tp.notify_error('授权策略顺序调整失败：' + tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $tp.notify_error('网络故障，授权策略顺序调整失败！');
        }
    );
};

$app.check_host_all_selected = function (cb_stack) {
    var _all_checked = true;
    var _objs = $('#' + $app.table_policy.dom_id + ' tbody').find('[data-check-box]');
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
        $app.dom.select_all_policy.prop('checked', true);
    } else {
        $app.dom.select_all_policy.prop('checked', false);
    }

    if (cb_stack)
        cb_stack.exec();
};

$app.on_table_policy_render_created = function (render) {

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
    //
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

    render.rank = function (row_id, fields) {
        return '<span class="reorder"><i class="fas fa-bars fa-fw"></i> ' + fields.rank + '</span>'
    };

    render.make_check_box = function (row_id, fields) {
        return '<span><input type="checkbox" data-check-box="' + fields.id + '" data-row-id="' + row_id + '"></span>';
    };

    render.policy_info = function (row_id, fields) {
        return '<a href="/ops/policy/detail/' + fields.id + '">' + fields.name + '</a><span class="policy-desc">' + fields.desc + '</span>'
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

    render.make_action_btn = function (row_id, fields) {
        var ret = [];
        ret.push('<div class="btn-group btn-group-sm" role="group">');
        ret.push('<btn class="btn btn-primary" data-action="edit"><i class="fa fa-edit"></i> 编辑</btn>');
        // ret.push('<btn class="btn btn-info" data-btn-disable="' + fields.id + '"><i class="fas fa-trash-alt"></i> 禁用</btn>');
        // ret.push('<btn class="btn btn-danger" data-btn-remove="' + fields.id + '"><i class="fas fa-trash-alt"></i> 删除</btn>');
        ret.push('</div>');
        return ret.join('');
    };
};

$app.on_table_policy_header_created = function (header) {
    // $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
    //     CALLBACK_STACK.create()
    //         .add(header._table_ctrl.load_data)
    //         .add(header._table_ctrl.reset_filters)
    //         .exec();
    // });

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    // header._table_ctrl.get_filter_ctrl('search').on_created();
    // header._table_ctrl.get_filter_ctrl('state').on_created();
};

$app.get_selected_policy = function (tbl) {
    var users = [];
    var _objs = $('#' + $app.table_policy.dom_id + ' tbody tr td input[data-check-box]');
    $.each(_objs, function (i, _obj) {
        if ($(_obj).is(':checked')) {
            var _row_data = tbl.get_row(_obj);
            // _all_checked = false;
            users.push(_row_data.id);
        }
    });
    return users;
};

$app.on_btn_lock_click = function () {
    var items = $app.get_selected_policy($app.table_policy);
    if (items.length === 0) {
        $tp.notify_error('请选择要禁用的授权策略！');
        return;
    }

    $tp.ajax_post_json('/ops/policies/update', {
            action: 'lock',
            policy_ids: items
        },
        function (ret) {
            if (ret.code === TPE_OK) {
                CALLBACK_STACK.create()
                    .add($app.check_host_all_selected)
                    .add($app.table_policy.load_data)
                    .exec();
                $tp.notify_success('禁用授权策略操作成功！');
            } else {
                $tp.notify_error('禁用授权策略操作失败：' + tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $tp.notify_error('网络故障，禁用授权策略操作失败！');
        }
    );
};

$app.on_btn_unlock_click = function () {
    var items = $app.get_selected_policy($app.table_policy);
    if (items.length === 0) {
        $tp.notify_error('请选择要解禁的授权策略！');
        return;
    }

    $tp.ajax_post_json('/ops/policies/update', {
            action: 'unlock',
            policy_ids: items
        },
        function (ret) {
            if (ret.code === TPE_OK) {
                CALLBACK_STACK.create()
                    .add($app.check_host_all_selected)
                    .add($app.table_policy.load_data)
                    .exec();
                $tp.notify_success('解禁授权策略操作成功！');
            } else {
                $tp.notify_error('解禁授权策略操作失败：' + tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $tp.notify_error('网络故障，解禁授权策略操作失败！');
        }
    );
};

$app.on_btn_remove_click = function () {
    var items = $app.get_selected_policy($app.table_policy);
    if (items.length === 0) {
        $tp.notify_error('请选择要删除的授权策略！');
        return;
    }

    var _fn_sure = function (cb_stack, cb_args) {
        $tp.ajax_post_json('/ops/policies/update', {
                action: 'remove',
                policy_ids: items
            },
            function (ret) {
                if (ret.code === TPE_OK) {
                    cb_stack.add($app.check_host_all_selected);
                    cb_stack.add($app.table_policy.load_data);
                    $tp.notify_success('删除授权策略操作成功！');
                } else {
                    $tp.notify_error('删除授权策略操作失败：' + tp_error_msg(ret.code, ret.message));
                }

                cb_stack.exec();
            },
            function () {
                $tp.notify_error('网络故障，删除授权策略操作失败！');
                cb_stack.exec();
            }
        );
    };

    var cb_stack = CALLBACK_STACK.create();
    $tp.dlg_confirm(cb_stack, {
        msg: '<div class="alert alert-danger"><p><strong>注意：删除操作不可恢复！！</strong></p></div><p>如果您希望临时禁止指定的授权策略，可将其“禁用”！</p><p>您确定要移除选定的' + items.length + '个授权策略吗？</p>',
        fn_yes: _fn_sure
    });

};

$app.create_dlg_edit_policy = function () {
    var dlg = {};
    dlg.dom_id = 'dlg-edit-policy';
    dlg.field_id = -1;
    dlg.field_name = '';
    dlg.field_desc = '';

    dlg.dom = {
        dialog: $('#' + dlg.dom_id),
        dlg_title: $('#' + dlg.dom_id + ' [data-field="dlg-title"]'),
        edit_name: $('#edit-name'),
        edit_desc: $('#edit-desc'),
        btn_save: $('#btn-edit-policy-save')
    };

    dlg.init = function (cb_stack) {
        dlg.dom.btn_save.click(dlg.on_save);
        cb_stack.exec();
    };

    dlg.init_fields = function (policy) {
        dlg.field_id = -1;
        dlg.field_os_type = -1;

        if (_.isUndefined(policy)) {
            dlg.dom.dlg_title.html('创建授权策略');

            dlg.dom.edit_name.val('');
            dlg.dom.edit_desc.val('');
        } else {
            dlg.field_id = policy.id;
            dlg.dom.dlg_title.html('编辑授权策略：');
            dlg.dom.edit_name.val(policy.name);
            dlg.dom.edit_desc.val(policy.desc);
        }
    };

    dlg.show_add = function () {
        dlg.init_fields();
        dlg.dom.dialog.modal({backdrop: 'static'});
    };

    dlg.show_edit = function (row_id) {
        var host = $app.table_policy.get_row(row_id);
        dlg.init_fields(host);
        dlg.dom.dialog.modal({backdrop: 'static'});
    };

    dlg.check_input = function () {
        dlg.field_name = dlg.dom.edit_name.val();
        dlg.field_desc = dlg.dom.edit_desc.val();

        if (dlg.field_name.length === 0) {
            dlg.dom.edit_name.focus();
            $tp.notify_error('请设定授权策略名称！');
            return false;
        }

        return true;
    };

    dlg.on_save = function () {
        if (!dlg.check_input())
            return;

        var action = (dlg.field_id === -1) ? '添加' : '更新';

        // 如果id为-1表示创建，否则表示更新
        $tp.ajax_post_json('/ops/policy/update', {
                id: dlg.field_id,
                name: dlg.field_name,
                desc: dlg.field_desc
            },
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('授权策略' + action + '成功！');
                    $app.table_policy.load_data();
                    dlg.dom.dialog.modal('hide');
                } else {
                    $tp.notify_error('授权策略' + action + '失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，授权策略' + action + '失败！');
            }
        );
    };

    return dlg;
};
