//===================================================
// basic and common functions.
//===================================================

"use strict";

$tp.create_table = function (options) {
    // 可重载的函数（在table_options中设定）
    // on_table_created
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

    var _tbl = {};

    // 此表格绑定的DOM对象的ID，用于JQuery的选择器
    _tbl.dom_id = options.dom_id;
    _tbl.options = options;
    _tbl.column_count = _tbl.options.columns.length;

    _tbl.row_data = []; // 每一行的数据内容
    _tbl.total = 0;	// 记录总数
    _tbl.page_index = 0;	// 当前页数（基数为0）
    _tbl.page_total = 0;    // 总页数
    _tbl.per_page = 25;	// 每页显示的记录数量

    // 内建的表头控件(一个表格只有一个表头控件)
    _tbl.header_ctrl = null;
    // 关联的分页信息控件(一个表格只有一个分页控件，显示记录总数、页数、总页数，选择每页显示记录数等等)
    _tbl.paging_ctrl = null;
    // 关联的分页跳转控件(一个表格只有一个分页控件，显示上一页、下一页，跳转到指定页等等)
    _tbl.pagination_ctrl = null;
    // 关联的过滤器控件（一个表格可以有多个过滤器控件）
    _tbl.filter_ctrls = {};

    // 过滤器值对，由过滤器控件调用 _tbl.update_filter() 进行设定
    // 每个过滤器控件可以设置一到多个过滤器值对
    // 此外，当过滤器值对数据发生变化，过滤器控件的 _tblf.on_filter_change() 会被调用，用于更新过滤器控件界面
    // _tbl.filter = {};

    _tbl.render = null;//$tp.create_table_render(self, self.options.on_render_created || null);

    //=======================
    // 需要被重载的函数
    //=======================

    _tbl.on_data_loaded = function (cb_stack, cb_args) {
        cb_stack.exec();
    };

    // _tbl.on_cell_created = function (tbl, row_id, col_key, obj) {
    // };

    _tbl.init = function (cb_stack, cb_args) {
        _tbl._fix_options();

        // 表格创建完成后，加入表格的body部分，这样就可以在没有表头的情况下创建表格了
        cb_stack.add(_tbl._make_body);

        // 创建表格渲染器
        _tbl.render = $tp.create_table_render(_tbl, _tbl.options.on_render_created || null);

        // 根据需要创建表头并初始化
        if (_tbl.options.have_header) {
            _tbl.header_ctrl = $tp.create_table_header(_tbl, _tbl.options.on_header_created || null);
            cb_stack.add(_tbl.header_ctrl.init);
        }

        // 如果设置了分页控件的属性，那么创建分页控件并初始化
        // if (_tbl.options.have_paging) {
        //     _tbl.paging_ctrl = $tp.create_table_paging(_tbl, _tbl.on_paging_created || null);
        //     cb_stack.add(_tbl.paging_ctrl.init);
        // }
        if (!_.isUndefined(_tbl.paging_ctrl) && !_.isNull(_tbl.paging_ctrl))
            cb_stack.add(_tbl.paging_ctrl.init);
        if (!_.isUndefined(_tbl.pagination_ctrl) && !_.isNull(_tbl.pagination_ctrl))
            cb_stack.add(_tbl.pagination_ctrl.init);

        // 对每一个过滤器进行初始化
        $.each(_tbl.filter_ctrls, function (name, ctrl) {
            if (_.isFunction(ctrl.init)) {
                cb_stack.add(ctrl.init);
            }
        });

        // 执行初始化函数链
        cb_stack.exec();
    };

    _tbl._make_body = function (cb_stack) {
        $('#' + _tbl.dom_id).append($('<tbody></tbody>'));
        cb_stack.exec();
    };

    _tbl.destroy = function (cb_stack) {
        $('#' + _tbl.dom_id).empty();
        cb_stack.exec();
    };

    // 整理传入的表格初始化参数
    _tbl._fix_options = function () {
        if (!_.isUndefined(_tbl.options.column_default)) {
            for (var i = 0, cnt = _tbl.options.columns.length; i < cnt; ++i) {
                if (!_.isUndefined(_tbl.options.columns[i]['align'])) {
                    if (_.isUndefined(_tbl.options.columns[i]['header_align'])) {
                        _tbl.options.columns[i]['header_align'] = _tbl.options.columns[i]['align'];
                    }
                    if (_.isUndefined(_tbl.options.columns[i]['cell_align'])) {
                        _tbl.options.columns[i]['cell_align'] = _tbl.options.columns[i]['align'];
                    }
                }

                for (var k in _tbl.options.column_default) {
                    if (_tbl.options.column_default.hasOwnProperty(k)) {
                        if (k === 'align') {
                            if (_.isUndefined(_tbl.options.columns[i]['header_align'])) {
                                _tbl.options.columns[i]['header_align'] = _tbl.options.column_default[k];
                            }
                            if (_.isUndefined(_tbl.options.columns[i]['cell_align'])) {
                                _tbl.options.columns[i]['cell_align'] = _tbl.options.column_default[k];
                            }
                        }
                        else if (_.isUndefined(_tbl.options.columns[i][k])) {
                            _tbl.options.columns[i][k] = _tbl.options.column_default[k];
                        }
                    }
                }

                if (_.isUndefined(_tbl.options.columns[i]['fields'])) {
                    _tbl.options.columns[i]['fields'] = {};
                    _tbl.options.columns[i]['fields'][_tbl.options.columns[i]['key']] = _tbl.options.columns[i]['key'];
                }
                if (_.isUndefined(_tbl.options.columns[i]['sort_asc'])) {
                    _tbl.options.columns[i]['sort_asc'] = true;
                }
                if (_.isUndefined(_tbl.options.columns[i]['recreate'])) {
                    _tbl.options.columns[i]['recreate'] = true;
                }
            }
        }
        if (_.isUndefined(_tbl.options.sort)) {
            _tbl.options.sort = 'remote';
        }

        if (_.isUndefined(_tbl.options.have_header)) {
            _tbl.options.have_header = true;
        }

        _tbl.options.have_paging = !_.isUndefined(_tbl.options.paging);
        //if (_.isUndefined(_tbl.options.paging)) {
        //	_tbl.options.have_paging = false;
        //} else {
        //	_tbl.options.have_paging = true;
        //}

        // cb_stack.exec();
    };

    //=====================================================================
    // 关联控件相关操作
    //=====================================================================
    _tbl.add_filter_ctrl = function (filter_name, filter_ctrl) {
        if (!_.isUndefined(_tbl.filter_ctrls[filter_name])) {
            console.error('filter named `' + filter_name + '` already exists, can not add again.');
            return;
        }

        _tbl.filter_ctrls[filter_name] = filter_ctrl;
    };

    _tbl.get_filter_ctrl = function (filter_name) {
        if (_.isUndefined(_tbl.filter_ctrls[filter_name]))
            console.error('no such filter named `' + filter_name + '`');
        return _tbl.filter_ctrls[filter_name];
    };

    // // 由各个相关的过滤器设置过滤属性，供表格load_data时使用。
    // _tbl.set_filter = function (name, value) {
    //     if (_.isUndefined(_tbl.filter[name]))
    //         return;
    //     if (_.isUndefined(value) || _.isNull(value)) {
    //         delete _tbl.filter[name];
    //         return;
    //     }
    //
    //     _tbl.filter[name] = value;
    // };

    //=====================================================================
    // 过滤器相关操作
    //=====================================================================
    _tbl.reset_filters = function (cb_stack, cb_args) {
        cb_stack = cb_stack || CALLBACK_STACK.create();

        $.each(_tbl.filter_ctrls, function (name, ctrl) {
            if (_.isFunction(ctrl.reset))
                cb_stack.add(ctrl.reset);
        });

        cb_stack.exec();
    };

    //=====================================================================
    // 功能
    //=====================================================================
    _tbl.load_data = function (cb_stack, cb_args) {
        cb_stack = cb_stack || CALLBACK_STACK.create();

        //log.v('load table data.', cb_args);
        if (_tbl.paging_ctrl)
            _tbl.per_page = _tbl.paging_ctrl.get_per_page();
        else
            _tbl.per_page = 0;

        _tbl.load_begin(1500);

        var _filter = {};
        // 对每一个关联的过滤器，获取其设置
        $.each(_tbl.filter_ctrls, function (name, ctrl) {
            if (_.isUndefined(ctrl.get_filter)) {
                console.error('filter', name, 'has have no get_filter() interface.');
            }
            var _f = ctrl.get_filter();
            // console.log('filter from', name, _f);
            $.each(_f, function (k, v) {
                _filter[k] = v;
            });
        });

        var _order = null;
        if (_tbl.header_ctrl) {
            _order = _tbl.header_ctrl.get_order();
        }

        var _limit = {};
        _limit.page_index = _tbl.page_index;
        _limit.per_page = _tbl.per_page;

        var args = {filter: _filter, order: _order, limit: _limit};
        if (_tbl.options.data_source && _tbl.options.data_source.restrict)
            args.restrict = _tbl.options.data_source.restrict;
        if (_tbl.options.data_source && _tbl.options.data_source.exclude)
            args.exclude = _tbl.options.data_source.exclude;

        // console.log('when load, args:', args);
        // console.log('when load, order:', _order);
        // console.log('when load, limit:', _limit);

        // 根据数据源的设定加载数据
        if (_tbl.options.data_source) {
            if (_tbl.options.data_source.type === 'none') {
                // 外部直接调用set_data()方法来设置数据，无需本控件主动获取
            } else if (_tbl.options.data_source.type === 'callback') {
                // 调用一个函数来加载数据
                args.table = _tbl;
                _tbl.options.data_source.fn(cb_stack, args);
            } else if (_tbl.options.data_source.type === 'ajax-post') {
                var _url = _tbl.options.data_source.url;
                $tp.ajax_post_json(_url, args,
                    function (ret) {
                        // console.log('ajax-return:', ret);
                        if (ret.code !== TPE_OK) {
                            $tp.notify_error(tp_error_msg(ret.code, ret.message));
                            _tbl.show_load_failed();
                        } else {
                            cb_stack.add(_tbl.load_end);
                            _tbl.set_data(cb_stack, {}, {total: ret.data.total, page_index: ret.data.page_index, data: ret.data.data});
                        }
                    },
                    function () {
                        _tbl.show_load_failed();
                    }, 6000
                );
            } else {
                console.error('table-options [data-source] type [' + _tbl.options.data_source.type + '] known.');
            }
        } else {
            console.error('have no idea for load table data. need data_source.');
        }
    };

    _tbl._create_row_dom = function (row_data) {
        var node = ['<tr data-row-id="' + row_data._row_id + '">'];

        for (var i = 0, cnt = _tbl.options.columns.length; i < cnt; ++i) {
            var col = _tbl.options.columns[i];
            node.push('<td data-cell-id="' + row_data._row_id + '-' + i + '"');

            var _style = '';
            if (col.cell_align !== 'center') {
                _style += 'text-align:' + col.cell_align + ';';
            }

            if (_style.length > 0) {
                node.push(' style="');
                node.push(_style);
                node.push('"');
            }

            node.push('>');

            var k;
            if (_.isUndefined(col.render)) {
                if (_.isUndefined(col.fields) || _.isEmpty(col.fields)) {
                    node.push(row_data[col.key]);
                } else {
                    var _tmp = [];
                    for (k in col.fields) {
                        if (col.fields.hasOwnProperty(k))
                            _tmp.push(row_data[col.fields[k]]);
                    }
                    node.push(_tmp.join(' '));
                }
            } else {
                if (_.isFunction(_tbl.render[col.render])) {
                    var _args = {};
                    for (k in col.fields) {
                        if (col.fields.hasOwnProperty(k))
                            _args[k] = row_data[col.fields[k]];
                    }
                    node.push(_tbl.render[col.render](row_data._row_id, _args));
                }
            }
            node.push('</td>');
        }
        node.push('</tr>');

        return node.join('');
    };

    _tbl._render_row = function (row_data, pos_row_id) {
        // 0=插入到第一行，-1=插入到最后一行（默认），其他=插入到指定row_id的行之后，如果没有找到指定的行，则插入到最后
        var _pos = !_.isUndefined(pos_row_id) ? pos_row_id : -1;

        var dom_obj = $('#' + _tbl.dom_id + ' tbody');
        var _tr = $(_tbl._create_row_dom(row_data));
        _tr.data('data-row-data', row_data);

        if (_pos === -1) {
            dom_obj.append(_tr);
        } else if (_pos === 0) {
            dom_obj.prepend(_tr);
        } else {
            var _pos_obj = $(dom_obj).find("[data-row-id='" + _pos + "']");
            if (0 === _pos_obj[0]) {
                // 没有找到指定行，则加入到最后
                dom_obj.append(_tr);
            } else {
                // 找到了指定行，则尾随其后
                _pos_obj.after(_tr);
            }
        }

        // callback for each cell.
        if (_.isFunction(_tbl.options.on_cell_created)) {
            var _cell_objs = $('#' + _tbl.dom_id + " tr[data-row-id='" + row_data._row_id + "'] td");
            for (var i = 0, cnt = _cell_objs.length; i < cnt; ++i) {
                console.log('aaaa');
                _tbl.options.on_cell_created(_tbl, row_data._row_id, _tbl.options.columns[i].key, $(_cell_objs[i]));
            }
        }

        if (_.isFunction(_tbl.options.on_row_created)) {
            var _row_obj = $('#' + _tbl.dom_id + " [data-row-id='" + row_data._row_id + "']");
            _tbl.options.on_row_created(_tbl, row_data._row_id, _row_obj);
        }
    };

    _tbl._render_rows = function (rows_data, pos_row_id) {
        // 0=插入到第一行，-1=插入到最后一行（默认），其他=插入到指定row_id的行之后，如果没有找到指定的行，则插入到最后
        var _pos = !_.isUndefined(pos_row_id) ? pos_row_id : -1;

        var dom_obj = $('#' + _tbl.dom_id + ' tbody');
        var node = [];

        var r;
        var row_count = rows_data.length;
        for (r = 0; r < row_count; ++r) {
            node.push(_tbl._create_row_dom(rows_data[r]));
        }

        var _tr = $(node.join(''));

        if (_pos === -1) {
            dom_obj.append(_tr);
        } else if (_pos === 0) {
            dom_obj.prepend(_tr);
        } else {
            var _pos_obj = $(dom_obj).find("[data-row-id='" + _pos + "']");
            if (0 === _pos_obj[0]) {
                // 没有找到指定行，则加入到最后
                dom_obj.append(_tr);
            } else {
                // 找到了指定行，则尾随其后
                _pos_obj.after(_tr);
            }
        }

        var _have_cell_created = _.isFunction(_tbl.options.on_cell_created);
        var _have_row_created = _.isFunction(_tbl.options.on_row_created);

        for (r = 0; r < row_count; ++r) {
            var _row_obj = $('#' + _tbl.dom_id + ' tr[data-row-id="' + rows_data[r]._row_id + '"]');
            _row_obj.data('data-row-data', rows_data[r]);

            if (_have_cell_created) {
                for (var i = 0, cnt = _tbl.options.columns.length; i < cnt; ++i) {
                    _tbl.options.on_cell_created(_tbl, rows_data[r]._row_id, _tbl.options.columns[i].key, $('#' + _tbl.dom_id + ' td[data-cell-id="' + rows_data[r]._row_id + '-' + i + '"]'));
                }
            }
            if (_have_row_created) {
                _tbl.options.on_row_created(_tbl, rows_data[r]._row_id, _row_obj);
            }
        }
    };

    _tbl.render_table = function (cb_stack, cb_args) {
        var dom_obj = $('#' + _tbl.dom_id + ' tbody');

        if (_tbl.row_data.length === 0) {
            _tbl.show_empty_table();
            cb_stack.exec();
            return;
        } else {
            dom_obj.empty();
        }

        _tbl._render_rows(_tbl.row_data);

        cb_stack.exec();
    };

    _tbl.set_data = function (cb_stack, cb_args, ex_args) {
        _tbl.row_data = ex_args.data || [];
        _tbl.total = ex_args.total || _tbl.row_data.length;
        _tbl.page_index = ex_args.page_index || 0;
        _tbl.page_total = Math.ceil(_tbl.total / _tbl.per_page);

        // 我们为表格的每一行数据加入我们自己的索引 _row_id
        for (var i = 0, cnt = _tbl.row_data.length; i < cnt; ++i) {
            if (_.isUndefined(_tbl.row_data[i]._row_id)) {
                _tbl.row_data[i]._row_id = _.uniqueId();
            }

            if (_.isFunction(_tbl.options.on_set_row_data)) {
                _tbl.options.on_set_row_data(_tbl.row_data[i]);
            }
        }

        cb_stack
            .add(_tbl.on_data_loaded)
            .add(_tbl.update_paging)
            .add(_tbl.render_table)
            .exec();
    };

    // get_row() 获取绑定到一行上的原始数据。传入的参数，可以是下列几种：
    // 1. 行本身的DOM对象，或者行内任意一个DOM对象
    // 2. 行本身的JQuery对象，或者行内任意一个JQuery对象
    // 3. 行的id（创建行时内部制定的，不一定是顺序号）
    _tbl.get_row = function (obj) {
        var _tr = null;
        if (_.isElement(obj) || _.isObject(obj)) {
            var _obj = _.isElement(obj) ? $(obj) : obj;
            if (_obj.prop('tagName') === 'TR') {
                _tr = _obj;
            } else if (_obj.prop('tagName') === 'TD') {
                _tr = $(_obj.parent()[0]);
            } else {
                _tr = $(_obj.parentsUntil($('tr')).parent()[0]);
            }
            return _tr.data('data-row-data');
        } else if (_.isString(obj) || _.isNumber(obj)) {
            var _id = _.isString(obj) ? obj : '' + obj;
            for (var i = 0, cnt = _tbl.row_data.length; i < cnt; ++i) {
                if (_tbl.row_data[i]._row_id === _id) {
                    return _tbl.row_data[i];
                }
            }
            return null;
        } else {
            console.error('need an element.');
            return null;
        }
    };

    // TODO: 更新一行数据，传入的kv有可能比原始数据内容的字段更多，需要能够保存下来备用
    // TODO: 此外，需要检查一下表格初始化时使用的字段，如果这些字段的内容并没有更新，则无需更新界面元素，以提升性能
    _tbl.update_row = function (row_id, kv) {
        var _row_obj = $('#' + _tbl.dom_id + " tr[data-row-id='" + row_id + "']");
        var _row_data = _row_obj.data('data-row-data');
        var _changed_fields = [];
        for (var k in kv) {
            if (kv.hasOwnProperty(k)) {
                if (!_.isUndefined(_row_data[k])) {
                    if (_row_data[k] !== kv[k])
                        _changed_fields.push(k);
                }
                _row_data[k] = kv[k];
            }
        }

        _row_obj.data('data-row-data', _row_data);

        if (_changed_fields.length === 0)
            return;

        console.log('-- update row ui --');

        // 根据columns的设置，更新界面元素
        for (var i in _tbl.options.columns) {
            if (!_tbl.options.columns.hasOwnProperty(i))
                continue;
            var col = _tbl.options.columns[i];
            for (k in kv) {
                if (!kv.hasOwnProperty(k))
                    continue;

                //log.v('k:', k, 'fields:', col.fields, 'chk:', _.contains(col.fields, k));

                if (_.contains(col.fields, k)) {

                    var _cell = $('#' + _tbl.dom_id + ' td[data-cell-id="' + row_id + '-' + i + '"]');

                    if (col.recreate) {
                        if (_.isFunction(_tbl.options.on_cell_created)) {
                            var node = '';
                            if (_.isUndefined(col.render)) {
                                node += _row_data[col.key];
                            } else {
                                if (_.isFunction(_tbl.render[col.render])) {
                                    var _args = {};
                                    for (var f in col.fields) {
                                        if (col.fields.hasOwnProperty(f))
                                            _args[f] = _row_data[col.fields[f]];
                                    }
                                    node += _tbl.render[col.render](row_id, _args);
                                }
                            }
                            _cell.html(node);
                            _tbl.options.on_cell_created(_tbl, row_id, col.key, _cell);
                        }
                    } else {
                        //log.v('update-row.', col.key);
                        if (_.isFunction(_tbl.options.on_cell_update)) {
                            _tbl.options.on_cell_update(_tbl, row_id, col.key, _cell);
                        }
                    }


                    //if (col.recreate) {
                    //	_cell.html(node);
                    //	_tbl.on_cell_created(row_id, col.key, _cell);
                    //} else {
                    //	log.v('update-row.', col.key);
                    //	_tbl.on_cell_created(row_id, col.key, _cell);
                    //}

                    break;
                }
            }
        }
    };

    // 参数pos_row_id: 0=插入到第一行，-1=插入到最后一行（默认），其他=插入到指定row_id的行之后，如果没有找到指定的行，则插入到最后
    _tbl.add_row = function (rows, pos_row_id, fn_is_duplicated) {
        var ret_row_id = [];
        var _fn = _.isFunction(fn_is_duplicated) ? fn_is_duplicated : null;
        var _new_count = rows.length;
        for (var i = 0; i < _new_count; ++i) {
            var _my_count = _tbl.row_data.length;
            var _is_duplicated = false;
            for (var j = 0; j < _my_count; ++j) {
                if (_fn) {
                    if (_fn(rows[i], _tbl.row_data[j])) {
                        _is_duplicated = true;
                        break;
                    }
                } else {
                    if (rows[i] === _tbl.row_data[j]) {
                        _is_duplicated = true;
                        break;
                    }
                }
            }

            if (!_is_duplicated) {
                //if(_.isUndefined(rows[i].ywl_row_id)) {
                //	rows[i].ywl_row_id = _.uniqueId();
                //}
                rows[i]._row_id = _.uniqueId();
                ret_row_id.push(rows[i]._row_id);

                _tbl.row_data.push(rows[i]);
                if (_.isFunction(_tbl.options.on_set_row_data)) {
                    _tbl.options.on_set_row_data(rows[i]);
                }
                _tbl._render_row(rows[i], pos_row_id);
            } else {
                ret_row_id.push(-1);
            }
        }

        return ret_row_id;
    };

    _tbl.remove_row = function (row_id) {
        var _index = -1;
        for (var i = 0, cnt = _tbl.row_data.length; i < cnt; ++i) {
            if (_tbl.row_data[i]['_row_id'] === row_id) {
                _index = i;
                break;
            }
        }

        if (_index === -1) {
            return false;
        }

        _tbl.row_data.splice(_index, 1);
        $('#' + _tbl.dom_id + ' tbody [data-row-id="' + row_id + '"]').remove();
        return true;
    };

    _tbl.clear = function () {
        $('#' + _tbl.dom_id + ' tbody').empty();
        _tbl.row_data = [];
        var cb_stack = CALLBACK_STACK.create();
        cb_stack
            .add(_tbl.on_data_loaded)
            .add(_tbl.update_paging)
            .exec();
    };

    _tbl.reload = function () {
        _tbl.load_data(CALLBACK_STACK.create(), {});
    };

    _tbl.load_begin = function (delay_) {
        var _delay = delay_ || 1000;
        _tbl.show_loading(_delay);
    };

    _tbl.load_end = function (cb_stack) {
        if (_tbl.loading_timer !== null) {
            clearTimeout(_tbl.loading_timer);
            _tbl.loading_timer = null;
        }

        cb_stack.exec();
    };

    _tbl.show_loading = function (delay_) {
        var _delay = delay_ || 0;
        if (_delay > 0) {
            if (_tbl.loading_timer === null) {
                _tbl.loading_timer = setTimeout(function () {
                    _tbl.show_loading();
                }, _delay);
                return;
            }
        }

        var msg_loading = '<tr role="row"><td class="loading" colspan="' + _tbl.column_count + '" style="text-align:center;"><i class="fa fa-circle-o-notch fa-spin"></i> 加载中，请稍候...</td></tr>';
        $('#' + _tbl.dom_id + ' tbody').prepend($(msg_loading))
    };

    _tbl.show_load_failed = function () {
        if (_tbl.loading_timer !== null) {
            clearTimeout(_tbl.loading_timer);
            _tbl.loading_timer = null;
        }

        var msg_loading = '<tr><td class="loading" colspan="' + _tbl.column_count + '" style="text-align:center;background-color:#f0d4d2;"><i class="fas fa-exclamation-triangle fa-fw"></i> 糟糕！加载失败了...</td></tr>';
        $('#' + _tbl.dom_id + ' tbody').empty().append($(msg_loading))
    };

    _tbl.show_empty_table = function () {
        if (_tbl.loading_timer !== null) {
            clearTimeout(_tbl.loading_timer);
            _tbl.loading_timer = null;
        }

        // var msg = '哇哦，没有数据哦...';
        // if(_tbl.options.message_no_data)
        var msg = _tbl.options.message_no_data || '哇哦，没有数据哦...';

        var msg_loading = '<tr><td class="loading" colspan="' + _tbl.column_count + '" style="text-align:center;"><i class="fa fa-info-circle fa-fw"></i> ' + msg + '</td></tr>';
        $('#' + _tbl.dom_id + ' tbody').empty().append($(msg_loading))
    };

    _tbl.update_paging = function (cb_stack, cb_args) {
        if (_tbl.paging_ctrl) {
            cb_stack.add(_tbl.paging_ctrl.update, {total: _tbl.total, page_index: _tbl.page_index, page_total: _tbl.page_total, per_page: _tbl.per_page});
        }
        if (_tbl.pagination_ctrl) {
            cb_stack.add(_tbl.pagination_ctrl.update, {total: _tbl.total, page_index: _tbl.page_index, page_total: _tbl.page_total, per_page: _tbl.per_page});
        }

        cb_stack.exec();
    };

    _tbl.paging_jump = function (page_index) {
        _tbl.page_index = page_index || 0;
        //_tbl.page_index -= 1;
        _tbl.load_data(CALLBACK_STACK.create(), {});
    };

    if (_.isFunction(_tbl.options.on_table_created)) {
        _tbl.options.on_table_created(_tbl);
    }

    return _tbl;
};

