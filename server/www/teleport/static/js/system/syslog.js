"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        btn_refresh_log: $('#btn-refresh-log'),
    };

    cb_stack.add($app.create_controls);
    cb_stack.exec();
};

//===================================
// 创建页面控件对象
//===================================
$app.create_controls = function (cb_stack) {

    //-------------------------------
    // 日志表格
    //-------------------------------
    var table_log_options = {
        dom_id: 'table-log',
        data_source: {
            type: 'ajax-post',
            url: '/system/get-logs'
        },
        column_default: {sort: false, align: 'left'},
        columns: [
            {
                title: '时间',
                key: 'log_time',
                sort: true,
                sort_asc: false,
                width: 160,
                //header_render: 'filter_search_host',
                render: 'log_time',
                fields: {log_time: 'log_time'}
            },
            // {
            //     title: 'ID',
            //     key: 'id',
            //     width:80,
            //     fields: {id: 'id'}
            // },
            {
                title: '用户',
                key: 'user',
                width: 160,
                //sort: true,
                //header_render: 'filter_search_host',
                render: 'user',
                fields: {user_name: 'user_name', user_surname: 'user_surname'}
            },
            {
                title: '来源',
                key: 'client_ip',
                width: 100,
                //sort: true,
                //header_render: 'filter_search_host',
                //render: 'host_info',
                fields: {client_ip: 'client_ip'}
            },
            {
                title: '操作',
                key: 'remote',
                //sort: true,
                //header_render: 'filter_search_host',
                render: 'message',
                fields: {code: 'code', message: 'message'}
            }
        ],

        // 重载回调函数
        on_header_created: $app.on_table_host_header_created,
        on_render_created: $app.on_table_host_render_created
        // on_cell_created: $app.on_table_host_cell_created
    };

    $app.table_log = $tp.create_table(table_log_options);
    cb_stack
        .add($app.table_log.load_data)
        .add($app.table_log.init);

    //-------------------------------
    // 用户列表相关过滤器
    //-------------------------------
    $app.table_log_filter_search_host = $tp.create_table_header_filter_search($app.table_log, {
        name: 'search_host',
        place_holder: '搜索：主机IP/名称/描述/资产编号/等等...'
    });
    // $app.table_log_role_filter = $tp.create_table_filter_role($app.table_log, $app.role_list);
    //$tp.create_table_header_filter_state($app.table_log, 'state', $app.obj_states, [TP_STATE_LOCKED]);

    $app.table_log_paging = $tp.create_table_paging($app.table_log, 'table-log-paging',
        {
            per_page: Cookies.get($app.page_id('system_log') + '_per_page'),
            on_per_page_changed: function (per_page) {
                Cookies.set($app.page_id('system_log') + '_per_page', per_page, {expires: 365});
            }
        });
    $tp.create_table_pagination($app.table_log, 'table-log-pagination');

    //-------------------------------
    // 页面控件事件绑定
    //-------------------------------
    $app.dom.btn_refresh_log.click(function () {
        $app.table_log.load_data();
    });

    cb_stack.exec();
};

// $app.on_table_host_cell_created = function (tbl, row_id, col_key, cell_obj) {
//     if (col_key === 'chkbox') {
//         cell_obj.find('[data-check-box]').click(function () {
//             $app.check_host_all_selected();
//         });
//     } else if (col_key === 'action') {
//         // 绑定系统选择框事件
//         cell_obj.find('[data-action]').click(function () {
//             var action = $(this).attr('data-action');
//             if (action === 'edit') {
//                 $app.dlg_edit_host.show_edit(row_id);
//             } else if (action === 'account') {
//                 $app.dlg_accounts.show(row_id);
//             }
//         });
//     } else if (col_key === 'ip') {
//         cell_obj.find('[data-toggle="popover"]').popover({trigger: 'hover'});
//         // } else if (col_key === 'account') {
//         //     cell_obj.find('[data-action="add-account"]').click(function () {
//         //         $app.dlg_accounts.show(row_id);
//         //     });
//     } else if (col_key === 'account_count') {
//         cell_obj.find('[data-action="edit-account"]').click(function () {
//             $app.dlg_accounts.show(row_id);
//         });
//     }
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

    // render.filter_host_state = function (header, title, col) {
    //     var _ret = ['<div class="tp-table-filter tp-table-filter-' + col.cell_align + '">'];
    //     _ret.push('<div class="tp-table-filter-inner">');
    //     _ret.push('<div class="search-title">' + title + '</div>');
    //
    //     // 表格内嵌过滤器的DOM实体在这时生成
    //     var filter_ctrl = header._table_ctrl.get_filter_ctrl('host_state');
    //     _ret.push(filter_ctrl.render());
    //
    //     _ret.push('</div></div>');
    //
    //     return _ret.join('');
    // };

    // render.filter_search_host = function (header, title, col) {
    //     var _ret = ['<div class="tp-table-filter tp-table-filter-input">'];
    //     _ret.push('<div class="tp-table-filter-inner">');
    //     _ret.push('<div class="search-title">' + title + '</div>');
    //
    //     // 表格内嵌过滤器的DOM实体在这时生成
    //     var filter_ctrl = header._table_ctrl.get_filter_ctrl('search_host');
    //     _ret.push(filter_ctrl.render());
    //
    //     _ret.push('</div></div>');
    //
    //     return _ret.join('');
    // };

    render.log_time = function (row_id, fields) {
        return tp_format_datetime(tp_utc2local(fields.log_time));
    };

    render.user = function (row, fields) {
        if (_.isNull(fields.user_surname) || fields.user_surname.length === 0 || fields.user_name === fields.user_surname) {
            return fields.user_name;
        } else {
            return fields.user_name + ' (' + fields.user_surname + ')';
        }
    };

    render.message = function (row_id, fields) {
        if(fields.code === TPE_OK)
            return fields.message;

        return '<span class="label label-danger">'+fields.message+'</span>';
    };

    // render.os = function (row_id, fields) {
    //     return fields.os;
    // };
    //

};

$app.on_table_host_header_created = function (header) {
    $('#' + header._table_ctrl.dom_id + ' a[data-reset-filter]').click(function () {
        CALLBACK_STACK.create()
            .add(header._table_ctrl.load_data)
            .add(header._table_ctrl.reset_filters)
            .exec();
    });

    // 表格内嵌过滤器的事件绑定在这时进行（也可以延期到整个表格创建完成时进行）
    // header._table_ctrl.get_filter_ctrl('search_host').on_created();
    // // header._table_ctrl.get_filter_ctrl('role').on_created();
    // header._table_ctrl.get_filter_ctrl('host_state').on_created();
};

