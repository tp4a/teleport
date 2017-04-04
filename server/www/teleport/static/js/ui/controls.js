/*! ywl v1.0.1, (c)2015 eomsoft.net */
"use strict";

ywl.create_table = function (table_options) {
	var _tbl = {};

	// 此表格绑定的DOM对象的ID，用于JQuery的选择器
	_tbl.selector = table_options.selector;
	_tbl.options = table_options;
	_tbl.column_count = _tbl.options.columns.length;

	_tbl.row_data = [];
	_tbl.total = 0;	// 记录总数
	_tbl.page_index = 0;	// 当前页数（基数为0）
	_tbl.per_page = 25;	// 每页显示的记录数量

	// 表头
	_tbl.header_ctrl = null;
	// 关联的分页控件(一个表格只有一个分页控件)
	_tbl.paging_ctrl = null;
	// 关联的过滤器控件（一个表格可以有多个过滤器控件）
	_tbl.filter_ctrls = [];

	_tbl.render = null;//ywl.create_table_render(self, self.options.on_render_created || null);

	//=======================
	// 需要被重载的函数
	//=======================

	_tbl.on_data_loaded = function (cb_stack, cb_args) {
		cb_stack.exec();
	};

	_tbl.on_cell_created = function (row_id, col_key, obj) {
		//log.v('on_cell_created:', row_id, col_key, obj);
	};

	_tbl.init = function (cb_stack, cb_args) {
		// 表格创建完成后，加入表格的body部分，这样就可以在没有表头的情况下创建表格了
		cb_stack.add(_tbl._make_body);

		// 创建表格渲染器
		_tbl.render = ywl.create_table_render(_tbl, _tbl.on_render_created || null);

		// 根据需要创建表头并初始化
		if (_tbl.options.have_header) {
			//log.v(' ======== create header.', _tbl.options.on_header_created);
			_tbl.header_ctrl = ywl.create_table_header(_tbl, _tbl.options.on_header_created || null);
			cb_stack.add(_tbl.header_ctrl.init);
		}

		// 如果设置了分页控件的属性，那么创建分页控件并初始化
		if (_tbl.options.have_paging) {
			_tbl.paging_ctrl = ywl.create_table_paging(_tbl, _tbl.on_paging_created || null);
			cb_stack.add(_tbl.paging_ctrl.init);
		}

		// 对每一个过滤器进行初始化
		for (var i = 0, cnt = _tbl.filter_ctrls.length; i < cnt; ++i) {
			//$.each(self.filter_ctrls, function (i, f) {
			if (_.isFunction(_tbl.filter_ctrls[i].init)) {
				cb_stack.add(_tbl.filter_ctrls[i].init);
			}
		}

		// 执行初始化函数链
		cb_stack.exec();
	};

	_tbl._make_body = function (cb_stack) {
		$(_tbl.selector).append($('<tbody></tbody>'));
		cb_stack.exec();
	};

	_tbl.destroy = function (cb_stack) {
		$(_tbl.selector).empty();
		cb_stack.exec();
	};

	_tbl._fix_options = function () {
		if (!_.isUndefined(_tbl.options.column_default)) {
			for (var i = 0, cnt = _tbl.options.columns.length; i < cnt; ++i) {
				for (var k in _tbl.options.column_default) {
					if (_tbl.options.column_default.hasOwnProperty(k)) {
						if (_.isUndefined(_tbl.options.columns[i][k])) {
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
	};

	//=====================================================================
	// 关联控件相关操作
	//=====================================================================
	_tbl.append_filter_ctrl = function (filter_ctrl) {
		_tbl.filter_ctrls.push(filter_ctrl);
	};

	//=====================================================================
	// 过滤器相关操作
	//=====================================================================
	_tbl.reset_filters = function (cb_stack, cb_args) {
		for (var i = 0, cnt = _tbl.filter_ctrls.length; i < cnt; ++i) {
			if (_.isFunction(_tbl.filter_ctrls[i].reset)) {
				cb_stack.add(_tbl.filter_ctrls[i].reset);
			}
		}
		cb_stack.exec();
	};

	//=====================================================================
	// 功能
	//=====================================================================
	_tbl.load_data = function (cb_stack, cb_args) {
		//log.v('load table data.', cb_args);
		if (_tbl.paging_ctrl)
			_tbl.per_page = _tbl.paging_ctrl.get_per_page();
		else
			_tbl.per_page = 0;

		_tbl.load_begin(1500);

		var _filter = {};
		// 对每一个关联的过滤器，获取其设置
		for (var i = 0, _filter_count = _tbl.filter_ctrls.length; i < _filter_count; ++i) {
			var _f = _tbl.filter_ctrls[i].get_filter();
			//$.each(_f, function (i, v) {
			//	_filter[v.k] = v.v;
			//});
			for (var _filter_key in _f) {
				if (_f.hasOwnProperty(_filter_key))
					_filter[_filter_key] = _f[_filter_key];
			}

		}

		var _order = null;
		if (_tbl.header_ctrl) {
			_order = _tbl.header_ctrl.get_order();
		}

		var _limit = {};
		_limit.page_index = _tbl.page_index;
		_limit.per_page = _tbl.per_page;

		//log.d('when load, filter:', _filter);
		//log.d('when load, order:', _order);
		//log.d('when load, limit:', _limit);

		// 根据数据源的设定加载数据
		if (_tbl.options.data_source) {
			if (_tbl.options.data_source.type == 'none') {
				// 外部直接调用set_data()方法来设置数据，无需本控件主动获取

			} else if (_tbl.options.data_source.type == 'callback') {
				// 调用一个函数来加载数据
				//cb_stack.add(self.load_end);
				//cb_stack.add(self.set_data);
				_tbl.options.data_source.fn(cb_stack, {table: _tbl, filter: _filter, order: _order, limit: _limit});

			} else if (_tbl.options.data_source.type == 'ajax-post') {
				var _url = _tbl.options.data_source.url;
				ywl.ajax_post_json(_url, {filter: _filter, order: _order, limit: _limit},
					function (ret) {
						log.d('ajax-return:', ret);
						if (ret.code != 0) {
							ywl.notify_error('');
						} else {
							//self.total = ret.data.total;
							//self.page_index = ret.data.page_index;
							cb_stack.add(_tbl.load_end);
							_tbl.set_data(cb_stack, {}, {total: ret.data.total, page_index: ret.data.page_index, data: ret.data.data});
						}
					},
					function () {
						_tbl.show_load_failed();
					}
				);
			} else {
				log.e('table-options [data-source] type [' + _tbl.options.data_source.type + '] known.');
			}

			//return;
		} else {
			log.e('have no idea for load table data. need data_source.');
		}
	};

	_tbl._render_row = function (row_data, pos_row_id) {
		var _pos = -1;	// 0=插入到第一行，-1=插入到最后一行（默认），其他=插入到指定row_id的行之后，如果没有找到指定的行，则插入到最后
		if (!_.isUndefined(pos_row_id)) {
			_pos = pos_row_id;
		}

		var dom_obj = $(_tbl.selector + ' tbody');
		var node = '<tr';

		if (_tbl.options.row_key) {
			$.each(_tbl.options.row_key, function (ki, kv) {
				node += ' ywl-key-' + kv + '="' + row_data[kv] + '"';
			});
		}

		node += ' ywl-row-id="' + row_data.ywl_row_id + '"';
		node += '>';

		for (var i = 0, cnt = _tbl.options.columns.length; i < cnt; ++i) {
			var col = _tbl.options.columns[i];
			node += '<td';

			var _style = ' style="';
			var _have_style = false;
			if (col.cell_align != 'center') {
				_style += 'text-align:' + col.cell_align + ';';
				_have_style = true;
			}

			if (col.width) {
				_style += 'width:' + col.width + 'px;';
				_have_style = true;
			}

			if (_have_style) {
				_style += '"';
				node += _style;
			}

			node += '>';


			var k;
			if (_.isUndefined(col.render)) {
				if (_.isUndefined(col.fields) || _.isEmpty(col.fields)) {
					node += row_data[col.key];
				} else {
					var _tmp = [];
					for (k in col.fields) {
						if (col.fields.hasOwnProperty(k))
							_tmp.push(row_data[col.fields[k]]);
					}
					node += _tmp.join(' ');
				}
			} else {
				if (_.isFunction(_tbl.render[col.render])) {
					var _args = {};
					for (k in col.fields) {
						if (col.fields.hasOwnProperty(k))
							_args[k] = row_data[col.fields[k]];
					}
					node += _tbl.render[col.render](row_data.ywl_row_id, _args);
				}
			}
			node += '</td>';
		}
		node += '</tr>';

		var _tr = $(node);
		_tr.data('ywl-row-data', row_data);

		if (_pos == -1) {
			dom_obj.append(_tr);
		} else if (_pos == 0) {
			dom_obj.prepend(_tr);
		} else {
			var _pos_obj = $(dom_obj).find("[ywl-row-id='" + _pos + "']");
			if (0 == _pos_obj[0]) {
				// 没有找到指定行，则加入到最后
				dom_obj.append(_tr);
			} else {
				// 找到了指定行，则尾随其后
				_pos_obj.after(_tr);
			}
		}

		// callback for each cell.
		if (_.isFunction(_tbl.on_cell_created)) {
			var _cell_objs = $(_tbl.selector + " [ywl-row-id='" + row_data.ywl_row_id + "'] td");
			for (i = 0, cnt = _cell_objs.length; i < cnt; ++i) {
				_tbl.on_cell_created(row_data.ywl_row_id, _tbl.options.columns[i].key, $(_cell_objs[i]));
			}
		}

		if (_.isFunction(_tbl.on_row_created)) {
			var _row_obj = $(_tbl.selector + " [ywl-row-id='" + row_data.ywl_row_id + "']")[0];
			_tbl.on_row_created(row_data.ywl_row_id, $(_row_obj));
		}

	};


	_tbl._render_rows = function (row_datas, pos_row_id) {
		var _pos = -1;	// 0=插入到第一行，-1=插入到最后一行（默认），其他=插入到指定row_id的行之后，如果没有找到指定的行，则插入到最后
		if (!_.isUndefined(pos_row_id)) {
			_pos = pos_row_id;
		}

		if (!_.isArray(row_datas)) {
			row_datas = [row_datas]
		}

		var dom_obj = $(_tbl.selector + ' tbody');
		var node = [];

		var r;
		var k = null;
		//var k = 0;
		//var key_count = _tbl.options.row_key.length;
		var row_count = row_datas.length;
		for (r = 0; r < row_count; ++r) {
			node.push('<tr');

			if (_tbl.options.row_key) {
				//	$.each(_tbl.options.row_key, function (ki, kv) {
				//		node += ' ywl-key-' + kv + '="' + row_data[kv] + '"';
				//	});
				for (k in _tbl.options.row_key) {
					if (_tbl.options.row_key.hasOwnProperty(k))
						node.push(' ywl-key-' + k + '="' + row_datas[r][k] + '"');
				}
			}

			node.push(' id="row-' + row_datas[r].ywl_row_id + '"');

			node.push(' ywl-row-id="' + row_datas[r].ywl_row_id + '">');


			for (var i = 0, cnt = _tbl.options.columns.length; i < cnt; ++i) {
				var col = _tbl.options.columns[i];
				//node.push('<td');
				node.push('<td id="cell-' + row_datas[r].ywl_row_id + '-' + i + '"');

				var _style = ' style="';
				var _have_style = false;
				if (col.cell_align != 'center') {
					_style += 'text-align:' + col.cell_align + ';';
					_have_style = true;
				}

				//if (col.width) {
				//	_style += 'width:' + col.width + 'px;';
				//	_have_style = true;
				//}

				if (_have_style) {
					_style += '"';
					node.push(_style);
				}

				node.push('>');

				//node.push('<td id="cell-'+row_datas[r].ywl_row_id+'-'+i+'">');


				if (_.isUndefined(col.render)) {
					if (_.isUndefined(col.fields) || _.isEmpty(col.fields)) {
						//node += row_data[col.key];
						node.push(row_datas[r][col.key])
					} else {
						var _tmp = [];
						for (k in col.fields) {
							if (col.fields.hasOwnProperty(k))
								_tmp.push(row_datas[r][col.fields[k]]);
						}
						node.push(_tmp.join(' '));
					}
				} else {
					if (_.isFunction(_tbl.render[col.render])) {
						var _args = {};
						for (k in col.fields) {
							if (col.fields.hasOwnProperty(k))
								_args[k] = row_datas[r][col.fields[k]];
						}
						node.push(_tbl.render[col.render](row_datas[r].ywl_row_id, _args));
					}
				}
				node.push('</td>');
			}
			node.push('</tr>');
		}


		var _tr = $(node.join(''));

		if (_pos == -1) {
			dom_obj.append(_tr);
		} else if (_pos == 0) {
			dom_obj.prepend(_tr);
		} else {
			var _pos_obj = $(dom_obj).find("[ywl-row-id='" + _pos + "']");
			if (0 == _pos_obj[0]) {
				// 没有找到指定行，则加入到最后
				dom_obj.append(_tr);
			} else {
				// 找到了指定行，则尾随其后
				_pos_obj.after(_tr);
			}
		}

		//// callback for each cell.
		//if (_.isFunction(_tbl.on_cell_created)) {
		//	var _cell_objs = $(_tbl.selector + " [ywl-row-id='" + row_datas[r].ywl_row_id + "'] td");
		//	for (i = 0, cnt = _cell_objs.length; i < cnt; ++i) {
		//		_tbl.on_cell_created(row_datas[r].ywl_row_id, _tbl.options.columns[i].key, $(_cell_objs[i]));
		//	}
		//}
		//
		//if (_.isFunction(_tbl.on_row_created)) {
		//	var _row_obj = $(_tbl.selector + " [ywl-row-id='" + row_datas[r].ywl_row_id + "']")[0];
		//	_tbl.on_row_created(row_datas[r].ywl_row_id, $(_row_obj));
		//}

		var _have_cell_created = _.isFunction(_tbl.on_cell_created);
		var _have_row_created = _.isFunction(_tbl.on_row_created);

		//if (_have_cell_created || _have_row_created) {
		for (r = 0; r < row_count; ++r) {
			var _row_obj = $('#row-' + row_datas[r].ywl_row_id);
			_row_obj.data('ywl-row-data', row_datas[r]);

			if (_have_cell_created) {
				for (i = 0, cnt = _tbl.options.columns.length; i < cnt; ++i) {
					_tbl.on_cell_created(row_datas[r].ywl_row_id, _tbl.options.columns[i].key, $('#cell-' + row_datas[r].ywl_row_id + '-' + i));
				}
			}
			if (_have_row_created) {
				_tbl.on_row_created(row_datas[r].ywl_row_id, _row_obj);
			}
		}
		//}
	};

	_tbl.render_table = function (cb_stack, cb_args) {
		var dom_obj = $(_tbl.selector + ' tbody');

		if (_tbl.row_data.length == 0) {
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

		// 我们为表格的每一行数据加入我们自己的索引
		for (var i = 0, cnt = _tbl.row_data.length; i < cnt; ++i) {
			if (_.isUndefined(_tbl.row_data[i].ywl_row_id)) {
				_tbl.row_data[i].ywl_row_id = _.uniqueId();
			}

			if (_.isFunction(_tbl.on_set_row_data)) {
				_tbl.on_set_row_data(_tbl.row_data[i]);
			}
		}

		cb_stack
			.add(_tbl.on_data_loaded)
			.add(_tbl.update_paging)
			.add(_tbl.render_table)
			.exec();
	};

	_tbl.get_row = function (obj) {
		//log.v('get-row, obj=', obj);
		if (_.isElement(obj)) {
			var _tr = null;
			if ($(obj).prop('tagName') == 'TR') {
				_tr = $(obj);
			} else if ($(obj).prop('tagName') == 'TD') {
				_tr = $($(obj).parent()[0]);
			} else {
				_tr = $($(obj).parentsUntil($('tr')).parent()[0]);
			}
			return _tr.data('ywl-row-data');

		} else if (_.isString(obj)) {
			for (var i = 0, cnt = _tbl.row_data.length; i < cnt; ++i) {
				if (_tbl.row_data[i].ywl_row_id == obj) {
					return _tbl.row_data[i];
				}
			}
			return null;

		} else {
			log.e('need an element.');
			return null;
		}

	};

	_tbl.update_row = function (row_id, kv) {
		//log.v('kv', kv);
		var _row_data = $($(_tbl.selector + " [ywl-row-id='" + row_id + "']")[0]).data('ywl-row-data');
		for (var k in kv) {
			if (kv.hasOwnProperty(k)) {
				if (_.isUndefined(_row_data[k])) {
					return false;
				} else {
					_row_data[k] = kv[k];
				}
			}
		}

		// 根据columns的设置，更新界面元素
		for (var i in _tbl.options.columns) {
			if (!_tbl.options.columns.hasOwnProperty(i))
				continue;
			var col = _tbl.options.columns[i];
			for (k in kv) {
				if (!kv.hasOwnProperty(k))
					continue;

				//log.v('k:', k, 'fields:', col.fields, 'chk:', _.contains(col.fields, k));

				//if (_.contains(col.fields, k) != -1) {
				if (_.contains(col.fields, k)) {

					var _cell = $($(_tbl.selector + " [ywl-row-id='" + row_id + "'] td")[i]);

					if (col.recreate) {
						if (_.isFunction(_tbl.on_cell_created)) {
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
							_tbl.on_cell_created(row_id, col.key, _cell);
						}
					} else {
						//log.v('update-row.', col.key);
						if (_.isFunction(_tbl.on_cell_update)) {
							_tbl.on_cell_update(row_id, col.key, _cell);
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
		var _fn = fn_is_duplicated || null;
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
					if (rows[i] == _tbl.row_data[j]) {
						_is_duplicated = true;
						break;
					}
				}
			}

			if (!_is_duplicated) {
				//if(_.isUndefined(rows[i].ywl_row_id)) {
				//	rows[i].ywl_row_id = _.uniqueId();
				//}
				rows[i].ywl_row_id = _.uniqueId();
				ret_row_id.push(rows[i].ywl_row_id);

				_tbl.row_data.push(rows[i]);
				if (_.isFunction(_tbl.on_set_row_data)) {
					_tbl.on_set_row_data(rows[i]);
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
			if (_tbl.row_data[i]['ywl_row_id'] == row_id) {
				_index = i;
				break;
			}
		}

		if (_index == -1) {
			return false;
		}

		_tbl.row_data.splice(_index, 1);
		$(_tbl.selector + ' tbody [ywl-row-id="' + row_id + '"]').remove();
		//var row_dom = $(_tbl.selector + ' tbody [ywl-row-id="' + row_id + '"]');
		//row_dom.fadeOut('normal', function(){
		//	$(this).remove();
		//});
		return true;
	};

	_tbl.clear = function () {
		$(_tbl.selector + ' tbody').empty();
		_tbl.row_data = [];
		var cb_stack = CALLBACK_STACK.create();
		cb_stack
			.add(_tbl.on_data_loaded)
			.add(_tbl.update_paging)
			.exec();
		//self.render_table(cb_stack);
	};

	_tbl.reload = function () {
		_tbl.load_data(CALLBACK_STACK.create(), {});
	};

	_tbl.load_begin = function (delay_) {
		var _delay = delay_ || 1000;
		_tbl.show_loading(_delay);
	};

	_tbl.load_end = function (cb_stack) {
		if (_tbl.loading_timer != null) {
			clearTimeout(_tbl.loading_timer);
			_tbl.loading_timer = null;
		}

		cb_stack.exec();
	};

	_tbl.show_loading = function (delay_) {
		var _delay = delay_ || 0;
		if (_delay > 0) {
			if (_tbl.loading_timer == null) {
				_tbl.loading_timer = setTimeout(function () {
					_tbl.show_loading();
				}, _delay);
				return;
			}
		}

		var msg_loading = '<tr role="row"><td class="loading" colspan="' + _tbl.column_count + '"><i class="fa fa-circle-o-notch fa-spin"></i> 加载中，请稍候...</td></tr>';
		$(_tbl.selector + ' tbody').prepend($(msg_loading))
	};

	_tbl.show_load_failed = function () {
		if (_tbl.loading_timer != null) {
			clearTimeout(_tbl.loading_timer);
			_tbl.loading_timer = null;
		}

		var msg_loading = '<tr role="row"><td class="loading" colspan="' + _tbl.column_count + '"><i class="fa fa-circle-o-notch fa-fw"></i> 天啦撸！加载失败...</td></tr>';
		$(_tbl.selector + ' tbody').empty().append($(msg_loading))
	};

	_tbl.show_empty_table = function () {
		if (_tbl.loading_timer != null) {
			clearTimeout(_tbl.loading_timer);
			_tbl.loading_timer = null;
		}

		var msg_loading = '<tr role="row"><td class="loading" colspan="' + _tbl.column_count + '"><i class="fa fa-circle-o-notch fa-fw"></i> 哇哦，没有数据哦...</td></tr>';
		$(_tbl.selector + ' tbody').empty().append($(msg_loading))
	};

	_tbl.update_paging = function (cb_stack, cb_args) {
		if (_tbl.paging_ctrl) {
			_tbl.paging_ctrl.update(cb_stack, {total: _tbl.total, page_index: _tbl.page_index, per_page: _tbl.per_page});
		} else {
			cb_stack.exec();
		}
	};

	_tbl.paging_prev = function () {
		if (_tbl.page_index == 0)
			return;
		_tbl.page_index -= 1;
		_tbl.load_data(CALLBACK_STACK.create(), {});
	};
	_tbl.paging_next = function () {
		_tbl.page_index += 1;
		_tbl.load_data(CALLBACK_STACK.create(), {});
	};
	_tbl.paging_jump = function (page_index) {
		_tbl.page_index = page_index || 0;
		_tbl.load_data(CALLBACK_STACK.create(), {});
	};

	_tbl._fix_options();

	if (_.isFunction(_tbl.options.on_created)) {
		_tbl.options.on_created(_tbl);
	}

	return _tbl;
};

// TODO: to create fixed header (not scroll), see https://github.com/markmalek/Fixed-Header-Table

ywl.create_table_header = function (tbl, on_created) {
	var _tbl_header = {};

	_tbl_header.selector = tbl.selector;
	_tbl_header._table_ctrl = tbl;
	//table_ctrl.header_ctrl = self;
	_tbl_header._columns = tbl.options.columns;

	_tbl_header.order_by = '';	// 排序字段（不一定对应数据库的字段，可能需要对应转换）
	_tbl_header.order_asc = true;	// 是否以升序排列

	_tbl_header.get_order = function () {
		if (_tbl_header.order_by == '') {
			return null;
		} else {
			return {k: _tbl_header.order_by, v: _tbl_header.order_asc};
		}
	};

	_tbl_header.init = function (cb_stack, cb_args) {
		// 从cookie中取得排序规则
		_tbl_header.order_by = null
		//log.d('order_by from cookie:', _tbl_header.order_by);
		if (_tbl_header.order_by == null) {
			_tbl_header.order_by = '';
		}

		var _first_sort = '';
		var _found = false;
		$.each(_tbl_header._columns, function (i, col) {
			if (col.sort) {
				if (_first_sort == '') {
					_first_sort = col.key;
					//log.v('first_sort', col.key);
				}

				if (_tbl_header.order_by == col.key) {
					_found = true;
					return false;	// 跳出循环
				}
			}
		});

		if (!_found) {
			_tbl_header.order_by = _first_sort;
			_tbl_header.order_asc = true;
		} else {
			_tbl_header.order_asc = ywl.assist.get_cookie('order_asc');
			if (_tbl_header.order_asc == null) {
				_tbl_header.order_asc = true;
			}
		}

		//log.v('table header:', self.order_by, self.order_asc);

		// 创建表格头
		var _dom_head = '<thead></tr>';
		$.each(_tbl_header._columns, function (i, col) {
			if (col.sort) {
				_dom_head += '<th class="';
				if (_tbl_header.order_by == col.key) {
					if (_tbl_header.order_asc)
						_dom_head += 'sorting_asc';
					else
						_dom_head += 'sorting_desc';
				} else {
					_dom_head += 'sorting';
				}

				_dom_head += '" ywl-table-col-key="' + col.key + '"';
			} else {
				_dom_head += '<th';
			}

			var _style = ' style="';
			var _have_style = false;
			if (col.header_align != 'center') {
				//_dom_head += ' align="'+col.header_align+'"';
				_style += 'text-align:' + col.header_align + ';';
				_have_style = true;
			}

			if (col.width) {
				_style += 'width:' + col.width + 'px;';
				_have_style = true;
			}
			//_dom_head += ' style="width:' + col.width + 'px;"';
			//_dom_head += '><span>' + col.title + '</span></th>';

			if (_have_style) {
				_style += '"';
				_dom_head += _style;
			}

			_dom_head += ' data-key="' + col.key + '"><span>' + col.title + '</span></th>';
		});
		_dom_head += '</tr></thead>';

		//log.v('header dom-id:', self.selector);
		$(_tbl_header.selector).append($(_dom_head));

		// 为标题栏设置点击回调函数（点击可排序）
		$(_tbl_header.selector + ' th.sorting').click(_tbl_header.click_header);
		$(_tbl_header.selector + ' th.sorting_asc').click(_tbl_header.click_header);
		$(_tbl_header.selector + ' th.sorting_desc').click(_tbl_header.click_header);

		if (_.isFunction(on_created)) {
			on_created(_tbl_header);
		}

		cb_stack.exec();
	};

	_tbl_header.click_header = function () {
		var t = $(this).attr('ywl-table-col-key');
		_tbl_header.on_head_click(t);
	};

	// 点击表格分栏，默认操作为按此栏进行升序/降序排序
	_tbl_header.on_head_click = function (col_key) {
		var i = 0;

		if (col_key == _tbl_header.order_by) {
			if (_tbl_header.order_asc) {
				$(_tbl_header.selector + ' th.sorting_asc').removeClass('sorting_asc').addClass('sorting_desc');
			} else {
				$(_tbl_header.selector + ' th.sorting_desc').removeClass('sorting_desc').addClass('sorting_asc');
			}
			_tbl_header.order_asc = !_tbl_header.order_asc;
		} else {
			$(_tbl_header.selector + ' th.sorting_asc').removeClass('sorting_asc').addClass('sorting');
			$(_tbl_header.selector + ' th.sorting_desc').removeClass('sorting_desc').addClass('sorting');

			$(_tbl_header.selector + " [ywl-table-col-key='" + col_key + "']").removeClass('sorting').addClass('sorting_asc');

			_tbl_header.order_by = col_key;

			var order_asc = true;

			for (i = 0; i < _tbl_header._table_ctrl.column_count; ++i) {
				if (_tbl_header._table_ctrl.options.columns[i].key == col_key) {
					order_asc = _tbl_header._table_ctrl.options.columns[i].sort_asc;
					log.v('-----', order_asc);
					break;
				}
			}

			if (order_asc) {
				$(_tbl_header.selector + " [ywl-table-col-key='" + col_key + "']").removeClass('sorting').addClass('sorting_asc');
			} else {
				$(_tbl_header.selector + " [ywl-table-col-key='" + col_key + "']").removeClass('sorting').addClass('sorting_desc');
			}

			_tbl_header.order_asc = order_asc;
		}

		var cb_stack = CALLBACK_STACK.create();
		if (_tbl_header._table_ctrl.options.sort == 'local') {
			//cb_stack.add(ywl.assist.set_cookie, {k: 'order_by', v: _tbl_header.order_asc});

			log.v('sort-by:', col_key);
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
				//.add(ywl.assist.set_cookie, {k: 'order_by', v: _tbl_header.order_asc})
				.add(_tbl_header._table_ctrl.load_data)
				.exec();
			//ywl.assist.set_cookie(cb_stack, {k: 'order_by', v: _tbl_header.order_asc});
		}
	};

	return _tbl_header;
};

ywl.create_table_render = function (tbl, on_created) {
	var _tbl_render = {};

	_tbl_render.fs_name = function (row_id, fields) {
		//if(fields.type == 2) {
		//	return '<a href="javascript:void(0);" onclick="open_folder();"><span class="icon icon16 icon-' + fields.icon + '"></span> <span ywl-field="name">' + fields.name + '</span></a>';
		//}
		//
		return '<span ywl-field="icon-and-name"><span class="icon icon16 icon-' + fields.icon + '"></span> <span ywl-field="name">' + fields.name + '</span></span>';
	};
	_tbl_render.pl_desc = function (row_id, fields) {
		//if(fields.type == 2) {
		//	return '<a href="javascript:void(0);" onclick="open_folder();"><span class="icon icon16 icon-' + fields.icon + '"></span> <span ywl-field="name">' + fields.name + '</span></a>';
		//}
		//
		var _desc = '未知';
		if (fields.pl == 0) {
			_desc = '来宾';
		} else if (fields.pl == 1) {
			_desc = '普通用户';
		} else if (fields.pl == 2) {
			_desc = '管理员';
		}
		return '<span ywl-field="pl-desc">' + _desc + '</span>';
	};

	_tbl_render.fs_size = function (row_id, fields) {
		if (fields.type == 0 || fields.type == 2) {
			return '';
		}
		return size2str(fields.size, 2);
	};

	_tbl_render.date_time = function (row_id, fields) {
		if (0 == fields.timestamp) {
			return '';
		}

		return '<span class="datetime">' + format_datetime(utc_to_local(fields.timestamp)) + '</span>';
	};

	_tbl_render.date_time_local = function (row_id, fields) {
		if (0 == fields.timestamp) {
			return '';
		}

		return '<span class="datetime">' + format_datetime(fields.timestamp) + '</span>';
	};

	_tbl_render.log_content = function (row_id, fields) {
		var _func = ywl_log_analysis[fields.cmd_id];
		var _content = fields.content;
		if (_func != undefined) {
			_content = _func(fields.content);
		}
		return '<span class="log-content">' + _content + '</span>';
	};

	_tbl_render.host_id = function (row_id, fields) {
		var ret = '';
		ret = '<span class="host-id">' + fields.id + '</span>';
		ret += '<span class="host-desc">' + fields.desc + '</span>';
		return ret;
	};

	_tbl_render.host_status = function (row_id, fields) {
		if (fields.status == HOST_STAT_ACTIVE) {
			switch (fields.online) {
				case AGENT_STAT_ONLINE:
					return '<span class="badge badge-success">在线</span>';
				case AGENT_STAT_OFFLINE:
					return '<span class="badge badge-danger">离线</span>';
				default:
					return '<span class="badge badge-warning">未知</span>';
			}
		} else {
			return '<span class="badge badge-ignore">- 未使用 -</span>';
		}
	};

	_tbl_render.sys_type = function (row_id, fields) {
		switch (fields.sys_type) {
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

	_tbl_render.host_group = function (row_id, fields) {
		if (fields.status == HOST_STAT_NOT_ACTIVE)
			return '-';
		var g = get_host_group_by_id(fields.group);
		if (g.id == 0)
			return '- 未知分组 -';
		else
			return g.group_name;
	};

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
	_tbl_render.user_info = function (row_id, fields) {
		var user_info = get_user_info_by_id(fields.u_id);
		if (user_info === null)
			return '用户名:' + fields.u_id;
		else
			return user_info.nickname;
		//var info = command.cmd_name + ' '+ command.cmd_desc;
		//return info;
	};
//	_tbl_render.event_type = function (row_id, fields) {
//		var _e_id = fields.id1 + '-' + fields.id2 + '-' + fields.id3 + '-' + fields.id4;
//		var content = '';
//		if (_e_id == '3-1-1-100') {
//			content = '系统性能监控';
//			return '<a href="#"> ' + content + '</a>';
//		} else if (_e_id == '3-1-1-107') {
//			content = 'TCP监听白名单监控';
//			return '<a href="#"> ' + content + '</a>';
//		} else if (_e_id == '3-1-1-108') {
//			content = 'UDP白名单监控';
//			return '<a href="#"> ' + content + '</a>';
//		} else if (_e_id == '3-1-1-109') {
//			content = 'TCP连接白名单监控';
//			return '<a href="#"> ' + content + '</a>';
//		} else if (_e_id == '3-1-1-110') {
//			content = '进程白名单监控';
//			return '<a href="#"> ' + content + '</a>';
//		} else if (_e_id == '3-1-1-7') {
//			content = '系统用户监控';
//			return '<a href="#"> ' + content + '</a>';
//		} else {
//			content = '未知';
//			return '<a href="#"> ' + content + '</a>';
//		}
//
//
//		//var info = command.cmd_name + ' '+ command.cmd_desc;
//		//return info;
//	};
	_tbl_render.event_code = function (row_id, fields) {
		var _e_id = fields.id1 + '-' + fields.id2 + '-' + fields.id3 + '-' + fields.id4;
		var _e_info = get_event_code_by_id(_e_id);
		var _tip = '';
		if (_e_info === null)
			_tip = '未知';
		else
			_tip = _e_info.event_desc;

		return '<a href="#" ywl-eventcode=\"' + _e_id + '\" data-toggle="tooltip" title=\"' + _tip + '\">' + _e_id + '</a>';
	};

	_tbl_render.ret_code = function (row_id, fields) {
		if (fields.code === 0)
			return '<span class="label label-success">成功</span>';
		else
			var message = '失败(' + fields.code + ',' + fields.param1 + ',' + fields.param2 + ')';
		return '<span class="label label-danger"  data-toggle="tooltip" title= \"' + message + '\">' + message + '</span>';
		//var info = command.cmd_name + ' '+ command.cmd_desc;
		//return info;
	};
	_tbl_render.memory = function (row_id, fields) {
		if (fields.status == HOST_STAT_NOT_ACTIVE)
			return '-';
		if (0 == fields.value)
			return '';
		return '<span class="badge bg-normal">' + size2str(fields.value, 0) + '</span>';
	};

	_tbl_render.ip = function (row_id, fields) {
		if (fields.status == HOST_STAT_NOT_ACTIVE)
			return '-';

		var ret = '';
		var _this_id = _.uniqueId('ip-list-');

		if (fields.ip.length > 2) {
			ret += '<div class="td-ip-show-more"><a href="javascript:;" onclick="ywl.toggle_display(\'#' + _this_id + '\');"><i class="fa fa-angle-down"></i></a></div>';
		}

		ret += '<div class="td-ip-list"><div class="td-ip">';

		var idx, loop;
		(fields.ip.length > 2) ? loop = 2 : loop = fields.ip.length;
		for (idx = 0; idx < loop; ++idx) {
			ret += '<div class="td-ip-item"><span>' + fields.ip[idx] + '</span>';
			if (fields.ip.length > 1) {
				// TODO：暂不支持调整IP列表顺序功能
				//ret += '<a href="#"><i class="fa fa-arrow-circle-up fa-fw"></i></a>';
			}
			ret += '</div>';
		}

		ret += '</div>';

		if (fields.ip.length > 2) {
			ret += '<div id="' + _this_id + '" class="td-ip-more" style="display:none;">';
			for (idx = 2; idx < fields.ip.length; ++idx) {
				ret += '<div class="td-ip-item"><span>' + fields.ip[idx] + '</span>';
				// TODO：暂不支持调整IP列表顺序功能
				//ret += '<a href="#"><i class="fa fa-arrow-circle-up fa-fw"></i></a>';
				ret += '</div>';
			}
			ret += '</div>';
		}

		return ret;
	};

	_tbl_render.disk = function (row_id, fields) {
		if (fields.status == HOST_STAT_NOT_ACTIVE)
			return '-';

		var ret = '';
		$.each(fields.disk, function (i, disk_size) {
			ret += '<span class="badge bg-normal">' + size2str(disk_size, 2) + '</span> ';
		});
		return ret;
	};

	_tbl_render.second2str = function (row_id, fields) {
		return '<i class="fa fa-clock-o fa-fw"></i> ' + second2str(fields.seconds);
	};

	_tbl_render.host_rate_show = function (row_id, fields) {
		if (fields.value >= 90) {
			return '<span class="badge badge-danger">' + fields.value + '</span>';
		} else if (fields.value >= 50) {
			return '<span class="badge badge-warning">' + fields.value + '</span>';
		} else {
			return '<span class="badge badge-success">' + fields.value + '</span>';
		}
	};
	if (_.isFunction(on_created)) {
		on_created(_tbl_render);
	}

	return _tbl_render;
};

ywl.create_table_paging = function (tbl, on_created) {
	var _tbl_paging = {};
	_tbl_paging.selector = tbl.options.paging.selector;
	_tbl_paging.options = tbl.options.paging;

	_tbl_paging._table_ctrl = tbl;
	//self._table_ctrl.attach_paging_ctrl(self);

	_tbl_paging._per_page = -1;

	_tbl_paging.get_per_page = function () {
		return _tbl_paging._per_page;
	};

	_tbl_paging.init = function (cb_stack, cb_args) {
		_tbl_paging._per_page = -1;
		if (_tbl_paging.options.per_page.use_cookie) {
			_tbl_paging._per_page = 10|| -1;
		}

		if (_tbl_paging._per_page == -1) {
			$.each(_tbl_paging.options.per_page.selections, function (i, s) {
				if (s.name == _tbl_paging.options.per_page.default_select) {
					_tbl_paging._per_page = s.val;
					return false;
				}
			});
		}

		if (_tbl_paging._per_page == -1) {
			_tbl_paging._per_page = _tbl_paging.options.per_page.selections[0].val;
		}

		if (_.isFunction(on_created)) {
			on_created(_tbl_paging);
		}

		_tbl_paging._update_per_page(cb_stack);
	};

	_tbl_paging._update_per_page = function (cb_stack, cb_args) {
		var node = '';

		$.each(_tbl_paging.options.per_page.selections, function (i, p) {
			if (_tbl_paging._per_page == p.val)
				node += '<option selected>' + p.val + '</option>';
			else
				node += '<option>' + p.val + '</option>';
		});

		$(_tbl_paging.selector + " select").unbind('change').empty().append($(node));
		$(_tbl_paging.selector + " select").change(function () {
			var count = parseInt($(this).children('option:selected').val());
			//log.v('per page', count);

			var cb_stack = CALLBACK_STACK.create();
			cb_stack.add(_tbl_paging._table_ctrl.load_data);
			if (_tbl_paging.options.per_page.use_cookie) {
				_tbl_paging._per_page = count;
				//cb_stack.add(ywl.assist.set_cookie, {k: 'count_per_page', v: count});
			}

			cb_stack.exec();
		});

		cb_stack.exec();
	};

	_tbl_paging.update = function (cb_stack, cb_args) {
		var _total = cb_args.total || 0;
		var _page_index = cb_args.page_index || 0;
		//var _per_page = cb_args.per_page || 25;

		$(_tbl_paging.selector + " [ywl-field='recorder_total']").html(_total);
		$(_tbl_paging.selector + " [ywl-field='page_current']").html(_page_index + 1);
		// 计算总页数
		//log.v('paging: total and per-page:', _total, self._per_page);
		var _total_page = Math.ceil(_total / _tbl_paging._per_page);
		$(_tbl_paging.selector + " [ywl-field='page_total']").html(_total_page);

		//log.v('paging: page-index and total pages:', _page_index, _total_page);

		var node = [];

		// 分页显示规则：
		//   总页数小于等于9的，全部显示
		//   总页数大于9的，部分显示
		//      第一页  上一页  ...  x-4  x-3  x-2  x-1  x  x+1  x+2  x+3  x+4  ...  下一页  最后一页

		var _start = _page_index - 4;
		if (_start < 0)
			_start = 0;
		var _end = _start + 9;
		if (_end > _total_page)
			_end = _total_page;

		if (_total_page > 9) {
			if (_page_index == 0)
				node.push('<li class="disabled"><span><i class="fa fa-fast-backward fa-fw"></i></span></li>');
			else
				node.push('<li><a href="javascript:;" ywl-jump-page="0"><span><i class="fa fa-fast-backward fa-fw"></i></span></a></li>');
		}

		if (_page_index == 0)
			node.push('<li class="disabled"><span><i class="fa fa-backward fa-fw"></i></span></li>');
		else
			node.push('<li><a href="javascript:;" ywl-action="paging-prev"><span><i class="fa fa-backward fa-fw"></i></span></a></li>');

		if (_start > 0) {
			node.push('<li class="disabled"><span><i class="fa fa-ellipsis-h fa-fw"></i></span></li>');
		}

		for (var i = _start; i < _end; ++i) {
			if (i == _page_index)
				node.push('<li class="disabled"><span><strong>' + (i + 1) + '</strong></span></li>');
			else
				node.push('<li><a href="javascript:;" ywl-jump-page="' + i + '">' + (i + 1) + '</a></li>');
		}

		if (_end < _total_page - 1) {
			node.push('<li class="disabled"><span><i class="fa fa-ellipsis-h fa-fw"></i></span></li>');
		}


		if (_page_index == _total_page - 1)
			node.push('<li class="disabled"><span><i class="fa fa-forward fa-fw"></i></span></li>');
		else
			node.push('<li><a href="javascript:;" ywl-action="paging-next"><span><i class="fa fa-forward fa-fw"></i></span></a></li>');

		if (_total_page > 9) {
			if (_page_index == _total_page - 1)
				node.push('<li class="disabled"><span><i class="fa fa-fast-forward fa-fw"></i></span></li>');
			else
				node.push('<li><a href="javascript:;" ywl-jump-page="' + (_total_page - 1) + '"><span><i class="fa fa-fast-forward fa-fw"></i></span></a></li>');
		}


		$(_tbl_paging.selector + " nav ul").empty().append($(node.join('')));

		// 事件绑定
		$(_tbl_paging.selector + " [ywl-action='paging-prev']").click(_tbl_paging.paging_prev);
		$(_tbl_paging.selector + " [ywl-action='paging-next']").click(_tbl_paging.paging_next);
		$(_tbl_paging.selector + " [ywl-jump-page]").click(_tbl_paging.paging_jump);

		_tbl_paging._update_per_page(cb_stack);
	};

	// 绑定三个页面跳转函数
	_tbl_paging.paging_prev = function () {
		_tbl_paging._table_ctrl.paging_prev();
	};
	_tbl_paging.paging_next = function () {
		_tbl_paging._table_ctrl.paging_next();
	};
	_tbl_paging.paging_jump = function () {
		var _page_index = parseInt($(this).attr('ywl-jump-page'));
		_tbl_paging._table_ctrl.paging_jump(_page_index);
	};

	return _tbl_paging;
};

ywl.create_table_filter_host_group = function (tbl, selector, group_list, on_created) {
	var _tblf_hg = {};

	// 此过滤器绑定的DOM对象，用于JQuery的选择器
	_tblf_hg.selector = selector;

	// 此过滤器绑定的表格控件
	_tblf_hg._table_ctrl = tbl;
	_tblf_hg._table_ctrl.append_filter_ctrl(_tblf_hg);

	// 过滤器内容
	_tblf_hg.filter_name = 'host_group';
	_tblf_hg.filter_default = 0;
	_tblf_hg.filter_value = 0;
	_tblf_hg.group_list = group_list;

	_tblf_hg.get_filter = function () {
		var _ret = {};
		_ret[_tblf_hg.filter_name] = _tblf_hg.filter_value;
		return _ret;
		//return [{k: self.filter_name, v: self.filter_value}];
	};

	_tblf_hg.reset = function (cb_stack, cb_args) {
		if (_tblf_hg.filter_value == _tblf_hg.filter_default) {
			cb_stack.exec();
			return;
		}

		cb_stack
			.add(function (cb_stack) {
				_tblf_hg.filter_value = _tblf_hg.filter_default;
				var g = get_host_group_by_id(_tblf_hg.filter_default);
				$(_tblf_hg.selector + ' button span:first').html(g.group_name);
				cb_stack.exec();
			});
		//ywl.assist.set_cookie(cb_stack, {k: _tblf_hg.filter_name, v: _tblf_hg.filter_default});
	};

	_tblf_hg.init = function (cb_stack, cb_args) {
		var _all = {id: 0, group_name: '全部'};
		var g = _all;
		$(_tblf_hg.selector + ' button span:first').html(g.group_name);
		_tblf_hg.filter_value = g.id;

		var _groups = _tblf_hg.group_list;

		var node = '';
		node += '<li><a href="javascript:;" ywl-group-id="0">全部</a></li>';
		node += '<li role="separator" class="divider"></li>';
		$.each(_groups, function (i, g) {
			node += '<li><a href="javascript:;" ywl-group-id="' + g.id + '">' + g.group_name + '</a></li>';
		});

		$(_tblf_hg.selector + ' ul').empty().append($(node));

		// 点击事件绑定
		$(_tblf_hg.selector + ' ul [ywl-group-id]').click(_tblf_hg._on_select);

		if (_.isFunction(on_created)) {
			on_created(_tblf_hg);
		}

		cb_stack.exec();
	};

	_tblf_hg._on_select = function () {
		var gid = parseInt($(this).attr('ywl-group-id'));
		var group_name = $(this).text();
		//var _group = get_current_host_group();
        //
		//if (gid == _group.id)
		//	return;

		//var g = get_host_group_by_id(gid);
		var cb_stack = CALLBACK_STACK.create();
		cb_stack
			.add(_tblf_hg._table_ctrl.load_data)
			.add(function (cb_stack) {
				_tblf_hg.filter_value = gid;
				$(_tblf_hg.selector + ' button span:first').html(group_name);
				cb_stack.exec();
			});
		cb_stack.exec();
		//ywl.assist.set_cookie(cb_stack, {k: _tblf_hg.filter_name, v: gid});
	};

	return _tblf_hg;
};

ywl.create_table_filter_system_type = function (tbl, selector, on_created) {
	var _tblf_st = {};

	// 此表格绑定的DOM对象的ID，用于JQuery的选择器
	_tblf_st.selector = selector;
	// 此过滤器绑定的表格控件
	_tblf_st._table_ctrl = tbl;
	_tblf_st._table_ctrl.append_filter_ctrl(_tblf_st);

	// 过滤器内容
	_tblf_st.filter_name = 'host_sys_type';
	_tblf_st.filter_default = 0;
	_tblf_st.filter_value = 0;

	_tblf_st.get_filter = function () {
		var _ret = {};
		_ret[_tblf_st.filter_name] = _tblf_st.filter_value;
		return _ret;
		//return [{k: self.filter_name, v: self.filter_value}];
	};

	_tblf_st.reset = function (cb_stack, cb_args) {
		if (_tblf_st.filter_value == _tblf_st.filter_default) {
			cb_stack.exec();
			return;
		}

		cb_stack
			.add(function (cb_stack) {
				_tblf_st.filter_value = _tblf_st.filter_default;
				var g = get_system_group_by_id(_tblf_st.filter_default);
				$(_tblf_st.selector + ' button span:first').html(g.name);
				cb_stack.exec();
			});
		//ywl.assist.set_cookie(cb_stack, {k: _tblf_st.filter_name, v: _tblf_st.filter_default});
	};

	_tblf_st.init = function (cb_stack) {
		var node = '';

		$.each(system_group, function (i, g) {
			if (g.id == -1) {
				node += '<li role="separator" class="divider"></li>';
				return true;
			}
			var is_sub = g.is_sub || false;
			if (is_sub)
				node += '<li><a href="javascript:;" ywl-group-id="' + g.id + '"><i class="fa fa-angle-right fa-fw"></i> ' + g.name + '</a></li>';
			else
				node += '<li><a href="javascript:;" ywl-group-id="' + g.id + '">' + g.name + '</a></li>';
		});

		var g = get_current_system_group();
		_tblf_st.filter_value = g.id;
		$(_tblf_st.selector + ' button span:first').html(g.name);
		$(_tblf_st.selector + ' ul').empty().append($(node));

		// 点击事件绑定
		$(_tblf_st.selector + ' ul [ywl-group-id]').click(_tblf_st._on_select);

		if (_.isFunction(on_created)) {
			on_created(_tblf_st);
		}

		cb_stack.exec();
	};

	_tblf_st._on_select = function () {
		var gid = parseInt($(this).attr('ywl-group-id'));
        //
		//var _group = get_current_system_group();
		//if (gid == _group.id)
		//	return;

		var g = get_system_group_by_id(gid);

		var cb_stack = CALLBACK_STACK.create();
		cb_stack
			.add(_tblf_st._table_ctrl.load_data)
			.add(function (cb_stack) {
				_tblf_st.filter_value = gid;
				$(_tblf_st.selector + ' button span:first').html(g.name);
				cb_stack.exec();
			});
		cb_stack.exec();
		//ywl.assist.set_cookie(cb_stack, {k: _tblf_st.filter_name, v: gid});
	};

	return _tblf_st;
};

ywl.create_table_filter_search_box = function (tbl, selector, on_created) {
	var _tblf_sb = {};
	// 此过滤器绑定的DOM对象，用于JQuery的选择器
	_tblf_sb.selector = selector;

	// 此过滤器绑定的表格控件
	_tblf_sb._table_ctrl = tbl;
	_tblf_sb._table_ctrl.append_filter_ctrl(_tblf_sb);

	// 过滤器内容
	_tblf_sb.filter_name = 'search';
	_tblf_sb.filter_default = '';

	_tblf_sb.get_filter = function () {
		var _val = $(_tblf_sb.selector + " input").val();

		var _ret = {};
		_ret[_tblf_sb.filter_name] = _val;
		return _ret;

		//return [{k: self.filter_name, v: _val}];
	};

	_tblf_sb.reset = function (cb_stack, cb_args) {
		var _val = $(_tblf_sb.selector + " input").val();

		if (_val != _tblf_sb.filter_default) {
			$(_tblf_sb.selector + " input").val(_tblf_sb.filter_default);
		}

		cb_stack.exec();
	};

	_tblf_sb.init = function (cb_stack, cb_args) {
		// 绑定搜索按钮点击事件
		$(_tblf_sb.selector + " button").click(function () {
			_tblf_sb._table_ctrl.load_data(CALLBACK_STACK.create(), {});
		});
		// 绑定搜索输入框中按下回车键
		$(_tblf_sb.selector + " input").keydown(function (event) {
			if (event.which == 13) {
				_tblf_sb._table_ctrl.load_data(CALLBACK_STACK.create(), {});
			}
		});

		if (_.isFunction(on_created)) {
			on_created(_tblf_sb);
		}

		cb_stack.exec();
	};

	return _tblf_sb;
};

ywl.create_table_filter_show_online = function (tbl, selector, on_created) {
	var _tblf_so = {};
	// 此过滤器绑定的DOM对象，用于JQuery的选择器
	_tblf_so.selector = selector;

	// 此过滤器绑定的表格控件
	_tblf_so._table_ctrl = tbl;
	_tblf_so._table_ctrl.append_filter_ctrl(_tblf_so);

	// 过滤器内容
	_tblf_so.filter_name = 'show_online_host_only';
	//self.filter_default = false;
	_tblf_so.filter_value = false;

	_tblf_so.get_filter = function () {
		var _ret = {};
		_ret[_tblf_so.filter_name] = _tblf_so.filter_value;
		return _ret;
		//return [{k: self.filter_name, v: self.filter_value}];
	};

	_tblf_so.reset = function (cb_stack, cb_args) {
		// 注意，是否仅显示在线主机并不受“重置过滤器”按钮的影响，因此只需要传递调用栈即可
		cb_stack.exec();
	};

	_tblf_so.init = function (cb_stack, cb_args) {
		var _t = ywl.assist.get_cookie(_tblf_so.filter_name);
		if (_t == null)
			_tblf_so.filter_value = false;
		else
			_tblf_so.filter_value = _t;

		_tblf_so._update_button();

		$(_tblf_so.selector).click(function () {
			_tblf_so.filter_value = !_tblf_so.filter_value;

			var cb_stack = CALLBACK_STACK.create();
			cb_stack
				.add(_tblf_so._table_ctrl.load_data)
				.add(function (cb_stack) {
					_tblf_so._update_button();
					cb_stack.exec();
				});
			//cb_stack.exec();
			//ywl.assist.set_cookie(cb_stack, {k: _tblf_so.filter_name, v: _tblf_so.filter_value});
		});

		if (_.isFunction(on_created)) {
			on_created(_tblf_so);
		}

		cb_stack.exec();
	};

	_tblf_so._update_button = function () {
		if (_tblf_so.filter_value) {
			$(_tblf_so.selector).html('<i class="fa fa-circle fa-fw"></i> 显示所有主机');
		} else {
			$(_tblf_so.selector).html('<i class="fa fa-dot-circle-o fa-fw"></i> 仅显示在线主机');
		}
	};

	return _tblf_so;
};