// TODO: to create fixed header (not scroll), see https://github.com/markmalek/Fixed-Header-Table

$tp.create_table_header = function (tbl, on_created) {
    var _tbl_header = {};

    _tbl_header.dom_id = tbl.dom_id;
    _tbl_header._table_ctrl = tbl;
    //table_ctrl.header_ctrl = self;
    _tbl_header._columns = tbl.options.columns;

    _tbl_header.order_by = '';	// 排序字段（不一定对应数据库的字段，可能需要对应转换）
    _tbl_header.order_asc = true;	// 是否以升序排列

    _tbl_header.get_order = function () {
        if (_tbl_header.order_by === '') {
            return null;
        } else {
            return {k: _tbl_header.order_by, v: _tbl_header.order_asc};
        }
    };

    _tbl_header.init = function (cb_stack, cb_args) {
        _tbl_header.order_by = null;
        if (_tbl_header.order_by === null) {
            _tbl_header.order_by = '';
        }

        var _first_sort = '';
        var _sort_asc = true;
        var _found = false;
        $.each(_tbl_header._columns, function (i, col) {
            if (col.sort) {
                if (_first_sort === '') {
                    _first_sort = col.key;
                    if (!_.isUndefined(col.sort_asc))
                        _sort_asc = col.sort_asc;
                }

                if (_tbl_header.order_by === col.key) {
                    _found = true;
                    if (!_.isUndefined(col.sort_asc))
                        _sort_asc = col.sort_asc;
                    return false;	// 跳出循环
                }
            }
        });

        if (!_found) {
            _tbl_header.order_by = _first_sort;
        }
        _tbl_header.order_asc = _sort_asc;

        // 创建表格头
        var _dom = ['<thead><tr>'];
        $.each(_tbl_header._columns, function (i, col) {
            _dom.push('<th');
            var _style = '';
            if (col.header_align !== 'center') {
                _style += 'text-align:' + col.header_align + ';';
            }
            if (col.width) {
                _style += 'width:' + col.width + 'px;';
            }
            if (_style.length > 0)
                _dom.push(' style="' + _style + '"');

            _dom.push('>');

            var _title = ['<span data-col-key="' + col.key + '"'];
            if (col.sort) {
                _title.push(' class="');
                if (_tbl_header.order_by === col.key) {
                    if (_tbl_header.order_asc)
                        _title.push('sorting_asc');
                    else
                        _title.push('sorting_desc');
                } else {
                    _title.push('sorting');
                }
                _title.push('"');
            }
            _title.push('>' + col.title + '</span>');
            _title = _title.join('');

            // 如果设置了表头渲染器，就交给渲染器去生产DOM，否则生产简单的表头DOM
            if (!_.isUndefined(col.header_render)) {
                if (!_.isFunction(_tbl_header._table_ctrl.render[col.header_render])) {
                    console.error('`' + col.header_render + '` is not callable.');
                }
                _dom.push(_tbl_header._table_ctrl.render[col.header_render](
                    _tbl_header, _title, col
                ));
            } else {
                _dom.push(_title);
            }

            _dom.push('</th>');
        });
        _dom.push('</tr></thead>');

        $('#' + _tbl_header.dom_id).append($(_dom.join('')));

        // 为标题栏设置点击回调函数（点击可排序）
        $('#' + _tbl_header.dom_id + ' th .sorting').click(_tbl_header.click_header);
        $('#' + _tbl_header.dom_id + ' th .sorting_asc').click(_tbl_header.click_header);
        $('#' + _tbl_header.dom_id + ' th .sorting_desc').click(_tbl_header.click_header);

        if (_.isFunction(on_created))
            on_created(_tbl_header);
        //else if (!_.isUndefined(on_created))
        else if (!_.isNull(on_created))
            console.error('create table header, on_created() is not callable.');

        cb_stack.exec();
    };

    _tbl_header.click_header = function () {
        var t = $(this).attr('data-col-key');
        _tbl_header.on_head_click(t);
    };

    // 点击表格分栏，默认操作为按此栏进行升序/降序排序
    _tbl_header.on_head_click = function (col_key) {
        var i = 0;

        if (col_key === _tbl_header.order_by) {
            if (_tbl_header.order_asc) {
                $('#' + _tbl_header.dom_id + ' th .sorting_asc').removeClass('sorting_asc').addClass('sorting_desc');
            } else {
                $('#' + _tbl_header.dom_id + ' th .sorting_desc').removeClass('sorting_desc').addClass('sorting_asc');
            }
            _tbl_header.order_asc = !_tbl_header.order_asc;
        } else {
            $('#' + _tbl_header.dom_id + ' th .sorting_asc').removeClass('sorting_asc').addClass('sorting');
            $('#' + _tbl_header.dom_id + ' th .sorting_desc').removeClass('sorting_desc').addClass('sorting');

            var sort_obj = $('#' + _tbl_header.dom_id + " [data-col-key='" + col_key + "']");
            sort_obj.removeClass('sorting').addClass('sorting_asc');

            _tbl_header.order_by = col_key;

            var order_asc = true;

            for (i = 0; i < _tbl_header._table_ctrl.column_count; ++i) {
                if (_tbl_header._table_ctrl.options.columns[i].key === col_key) {
                    order_asc = _tbl_header._table_ctrl.options.columns[i].sort_asc;
                    break;
                }
            }

            if (order_asc) {
                sort_obj.removeClass('sorting').addClass('sorting_asc');
            } else {
                sort_obj.removeClass('sorting').addClass('sorting_desc');
            }

            _tbl_header.order_asc = order_asc;
        }

        var cb_stack = CALLBACK_STACK.create();
        if (_tbl_header._table_ctrl.options.sort === 'local') {
            console.log('sort-by:', col_key);
            var data = _.sortBy(_tbl_header._table_ctrl.row_data, col_key);
            if (_tbl_header.order_asc) {
                _tbl_header._table_ctrl.set_data(cb_stack, {}, {data: data});
            } else {
                var tmp = [];
                for (i = data.length - 1; i >= 0; --i) {
                    tmp.push(data[i]);
                }
                _tbl_header._table_ctrl.set_data(cb_stack, {}, {data: tmp});
            }

        } else {
            cb_stack
                .add(_tbl_header._table_ctrl.load_data)
                .exec();
        }
    };

    return _tbl_header;
};

