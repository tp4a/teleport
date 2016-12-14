/**
 * Created by ApexLiu on 2016-03-28.
 */
"use strict";


var g_login_type = 'account';
//g_reference = '${ reference }';

ywl.on_init = function (cb_stack, cb_args) {
	ywl.login_type = ywl.page_options.login_type;
	ywl.app = ywl.create_app();
	cb_stack
		.add(ywl.app.init)
		.exec();
};


ywl.create_app = function () {
	var _app = {};

	_app.dom_login_quick = null;
	_app.dom_login_account = null;

	_app.init = function (cb_stack, cb_args) {
		_app.dom_login_quick = $('#login-type-quick');
		_app.dom_login_account = $('#login-type-account');

		_app.dom_login_quick.click(function (e) {
			_app.dom_login_account.removeClass('selected');
			$(this).addClass('selected');
			$('#input-area-account').slideUp(100);
			$('#input-area-quick').slideDown(100);
		});
		_app.dom_login_account.click(function (e) {
			_app.dom_login_quick.removeClass('selected');
			$(this).addClass('selected');
			$('#input-area-quick').slideUp(100);
			$('#input-area-account').slideDown(100);
		});

		if (ywl.assist.is_logon) {
			$('#input-area-quick' + ' .quick-yes').show();
			$('#quick-username').html(ywl.assist.user_name);
			_app.dom_login_quick.trigger('click');
		} else {
			$('#input-area-quick' + ' .quick-no').show();
			_app.dom_login_account.trigger('click');
		}

		$('#btn-login-quick').click(_app.login_quick);
		$('#btn-login-account').click(_app.login_account);

		$('#captcha_image').click(function () {
			$(this).attr('src', '/auth/get-captcha?' + Math.random());
			$('#captcha').focus();
		});
		$('#username_account').keydown(function (event) {
			$('[data-toggle="popover"]').popover('hide');
			if (event.which == 13) {
				$('#password_account').focus();
			}
		});
		$('#password_account').keydown(function (event) {
			$('[data-toggle="popover"]').popover('hide');
			if (event.which == 13) {
				$('#captcha').focus();
			}
		});
		$('#username_usbkey').keydown(function (event) {
			$('[data-toggle="popover"]').popover('hide');
			if (event.which == 13) {
				$('#password_usbkey').focus();
			}
		});
		$('#password_usbkey').keydown(function (event) {
			$('[data-toggle="popover"]').popover('hide');
			if (event.which == 13) {
				$('#captcha').focus();
			}
		});
		$('#captcha').keydown(function (event) {
			$('[data-toggle="popover"]').popover('hide');
			if (event.which == 13) {
				_app.login_account();
			}
		});

		cb_stack.exec();
	};

	_app.login_quick = function () {
		if (!ywl.assist.is_logon) {
			return;
		}
		_app.do_quick_login(ywl.assist.user_id, ywl.assist.ticket);
	};

	_app.login_account = function () {
		var str_username = '';
		var str_password = '';
		var str_captcha = '';

		var dom_username = $('#username_' + ywl.login_type);
		var dom_password = $('#password_' + ywl.login_type);
		var dom_captcha = $('#captcha');

		str_username = dom_username.val();
		str_password = dom_password.val();
		str_captcha = dom_captcha.val();

		if (str_username.length == 0) {
			show_op_box('error', '缺少账号！');
			dom_username.attr('data-content', "请填写您的账号！").popover('show');
			dom_username.focus();
			return;
		}

		if (str_password.length == 0) {
			show_op_box('error', '缺少密码！');
			dom_password.attr('data-content', "请填写密码！").popover('show');
			dom_password.focus();
			return;
		}

		if (str_captcha.length != 4) {
			show_op_box('error', '验证码错误！');
			dom_captcha.attr('data-content', "验证码为4位数字和字母的组合，请重新填写！").popover('show').focus();
			return;
		}

		$('#btn_login').attr('disabled', 'disabled');
		show_op_box('wait', '<i class="fa fa-circle-o-notch fa-spin"></i> 正在进行身份认证，请稍候...');

		// 先判断一下captcha是否正确，如果不正确，拒绝登录
		$.ajax({
			type: 'GET',
			url: '/auth/verify-captcha',
			jsonp: "callback",
			//jsonpCallback:"login_ret",
			data: {captcha: str_captcha},
			dataType: 'jsonp',
			success: function (data) {
				if (data.code == 0) {
					// 验证成功
					hide_op_box();
					show_op_box('wait', '<i class="fa fa-circle-o-notch fa-spin"></i> 正在登录TELEPORT，请稍候...');
					//var ticket = data.data.ticket;
					//var user_id = data.data.user_id;
					_app.do_account_login(str_username, str_password, str_captcha);

					//_app.do_auth(ywl.login_type, str_username, str_password, str_captcha);
				}
				else {
					hide_op_box();
					show_op_box('error', '验证码错误！');
					// renew the captcha.
					//change_captcha();
					$('#captcha_image').attr('src', '/auth/get-captcha?' + Math.random());
					$('#captcha').focus().val('');
				}

				$('#btn_login').removeAttr('disabled');
			},
			error: function () {
				hide_op_box();
				show_op_box('error', '很抱歉，无法连接服务器！请稍后再试一次！');
				$('#btn_login').removeAttr('disabled');
			}
		});
	};

	_app.do_quick_login = function (uid, ticket) {
		log.v('quick');
		$.ajax({
			type: 'GET',
			url: '/auth/quick-login',
			jsonp: "callback",
			data: {uid: uid, ticket: ticket},
			dataType: 'jsonp',
			success: function (data) {
				if (data.code == 0) {
					// 验证成功
					window.location.href = ywl.page_options.reference;
				}
				else {
					hide_op_box();
					show_op_box('error', '无法登录TELEPORT！');
				}

				$('#btn_login').removeAttr('disabled');
			},
			error: function () {
				hide_op_box();
				show_op_box('error', '很抱歉，无法连接服务器！请稍后再试一次！');
				$('#btn_login').removeAttr('disabled');
			}
		});
	};


	_app.do_auth = function (login_type, username, password, captcha) {
		// 开始Ajax调用
		$.ajax({
			type: 'GET',
			url: 'http://127.0.0.1:50021/login',
			jsonp: "callback",
			data: {login_type: login_type, username: username, password: password},
			dataType: 'jsonp',
			success: function (data) {
				if (data.code == 0) {
					// 登录成功了
					hide_op_box();
					show_op_box('wait', '<i class="fa fa-circle-o-notch fa-spin"></i> 正在登录TELEPORT，请稍候...');
					var ticket = data.data.ticket;
					var user_id = data.data.user_id;
					_app.do_account_login(user_id, username, ticket, captcha);
				}
				else {
					hide_op_box();
					show_op_box('error', data.data.err_msg);
				}

				$('#btn_login').removeAttr('disabled');
			},
			error: function () {
				hide_op_box();
				show_op_box(login_type, 'error', '很抱歉，身份认证失败！请稍后再试一次！');
				$('#btn_login').removeAttr('disabled');
			}
		});
	};

	_app.do_account_login = function (username, userpwd, captcha) {

		$.ajax({
			type: 'GET',
			url: '/auth/verify-user',
			jsonp: "callback",
			data: {username: username, userpwd: userpwd, captcha: captcha},
			dataType: 'jsonp',
			success: function (data) {
				if (data.code == 0) {
					// 验证成功
					window.location.href = ywl.page_options.reference;
				}
				else {
					hide_op_box();
					show_op_box('error', '无法登录TELEPORT！');
				}

				$('#btn_login').removeAttr('disabled');
			},
			error: function () {
				hide_op_box();
				show_op_box('error', '很抱歉，无法连接服务器！请稍后再试一次！');
				$('#btn_login').removeAttr('disabled');
			}
		});
	};


	return _app;
};

function change_login_type(login_type) {
	if (login_type == g_login_type)
		return;

	$('#login_' + login_type).show('fast');
	$('#login_' + g_login_type).hide('fast');

	$('#login_type_' + login_type).addClass('selected');
	$('#login_type_' + g_login_type).removeClass('selected');

	if (login_type == 'usbkey')
		$('#btn_login').attr('disabled', 'disabled');
	else
		$('#btn_login').removeAttr('disabled');

	g_login_type = login_type;
}

function hide_op_box() {
	$('#login_message').hide();
}

function show_op_box(op_type, op_msg) {
	var obj_box = $('#login_message');

	obj_box.html(op_msg);
	obj_box.removeClass().addClass('op_box op_' + op_type);
	obj_box.show();
}
