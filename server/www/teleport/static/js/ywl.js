/*! ywl v1.0.1, (c)2015 eomsoft.net */
"use strict";

var YWL = {
	create: function () {
		var self = {};

		self.assist = null;
		self.page_options = {};

		self.add_page_options = function (options) {
			_.extend(self.page_options, options);
		};

		// 页面主入口函数，每个页面加载完成后，调用此函数来传递页面参数
		self.init = function () {
			var cb_stack = CALLBACK_STACK.create();
			cb_stack.add(self.on_init);

			if (_.isFunction(self.create_assist)) {
				self.assist = self.create_assist();
				cb_stack.add(self.assist.init, self.page_options);
			}

			if (!_.isUndefined(self.page_options.active_menu)) {
				self._sidebar_active_menu(self.page_options.active_menu);
			}

			$('#btn-logout').click(self._logout);

			cb_stack
			//.add(self.on_init)
				.add(self.assist.init, self.page_options)
				.exec();
		};

		self.on_init = function (cb_stack) {
			cb_stack.exec();
		};

		self._logout = function () {
			var cb_stack = CALLBACK_STACK.create();
			cb_stack.add(function (cb_stack, cb_args) {
				window.location.href = '/auth/logout';
			});
			self.assist.logout(cb_stack);
		};

		self.ajax_post_json = function (url, args, success, error) {
			var _args = JSON.stringify(args);
			//log.d('ywl.ajax_post_json, args=', _args);

			// 开始Ajax调用
			$.ajax({
				url: url,
				type: 'POST',
				timeout: 3000,
				data: {_xsrf: get_cookie('_xsrf'), args: _args},
				dataType: 'json',
				success: success,
				error: error
			});
		};

		self.ajax_post_json_time_out = function (url, args, time_out,success,error) {
			var _args = JSON.stringify(args);
			//log.d('ywl.ajax_post_json, args=', _args);

			// 开始Ajax调用
			$.ajax({
				url: url,
				type: 'POST',
				timeout: time_out,
				data: {_xsrf: get_cookie('_xsrf'), args: _args},
				dataType: 'json',
				success: success,
				error: error
			});
		};

		self.ajax_post_async_json = function (url, args, success, error) {
			var _args = JSON.stringify(args);
			//log.d('ywl.ajax_post_async_json, args=', _args);

			// 开始Ajax调用
			$.ajax({
				url: url,
				type: 'POST',
				timeout: 3000,
				async: false,
				data: {_xsrf: get_cookie('_xsrf'), args: _args},
				dataType: 'json',
				success: success,
				error: error
			});
		};

		self.ajax_get_json = function (url, args, success, error) {
			var _args = JSON.stringify(args);
			log.i('ywl.ajax_get_json, args=', _args);

			// 开始Ajax调用
			$.ajax({
				url: url,
				type: 'GET',
				timeout: 3000,
				data: {args: _args},
				dataType: 'json',
				success: success,
				error: error
			});
		};

		//self.ajax_get_html = function (url, args, success, error) {
		//	var _args = JSON.stringify(args);
		//	log.d('ywl.ajax_get_html, args=', _args);
		//
		//	// 开始Ajax调用
		//	$.ajax({
		//		url: url,
		//		type: 'GET',
		//		timeout: 3000,
		//		data: {args: _args},
		//		dataType: 'json',
		//		success: success,
		//		error: error
		//	});
		//};

		self._sidebar_menu_current_expand = '';
		self._sidebar_toggle_submenu = function (id_) {
			var obj = $('#sidebar_menu_' + id_);
			if (obj.hasClass('expand')) {
				obj.removeClass('expand');
				$('#sidebar_submenu_' + id_).slideUp(300);//hide('fast');
			}
			else {
				obj.addClass('expand');
				$('#sidebar_submenu_' + id_).slideDown(300);//.show('fast');
			}

			if (self._sidebar_menu_current_expand != id_) {
				if (self._sidebar_menu_current_expand.length > 0) {
					$('#sidebar_menu_' + self._sidebar_menu_current_expand).removeClass('expand');
					$('#sidebar_submenu_' + self._sidebar_menu_current_expand).slideUp(300);//.hide();
				}
			}

			self._sidebar_menu_current_expand = id_;
		};

		self._sidebar_active_menu = function (menu_) {
			if (menu_.length == 1) {
				$('#sidebar_menu_' + menu_[0] + ' a').addClass('active');
			} else if (menu_.length == 2) {
				$('#sidebar_menu_' + menu_[0]).addClass('expand');
				$('#sidebar_submenu_' + menu_[0]).show();//.slideDown(300);//.show('fast');
				self._sidebar_menu_current_expand = menu_[0];
				$('#sidebar_menu_' + menu_[0] + '_' + menu_[1] + ' a').addClass('active');
			}
		};

		self.delay_exec = function (cb_stack, cb_args) {
			var _delay_ms = cb_args.delay_ms || 500;
			setTimeout(function () {
				cb_stack.exec();
			}, _delay_ms);
		};


		return self;
	}
};

// 所有的数据、函数均放到此对象中，避免污染全局名称空间
// 只有一个全局变量ywl，可以在任意地方引用。
var ywl = YWL.create();