$tp.create_table_render = function (tbl, on_created) {
    // console.log('create_table_render', tbl, on_created);
    var _tbl_render = {};

    // _tbl_render.fs_name = function (row_id, fields) {
    //     //if(fields.type == 2) {
    //     //	return '<a href="javascript:void(0);" onclick="open_folder();"><span class="icon icon16 icon-' + fields.icon + '"></span> <span ywl-field="name">' + fields.name + '</span></a>';
    //     //}
    //     //
    //     return '<span ywl-field="icon-and-name"><span class="icon icon16 icon-' + fields.icon + '"></span> <span ywl-field="name">' + fields.name + '</span></span>';
    // };
    // _tbl_render.pl_desc = function (row_id, fields) {
    //     //if(fields.type == 2) {
    //     //	return '<a href="javascript:void(0);" onclick="open_folder();"><span class="icon icon16 icon-' + fields.icon + '"></span> <span ywl-field="name">' + fields.name + '</span></a>';
    //     //}
    //     //
    //     var _desc = '未知';
    //     if (fields.pl == 0) {
    //         _desc = '来宾';
    //     } else if (fields.pl == 1) {
    //         _desc = '普通用户';
    //     } else if (fields.pl == 2) {
    //         _desc = '管理员';
    //     }
    //     return '<span ywl-field="pl-desc">' + _desc + '</span>';
    // };

    _tbl_render.fs_size = function (row_id, fields) {
        if (fields.type === 0 || fields.type === 2)
            return '';
        return size2str(fields.size, 2);
    };

    _tbl_render.date_time = function (row_id, fields) {
        if (0 === fields.timestamp)
            return '';
        return '<span class="datetime">' + tp_format_datetime(tp_utc2local(fields.timestamp)) + '</span>';
    };

    _tbl_render.date_time_local = function (row_id, fields) {
        if (0 === fields.timestamp)
            return '';
        return '<span class="datetime">' + tp_format_datetime(fields.timestamp) + '</span>';
    };

    // _tbl_render.log_content = function (row_id, fields) {
    //     var _func = ywl_log_analysis[fields.cmd_id];
    //     var _content;
    //     if (_.isFunction(_func)) {
    //         _content = _func(fields.content);
    //     } else {
    //         _content = fields.content;
    //     }
    //     return '<span class="log-content">' + _content + '</span>';
    // };

    _tbl_render.host_id = function (row_id, fields) {
        var ret = '';
        ret = '<span class="host-id">' + fields.id + '</span>';
        ret += '<span class="host-desc">' + fields.desc + '</span>';
        return ret;
    };

//	_tbl_render.host_status = function (row_id, fields) {
//		if (fields.status == HOST_STAT_ACTIVE) {
//			switch (fields.online) {
//				case AGENT_STAT_ONLINE:
//					return '<span class="badge badge-success">在线</span>';
//				case AGENT_STAT_OFFLINE:
//					return '<span class="badge badge-danger">离线</span>';
//				default:
//					return '<span class="badge badge-warning">未知</span>';
//			}
//		} else {
//			return '<span class="badge badge-ignore">- 未使用 -</span>';
//		}
//	};

    _tbl_render.os_type = function (row_id, fields) {
        switch (fields.os_type) {
            case 1:
                return '<span class="os-icon-windows"></span>';

            case 2:
                return '<span class="os-icon-linux"></span>';
            case 201:
                return '<span class="os-icon-centos"></span>';
            case 202:
                return '<span class="os-icon-ubuntu"></span>';
            case 203:
                return '<span class="os-icon-debian"></span>';
            case 204:
                return '<span class="os-icon-redhat"></span>';

            case 3:
            case 300:
                return '<span class="os-icon-macos"></span>';

            default:
                return '<span class="os-icon-linux"></span>';
        }
    };

    _tbl_render.record_id = function (row_id, fields) {
        return '<span ywl-record-id="' + row_id + '">' + fields.r_id + '</span>';
    };

    // _tbl_render.host_group = function (row_id, fields) {
    //     if (fields.status == HOST_STAT_NOT_ACTIVE)
    //         return '-';
    //     var g = get_host_group_by_id(fields.group);
    //     if (g.id == 0)
    //         return '- 未知分组 -';
    //     else
    //         return g.group_name;
    // };

//	_tbl_render.command_info = function (row_id, fields) {
//		var command = get_command_name_by_id(fields.cmd_id);
//		if (command === null)
//			return '命令 ' + fields.cmd_id;
//		else
//			//return '<a href="#" data-toggle="tooltip" title=\"' + command.cmd_name + '\">' + command.cmd_desc + '</a>';
//			return '<span data-toggle="tooltip" title=\"' + command.cmd_name + '\">' + command.cmd_desc + '</span>';
//		//var info = command.cmd_name + ' '+ command.cmd_desc;
//		//return info;
//	};
//     _tbl_render.user_info = function (row_id, fields) {
//         var user_info = get_user_info_by_id(fields.u_id);
//         if (user_info === null)
//             return '用户名:' + fields.u_id;
//         else
//             return user_info.nickname;
//         //var info = command.cmd_name + ' '+ command.cmd_desc;
//         //return info;
//     };
// //	_tbl_render.event_type = function (row_id, fields) {
// //		var _e_id = fields.id1 + '-' + fields.id2 + '-' + fields.id3 + '-' + fields.id4;
// //		var content = '';
// //		if (_e_id == '3-1-1-100') {
// //			content = '系统性能监控';
// //			return '<a href="#"> ' + content + '</a>';
// //		} else if (_e_id == '3-1-1-107') {
// //			content = 'TCP监听白名单监控';
// //			return '<a href="#"> ' + content + '</a>';
// //		} else if (_e_id == '3-1-1-108') {
// //			content = 'UDP白名单监控';
// //			return '<a href="#"> ' + content + '</a>';
// //		} else if (_e_id == '3-1-1-109') {
// //			content = 'TCP连接白名单监控';
// //			return '<a href="#"> ' + content + '</a>';
// //		} else if (_e_id == '3-1-1-110') {
// //			content = '进程白名单监控';
// //			return '<a href="#"> ' + content + '</a>';
// //		} else if (_e_id == '3-1-1-7') {
// //			content = '系统用户监控';
// //			return '<a href="#"> ' + content + '</a>';
// //		} else {
// //			content = '未知';
// //			return '<a href="#"> ' + content + '</a>';
// //		}
// //
// //
// //		//var info = command.cmd_name + ' '+ command.cmd_desc;
// //		//return info;
// //	};
// //     _tbl_render.event_code = function (row_id, fields) {
// //         var _e_id = fields.id1 + '-' + fields.id2 + '-' + fields.id3 + '-' + fields.id4;
// //         var _e_info = get_event_code_by_id(_e_id);
// //         var _tip = '';
// //         if (_e_info === null)
// //             _tip = '未知';
// //         else
// //             _tip = _e_info.event_desc;
// //
// //         return '<a href="#" ywl-eventcode=\"' + _e_id + '\" data-toggle="tooltip" title=\"' + _tip + '\">' + _e_id + '</a>';
// //     };
// //
//     // _tbl_render.ret_code = function (row_id, fields) {
//     //     if (fields.code === 0)
//     //         return '<span class="label label-success">成功</span>';
//     //     else
//     //         var message = '失败(' + fields.code + ',' + fields.param1 + ',' + fields.param2 + ')';
//     //     return '<span class="label label-danger"  data-toggle="tooltip" title= \"' + message + '\">' + message + '</span>';
//     //     //var info = command.cmd_name + ' '+ command.cmd_desc;
//     //     //return info;
//     // };
//     //
//     // _tbl_render.memory = function (row_id, fields) {
//     //     if (fields.status == HOST_STAT_NOT_ACTIVE)
//     //         return '-';
//     //     if (0 == fields.value)
//     //         return '';
//     //     return '<span class="badge bg-normal">' + size2str(fields.value, 0) + '</span>';
//     // };
// //
//     // _tbl_render.ip = function (row_id, fields) {
//     //     if (fields.status == HOST_STAT_NOT_ACTIVE)
//     //         return '-';
//     //
//     //     var ret = '';
//     //     var _this_id = _.uniqueId('ip-list-');
//     //
//     //     if (fields.ip.length > 2) {
//     //         ret += '<div class="td-ip-show-more"><a href="javascript:;" onclick="$tp.toggle_display(\'#' + _this_id + '\');"><i class="fa fa-angle-down"></i></a></div>';
//     //     }
//     //
//     //     ret += '<div class="td-ip-list"><div class="td-ip">';
//     //
//     //     var idx, loop;
//     //     (fields.ip.length > 2) ? loop = 2 : loop = fields.ip.length;
//     //     for (idx = 0; idx < loop; ++idx) {
//     //         ret += '<div class="td-ip-item"><span>' + fields.ip[idx] + '</span>';
//     //         if (fields.ip.length > 1) {
//     //             // TODO：暂不支持调整IP列表顺序功能
//     //             //ret += '<a href="#"><i class="fa fa-arrow-circle-up fa-fw"></i></a>';
//     //         }
//     //         ret += '</div>';
//     //     }
//     //
//     //     ret += '</div>';
//     //
//     //     if (fields.ip.length > 2) {
//     //         ret += '<div id="' + _this_id + '" class="td-ip-more" style="display:none;">';
//     //         for (idx = 2; idx < fields.ip.length; ++idx) {
//     //             ret += '<div class="td-ip-item"><span>' + fields.ip[idx] + '</span>';
//     //             // TODO：暂不支持调整IP列表顺序功能
//     //             //ret += '<a href="#"><i class="fa fa-arrow-circle-up fa-fw"></i></a>';
//     //             ret += '</div>';
//     //         }
//     //         ret += '</div>';
//     //     }
//     //
//     //     return ret;
//     // };
// //
//     // _tbl_render.disk = function (row_id, fields) {
//     //     if (fields.status == HOST_STAT_NOT_ACTIVE)
//     //         return '-';
//     //
//     //     var ret = '';
//     //     $.each(fields.disk, function (i, disk_size) {
//     //         ret += '<span class="badge bg-normal">' + size2str(disk_size, 2) + '</span> ';
//     //     });
//     //     return ret;
//     // };
// //
    _tbl_render.second2str = function (row_id, fields) {
        return '<i class="far fa-clock fa-fw"></i> ' + tp_second2str(fields.seconds);
    };

    // _tbl_render.host_rate_show = function (row_id, fields) {
    //     if (fields.value >= 90) {
    //         return '<span class="badge badge-danger">' + fields.value + '</span>';
    //     } else if (fields.value >= 50) {
    //         return '<span class="badge badge-warning">' + fields.value + '</span>';
    //     } else {
    //         return '<span class="badge badge-success">' + fields.value + '</span>';
    //     }
    // };

    if (_.isFunction(on_created)) {
        on_created(_tbl_render);
    } else if (!_.isUndefined(on_created)) {
        console.error('create table render, on_created is not callable.');
    }

    return _tbl_render;
};

$tp.create_table_paging = function (tbl, dom_id, options) {
    var _tblp = {};
    _tblp._table_ctrl = tbl;
    tbl.paging_ctrl = _tblp;
    _tblp.dom_id = dom_id;
    _tblp.options = options || {};

    _tblp.record_total = 0;
    _tblp.page_total = 0;
    _tblp.page_current = 0;
    _tblp.per_page = parseInt(_tblp.options.per_page) || -1;

    if (_.isUndefined(_tblp.options['paging_selector'])) {
        _tblp.options.paging_selector = PAGING_SELECTOR;
    }

    _tblp.get_per_page = function () {
        return _tblp.per_page;
    };

    _tblp.init = function (cb_stack) {
        var _def_per_page = -1;
        var _per_page = -1;
        $.each(_tblp.options.paging_selector.selections, function (i, s) {
            if (s.name === _tblp.options.paging_selector.default_select)
                _def_per_page = s.val;
            if (s.val === _tblp.per_page)
                _per_page = s.val;
        });

        // 如果传入的per_page在给定的选择器中并不存在，那么使用选择器的默认值
        _tblp.per_page = (_per_page === -1) ? _def_per_page : _per_page;

        //------------------------------------------------
        // create DOM
        //------------------------------------------------
        var dom = [];
        dom.push('<li><i class="fa fa-list fa-fw"></i> 记录总数 <span data-field="recorder_total">0</span></li>');
        dom.push('<li>页数 <span data-field="page_current">1</span>/<span data-field="page_total">0</span></li>');
        dom.push('<li data-field="jump">跳转到第 <input data-field="jump-to-page" type="text" class="form-control form-control-sm" style="display:inline-block;width:3em;padding:1px 5px;" /> 页</li>');
        dom.push('<li>每页显示 <div class="btn-group btn-group-xs dropup pagination">');
        dom.push('<button type="button" class="btn dropdown-toggle" data-toggle="dropdown"><span data-tp-select-result>' + _tblp.per_page + '</span> <span class="caret"></span></button>');
        dom.push('<ul class="dropdown-menu dropdown-menu-right dropdown-menu-xs" style="max-height:240px;overflow-y:auto; overflow-x:hidden;">');
        $.each(_tblp.options.paging_selector.selections, function (i, p) {
            dom.push('<li><a href="javascript:;" data-tp-selector="' + p.val + '">' + p.name + '</a></li>');
        });
        dom.push('</ul></div> 条记录</li>');

        $('#' + _tblp.dom_id).append($(dom.join('')));

        // 绑定事件（输入页码跳转）
        $('#' + _tblp.dom_id + ' [data-field="jump-to-page"]').keydown(function (event) {
            if (event.which === 13) {
                var _val = parseInt($(this).val());
                if (_val === _tblp.page_current)
                    return;

                _tblp._table_ctrl.paging_jump(_val - 1);
            }
        });

        // 绑定事件（选择每页显示的记录数）
        $('#' + _tblp.dom_id + ' li a[data-tp-selector]').click(function () {
            var select = parseInt($(this).attr('data-tp-selector'));
            if (_tblp.per_page === select)
                return;
            _tblp.per_page = select;

            var name = '';
            $.each(_tblp.options.paging_selector.selections, function (i, p) {
                if (p.val === select) {
                    name = p.name;
                    return false;
                }
            });
            if (name === '')
                name = '-未知-';
            $('#' + _tblp.dom_id + ' span[data-tp-select-result]').text(name);

            // 刷新表格数据
            if (!_.isUndefined(_tblp.options.on_per_page_changed && _.isFunction(_tblp.options.on_per_page_changed)))
                _tblp.options.on_per_page_changed(select);

            _tblp._table_ctrl.load_data(CALLBACK_STACK.create(), {});
        });


        if (_.isFunction(_tblp.options.on_created)) {
            _tblp.options.on_created(_tblp);
        }

        cb_stack.exec();
    };

    _tblp.update = function (cb_stack) {
        var _total = _tblp._table_ctrl.total || 0;
        var _page_index = _tblp._table_ctrl.page_index || 0;
        var _page_total = _tblp._table_ctrl.page_total || 0;

        if (_total > 0)
            _page_index += 1;

        if (_page_total < 9) {
            $('#' + _tblp.dom_id + " [data-field='jump']").hide();
        } else {
            $('#' + _tblp.dom_id + " [data-field='jump']").show();
        }

        $('#' + _tblp.dom_id + " [data-field='recorder_total']").html(_total);
        $('#' + _tblp.dom_id + " [data-field='page_current']").html(_page_index);
        $('#' + _tblp.dom_id + " [data-field='page_total']").html(_page_total);
        $('#' + _tblp.dom_id + ' [data-field="jump-to-page"]').val(_page_index);

        _tblp.page_current = _page_index;

        cb_stack.exec();
    };

    return _tblp;
};

$tp.create_table_pagination = function (tbl, dom_id, options) {
    var _tblp = {};
    _tblp._table_ctrl = tbl;
    tbl.pagination_ctrl = _tblp;
    _tblp.dom_id = dom_id;
    _tblp.options = options || {};

    _tblp.dom = $('#' + _tblp.dom_id);

    _tblp.init = function (cb_stack) {
        cb_stack.exec();
    };

    _tblp.update = function (cb_stack) {
        var _page_index = _tblp._table_ctrl.page_index || 0;
        var _page_total = _tblp._table_ctrl.page_total || 0;

        // 如果只有一页，就没必要显示分页跳转器了。
        if (_page_total < 2) {
            _tblp.dom.hide();
            cb_stack.exec();
            return;
        }

        var node = [];

        // 分页显示规则：
        //   总页数小于等于9的，全部显示
        //   总页数大于9的，部分显示
        //      第一页  上一页  ...  x-4  x-3  x-2  x-1  x  x+1  x+2  x+3  x+4  ...  下一页  最后一页

        var _start = _page_index - 4;
        if (_start < 0)
            _start = 0;
        var _end = _start + 9;
        if (_end > _page_total)
            _end = _page_total;

        if (_page_total > 9) {
            if (_page_index === 0)
                node.push('<li class="disabled"><span><i class="fa fa-fast-backward fa-fw"></i></span></li>');
            else
                node.push('<li><a href="javascript:;" data-jump-to="0"><span><i class="fa fa-fast-backward fa-fw"></i></span></a></li>');
        }

        if (_page_index === 0)
            node.push('<li class="disabled"><span><i class="fa fa-backward fa-fw"></i></span></li>');
        else
            node.push('<li><a href="javascript:;" data-jump-to="' + (_page_index - 1) + '"><span><i class="fa fa-backward fa-fw"></i></span></a></li>');

        if (_start > 0) {
            node.push('<li class="disabled"><span><i class="fa fa-ellipsis-h fa-fw"></i></span></li>');
        }

        for (var i = _start; i < _end; ++i) {
            if (i === _page_index)
                node.push('<li class="disabled"><span><strong>' + (i + 1) + '</strong></span></li>');
            else
                node.push('<li><a href="javascript:;" data-jump-to="' + i + '">' + (i + 1) + '</a></li>');
        }

        if (_end < _page_total - 1) {
            node.push('<li class="disabled"><span><i class="fa fa-ellipsis-h fa-fw"></i></span></li>');
        }


        if (_page_index === _page_total - 1)
            node.push('<li class="disabled"><span><i class="fa fa-forward fa-fw"></i></span></li>');
        else
            node.push('<li><a href="javascript:;" data-jump-to="' + (_page_index + 1) + '"><span><i class="fa fa-forward fa-fw"></i></span></a></li>');

        if (_page_total > 9) {
            if (_page_index === _page_total - 1)
                node.push('<li class="disabled"><span><i class="fa fa-fast-forward fa-fw"></i></span></li>');
            else
                node.push('<li><a href="javascript:;" data-jump-to="' + (_page_total - 1) + '"><span><i class="fa fa-fast-forward fa-fw"></i></span></a></li>');
        }

        _tblp.dom
            .empty().show()
            .append($(node.join('')));

        // 事件绑定
        $('#' + _tblp.dom_id + " [data-jump-to]").click(function () {
            var _page_index = parseInt($(this).attr('data-jump-to'));
            _tblp._table_ctrl.paging_jump(_page_index);
        });

        cb_stack.exec();
    };

    return _tblp;
};

//==============================================================
// 过滤器
//==============================================================

$tp.create_table_filter_fixed_value = function (tbl, key_value_map) {
    var _tblf = {};
    _tblf._table_ctrl = tbl;
    _tblf.name = _.uniqueId('tbl_kv_filter_');
    _tblf.kvs = key_value_map;

    _tblf._table_ctrl.add_filter_ctrl(_tblf.name, _tblf);

    _tblf.get_filter = function () {
        return _tblf.kvs;
    };
};

$tp.create_table_header_filter_search = function (tbl, options) {
    var _tblf = {};
    _tblf._table_ctrl = tbl;
    _tblf.options = options;

    _tblf.dom_id = tbl.dom_id + '-table-header-filter-' + _tblf.options.name;//'-filter-search-group';
    _tblf.dom_obj = $('#' + _tblf.dom_id);
    _tblf.name = _tblf.options.name;//'search_user';
    _tblf.default_value = '';

    _tblf._table_ctrl.add_filter_ctrl(_tblf.name, _tblf);

    _tblf.init = function (cb_stack) {
        // 这是一个表格内嵌过滤器，因此无需在init时创建DOM对象。
        cb_stack.exec();
    };

    _tblf.get_filter = function () {
        var _ret = {};
        var _val = $('#' + _tblf.dom_id).val();
        if (_.isUndefined(_val) || _val.length === 0)
            return _ret;

        _ret[_tblf.name] = _val;
        return _ret;
    };

    _tblf.reset = function (cb_stack) {
        $('#' + _tblf.dom_id).val(_tblf.default_value);
        cb_stack.exec();
    };

    _tblf.render = function () {
        var _ret = [];
        _ret.push('<div class="search-input"><div class="input-group">');
        _ret.push('<span class="input-group-addon"><i class="fa fa-search fa-fw"></i></span>');
        _ret.push('<input id="' + _tblf.dom_id + '" type="text" class="form-control" placeholder="' + _tblf.options.place_holder + '">');
        _ret.push('</div>');

        return _ret.join('');
    };

    _tblf.on_created = function () {
        $('#' + _tblf.dom_id).keydown(function (event) {
            if (event.which === 13) {
                var _val = $(this).val();
                if (_val === _tblf.filter_value)
                    return;

                _tblf.filter_value = _val;
                _tblf._table_ctrl.load_data(CALLBACK_STACK.create(), {});
            }
        });
    };
};

$tp.create_table_filter_role = function (tbl, roles) {
    var _tblf = {};
    _tblf._table_ctrl = tbl;
    _tblf.dom_id = tbl.dom_id + '-filter-role';
    _tblf.name = 'role';
    _tblf.default_value = -1;
    _tblf.filter_value = -1;
    _tblf.roles = roles;

    _tblf._table_ctrl.add_filter_ctrl(_tblf.name, _tblf);

    _tblf.init = function (cb_stack) {
        // 这是一个表格内嵌过滤器，因此无需在init时创建DOM对象。
        cb_stack.exec();
    };

    _tblf.get_filter = function () {
        return {role: _tblf.filter_value};
    };

    _tblf.reset = function (cb_stack) {
        _tblf.filter_value = _tblf.default_value;
        var name = _tblf._id2name(_tblf.filter_value);
        $('#' + _tblf.dom_id + ' span[data-tp-select-result]').text(name);
        cb_stack.exec();
    };

    _tblf.render = function () {
        var _ret = [];
        _ret.push('<div id="' + _tblf.dom_id + '" class="btn-group search-select">');
        _ret.push('<button type="button" class="btn dropdown-toggle" data-toggle="dropdown">');
        _ret.push('<span data-tp-select-result></span> <i class="fa fa-caret-right"></i></button>');
        _ret.push('<ul class="dropdown-menu dropdown-menu-right dropdown-menu-sm">');
        _ret.push('<li><a href="javascript:;" data-tp-selector="-1"><i class="fa fa-list-ul fa-fw"></i> 所有</a></li>');
        _ret.push('<li role="separator" class="divider"></li>');
        $.each(_tblf.roles, function (i, role) {
            _ret.push('<li><a href="javascript:;" data-tp-selector="' + role.id + '"><i class="fa fa-caret-right fa-fw"></i> ' + role.name + '</a></li>');
        });
        _ret.push('<li role="separator" class="divider"></li>');
        _ret.push('<li><a href="javascript:;" data-tp-selector="0"><i class="fa fa-caret-right fa-fw"></i> 尚未设置</a></li>');
        _ret.push('</ul></div>');

        return _ret.join('');
    };

    _tblf._id2name = function (id_) {
        if (id_ === -1)
            return '所有';
        if (id_ === 0)
            return '尚未设置';
        for (var i = 0; i < _tblf.roles.length; ++i) {
            if (_tblf.roles[i].id === id_)
                return _tblf.roles[i].name;
        }
        console.error('on', _tblf.name, 'filter select, no such id.', id_);
        return '-未知-';
    };

    _tblf.on_created = function () {
        $('#' + _tblf.dom_id + ' span[data-tp-select-result]').text('所有');
        $('#' + _tblf.dom_id + ' li a[data-tp-selector]').click(function () {
            var select = parseInt($(this).attr('data-tp-selector'));
            if (_tblf.filter_value === select)
                return;
            _tblf.filter_value = select;

            var name = _tblf._id2name(select);
            $('#' + _tblf.dom_id + ' span[data-tp-select-result]').text(name);

            // 刷新数据
            _tblf._table_ctrl.load_data(CALLBACK_STACK.create(), {});
        });
    };
};

// $tp.create_table_filter_user_state = function (tbl, states, on_created) {
//     var _tblf = {};
//     _tblf._table_ctrl = tbl;
//     _tblf.dom_id = tbl.dom_id + '-filter-user-state';
//     _tblf.name = 'user_state';
//     _tblf.default_value = 0;
//     _tblf.filter_value = 0;
//     _tblf.states = states;
//
//     _tblf._table_ctrl.add_filter_ctrl(_tblf.name, _tblf);
//
//     _tblf.init = function (cb_stack, cb_args) {
//         // 这是一个表格内嵌过滤器，因此无需在init时创建DOM对象。
//         cb_stack.exec();
//     };
//
//     _tblf.get_filter = function () {
//         return {user_state: _tblf.filter_value};
//     };
//
//     _tblf.reset = function (cb_stack) {
//         _tblf.filter_value = _tblf.default_value;
//         var name = _tblf._id2name(_tblf.filter_value);
//         $('#' + _tblf.dom_id + ' span[data-tp-select-result]').text(name);
//         cb_stack.exec();
//     };
//
//     _tblf.render = function () {
//         var _ret = [];
//         _ret.push('<div id="' + _tblf.dom_id + '" class="btn-group search-select" role="group">');
//         _ret.push('<button type="button" class="btn dropdown-toggle" data-toggle="dropdown">');
//         _ret.push('<span data-tp-select-result></span> <i class="fa fa-caret-right"></i></button>');
//         _ret.push('<ul class="dropdown-menu dropdown-menu-right dropdown-menu-sm">');
//         _ret.push('<li><a href="javascript:;" data-tp-selector="0"><i class="fa fa-list-ul fa-fw"></i> 所有</a></li>');
//         _ret.push('<li role="separator" class="divider"></li>');
//         $.each(_tblf.states, function (i, state) {
//             _ret.push('<li><a href="javascript:;" data-tp-selector="' + state.id + '"><i class="fa fa-caret-right fa-fw"></i> ' + state.name + '</a></li>');
//         });
//         _ret.push('</ul></div>');
//
//         return _ret.join('');
//     };
//
//     _tblf._id2name = function (id_) {
//         if (id_ === 0)
//             return '所有';
//         for (var i = 0; i < _tblf.states.length; ++i) {
//             if (_tblf.states[i].id === id_)
//                 return _tblf.states[i].name;
//         }
//         console.error('on', _tblf.name, 'filter select, no such id.', id_);
//         return '-未知-';
//     };
//
//     _tblf.on_created = function () {
//         $('#' + _tblf.dom_id + ' span[data-tp-select-result]').text('所有');
//         $('#' + _tblf.dom_id + ' li a[data-tp-selector]').click(function () {
//             var select = parseInt($(this).attr('data-tp-selector'));
//             if (_tblf.filter_value === select)
//                 return;
//             _tblf.filter_value = select;
//
//             var name = _tblf._id2name(select);
//             // console.log(select, name);
//
//             $('#' + _tblf.dom_id + ' span[data-tp-select-result]').text(name);
//
//             // 更新表格过滤器，并刷新数据
//             // header._table_ctrl.update_filter('user_state', state);
//             _tblf._table_ctrl.load_data(CALLBACK_STACK.create(), {});
//         });
//     };
// };

$tp.create_table_header_filter_state = function (tbl, name, states, exclude_ids) {
    var _tblf = {};
    _tblf._table_ctrl = tbl;
    _tblf.dom_id = tbl.dom_id + '-header-filter-' + name;
    _tblf.name = name;
    _tblf.default_value = 0;
    _tblf.filter_value = 0;

    _tblf.states = [];
    if (exclude_ids && exclude_ids.length > 0) {
        for (var i = 0; i < states.length; ++i) {
            if (_.indexOf(exclude_ids, states[i].id) !== -1)
                continue;
            _tblf.states.push(states[i]);
        }
    } else {
        _tblf.states = states;
    }

    _tblf._table_ctrl.add_filter_ctrl(_tblf.name, _tblf);

    _tblf.init = function (cb_stack, cb_args) {
        // 这是一个表格内嵌过滤器，因此无需在init时创建DOM对象。
        cb_stack.exec();
    };

    _tblf.get_filter = function () {
        var ret = {};
        if (_tblf.default_value === _tblf.filter_value)
            return ret;
        ret[_tblf.name] = _tblf.filter_value;
        return ret;
    };

    _tblf.reset = function (cb_stack) {
        _tblf.filter_value = _tblf.default_value;
        var name = _tblf._id2name(_tblf.filter_value);
        $('#' + _tblf.dom_id + ' span[data-tp-select-result]').text(name);
        cb_stack.exec();
    };

    _tblf.render = function () {
        var _ret = [];
        _ret.push('<div id="' + _tblf.dom_id + '" class="btn-group search-select" role="group">');
        _ret.push('<button type="button" class="btn dropdown-toggle" data-toggle="dropdown">');
        _ret.push('<span data-tp-select-result></span> <i class="fa fa-caret-right"></i></button>');
        _ret.push('<ul class="dropdown-menu dropdown-menu-right dropdown-menu-sm">');
        _ret.push('<li><a href="javascript:;" data-tp-selector="0"><i class="fa fa-list-ul fa-fw"></i> 所有</a></li>');
        _ret.push('<li role="separator" class="divider"></li>');
        $.each(_tblf.states, function (i, state) {
            _ret.push('<li><a href="javascript:;" data-tp-selector="' + state.id + '"><i class="fa fa-caret-right fa-fw"></i> ' + state.name + '</a></li>');
        });
        _ret.push('</ul></div>');

        return _ret.join('');
    };

    _tblf._id2name = function (id_) {
        if (id_ === 0)
            return '所有';
        for (var i = 0; i < _tblf.states.length; ++i) {
            if (_tblf.states[i].id === id_)
                return _tblf.states[i].name;
        }
        console.error('on', _tblf.name, 'filter select, no such id.', id_);
        return '-未知-';
    };

    _tblf.on_created = function () {
        $('#' + _tblf.dom_id + ' span[data-tp-select-result]').text('所有');
        $('#' + _tblf.dom_id + ' li a[data-tp-selector]').click(function () {
            var select = parseInt($(this).attr('data-tp-selector'));
            if (_tblf.filter_value === select)
                return;
            _tblf.filter_value = select;

            var name = _tblf._id2name(select);

            $('#' + _tblf.dom_id + ' span[data-tp-select-result]').text(name);

            // 更新表格过滤器，并刷新数据
            _tblf._table_ctrl.load_data(CALLBACK_STACK.create(), {});
        });
    };
};

$tp.create_table_header_filter_dropdown = function (tbl, name, states, exclude_ids) {
    var _tblf = {};
    _tblf._table_ctrl = tbl;
    _tblf.dom_id = tbl.dom_id + '-header-filter-' + name;
    _tblf.name = name;
    _tblf.default_value = 0;
    _tblf.filter_value = 0;

    _tblf.states = [];
    if (exclude_ids && exclude_ids.length > 0) {
        for (var i = 0; i < states.length; ++i) {
            if (_.indexOf(exclude_ids, states[i].id) !== -1)
                continue;
            _tblf.states.push(states[i]);
        }
    } else {
        _tblf.states = states;
    }

    _tblf._table_ctrl.add_filter_ctrl(_tblf.name, _tblf);

    _tblf.init = function (cb_stack, cb_args) {
        // 这是一个表格内嵌过滤器，因此无需在init时创建DOM对象。
        cb_stack.exec();
    };

    _tblf.get_filter = function () {
        var ret = {};
        if (_tblf.default_value === _tblf.filter_value)
            return ret;
        ret[_tblf.name] = _tblf.filter_value;
        return ret;
    };

    _tblf.reset = function (cb_stack) {
        _tblf.filter_value = _tblf.default_value;
        var name = _tblf._id2name(_tblf.filter_value);
        $('#' + _tblf.dom_id + ' span[data-tp-select-result]').text(name);
        cb_stack.exec();
    };

    _tblf.render = function () {
        var _ret = [];
        _ret.push('<div id="' + _tblf.dom_id + '" class="btn-group search-select" role="group">');
        _ret.push('<button type="button" class="btn dropdown-toggle" data-toggle="dropdown">');
        _ret.push('<span data-tp-select-result></span> <i class="fa fa-caret-right"></i></button>');
        _ret.push('<ul class="dropdown-menu dropdown-menu-right dropdown-menu-sm">');
        _ret.push('<li><a href="javascript:;" data-tp-selector="0"><i class="fa fa-list-ul fa-fw"></i> 所有</a></li>');
        _ret.push('<li role="separator" class="divider"></li>');
        $.each(_tblf.states, function (i, state) {
            _ret.push('<li><a href="javascript:;" data-tp-selector="' + state.id + '"><i class="fa fa-caret-right fa-fw"></i> ' + state.name + '</a></li>');
        });
        _ret.push('</ul></div>');

        return _ret.join('');
    };

    _tblf._id2name = function (id_) {
        if (id_ === 0)
            return '所有';
        for (var i = 0; i < _tblf.states.length; ++i) {
            if (_tblf.states[i].id === id_)
                return _tblf.states[i].name;
        }
        console.error('on', _tblf.name, 'filter select, no such id.', id_);
        return '-未知-';
    };

    _tblf.on_created = function () {
        $('#' + _tblf.dom_id + ' span[data-tp-select-result]').text('所有');
        $('#' + _tblf.dom_id + ' li a[data-tp-selector]').click(function () {

            var select = parseInt($(this).attr('data-tp-selector'));
            if (_tblf.filter_value === select)
                return;
            _tblf.filter_value = select;

            var name = _tblf._id2name(select);

            $('#' + _tblf.dom_id + ' span[data-tp-select-result]').text(name);

            // 更新表格过滤器，并刷新数据
            _tblf._table_ctrl.load_data(CALLBACK_STACK.create(), {});
        });
    };
};

$tp.create_table_filter_group = function (tbl, name, dom_id, groups) {
    var _tblf = {};
    _tblf._table_ctrl = tbl;
    _tblf.dom_id = dom_id;
    _tblf.name = name;
    _tblf.default_value = -1;
    _tblf.filter_value = -1;
    _tblf.groups = groups;

    _tblf._table_ctrl.add_filter_ctrl(_tblf.name, _tblf);

    _tblf.init = function (cb_stack) {
        var html = [];
        html.push('<li><a href="javascript:;" data-tp-selector="-1" data-name="所有"><i class="fa fa-caret-right fa-fw"></i> 所有</a></li>');
        $.each(_tblf.groups, function (i, item) {
            html.push('<li><a href="javascript:;" data-tp-selector="' + item.id + '" data-name="' + item.name + '"><i class="fa fa-caret-right fa-fw"></i> ' + item.name + '</a></li>');
        });
        $(_tblf.dom_id + ' ul').append($(html.join('')));


        $(_tblf.dom_id + ' li a[data-tp-selector]').click(function () {
            var select = parseInt($(this).attr('data-tp-selector'));
            if (_tblf.filter_value === select)
                return;
            _tblf.filter_value = select;

            var name = _tblf._id2name(select);
            $(_tblf.dom_id + ' span[data-tp-select-result]').text(name);

            // 刷新数据
            _tblf._table_ctrl.load_data(CALLBACK_STACK.create(), {});
        });


        cb_stack.exec();
    };

    _tblf.get_filter = function () {
        var ret = {};
        ret[_tblf.name] = _tblf.filter_value;
        return ret;
    };

    _tblf._id2name = function (id_) {
        if (id_ === -1)
            return '所有';
        // if (id_ === 0)
        //     return '尚未设置';
        for (var i = 0; i < _tblf.groups.length; ++i) {
            if (_tblf.groups[i].id === id_)
                return _tblf.groups[i].name;
        }
        console.error('on', _tblf.name, 'filter select, no such id.', id_);
        return '-未知-';
    };
};

