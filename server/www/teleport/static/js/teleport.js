"use strict";

// 构造一个回调函数栈，遵循先进后出的原则进行顺序调用。
var CALLBACK_STACK = {
    create: function () {
        var self = {};

        self.cb_stack = [];

        // 加入一个函数到栈上等待被调用
        self.add = function (cb_func, cb_args) {
            if (!_.isFunction(cb_func)) {
                console.error('need callable function.');
            }
            cb_args = cb_args || {};
            self.cb_stack.push({func: cb_func, args: cb_args});

            return self; // 支持链式调用
        };

        // 加入一个函数到栈上等待被调用，但是该函数被调用前会等待指定时间（非阻塞式等待）
        self.add_delay = function (delay_ms, cb_func, cb_args) {
            // 先将要调用的函数入栈
            self.add(cb_func, cb_args);
            // 然后加一个定时器来做等待
            self.add(function (cb_stack, cb_args) {
                var _delay_ms = cb_args.delay_ms || 500;
                setTimeout(function () {
                    cb_stack.exec();
                }, _delay_ms);
            }, {delay_ms: delay_ms});

            return self; // 支持链式调用
        };

        self.exec = function (ex_args) {
            if (self.cb_stack.length > 0) {
                var cb = self.cb_stack.pop();
                var ex_ = ex_args || {};
                cb.func(self, cb.args, ex_);
            }
        };

        self.pop = function () {
            if (self.cb_stack.length === 0) {
                return null;
            } else {
                return self.cb_stack.pop();
            }
        };

        return self;
    }
};

// console.log(window.location, window.location.protocol+'://'+window.location.host);

// Teleport核心JS
var $tp = {
    web_server: window.location.protocol+'//'+window.location.host

    // Teleport页面应用对象，放置页面自身特有的属性和函数
    , app: {
        options: {}
        , on_init: function (cb_stack) {
            cb_stack.exec();
        }   // should be overwrite.
    }

    , assist_checked: null
};

$tp.init = function () {
    $app.obj_states = [
        {id: TP_STATE_NORMAL, name: '正常', style: 'success'},
        {id: TP_STATE_DISABLED, name: '禁用', style: 'danger'},
        {id: TP_STATE_LOCKED, name: '临时锁定', style: 'warning'}
    ];

    $app.user_type = [
        {id: TP_USER_TYPE_LOCAL, name: '本地用户', style: 'success'},
        {id: TP_USER_TYPE_LDAP, name: 'LDAP', style: 'warning'}
    ];

    $app.host_types = [
        {id: 1, name: '物理主机', style: 'success'},
        {id: 2, name: '虚拟主机', style: 'info'},
        {id: 3, name: '路由器', style: 'info'},
        {id: 4, name: '其它', style: 'default'}
    ];

    $app.host_os_type = [
        {id: 1, name: 'Windows', style: 'success'},
        {id: 2, name: 'Linux/Unix', style: 'info'}
        // {id: 3, name: '其它', style: 'info'}
    ];

    var cs = CALLBACK_STACK.create();


    if(!_.isUndefined($tp.assist)) {
        cs.add($tp.assist.init);
    }

    cs.add($tp.app.init);

    cs.exec();
};

$tp.logout = function () {
    window.location.href = '/auth/logout';
};

$tp.ajax_post_json = function (url, args, success, error, timeout) {
    var timeout_ = timeout || 3000;
    var _args = JSON.stringify(args);

    $.ajax({
        url: url,
        type: 'POST',
        timeout: timeout_,
        data: {_xsrf: tp_get_cookie('_xsrf'), args: _args},
        dataType: 'json',
        success: success,
        error: error
    });
};

// $app 是 $tp.app 的别名，方便使用。
var $app = $tp.app;

$app.add_options = function (options) {
    _.extend($app.options, options);
};

$app.init = function (cb_stack) {
    cb_stack.add($app.on_init);

    if (!_.isUndefined($app.sidebar_menu)) {
        cb_stack.add($app.sidebar_menu.init_active);
    }

    cb_stack.exec();
};

$app.active_menu = function (menu_id) {
    if (_.isUndefined($app._make_sidebar_menu)) {
        $app._make_sidebar_menu = function (menu_id) {
            var _menu = {};
            _menu.active_menu_id = menu_id;
            _menu.current_expand_menu_id = '';

            _menu.toggle_submenu = function (id_) {
                var obj = $('#sidebar_menu_' + id_);
                if (obj.hasClass('expand')) {
                    obj.removeClass('expand');
                    $('#sidebar_submenu_' + id_).slideUp(300);
                }
                else {
                    obj.addClass('expand');
                    $('#sidebar_submenu_' + id_).slideDown(300);
                }

                if (_menu.current_expand_menu_id !== id_) {
                    if (_menu.current_expand_menu_id.length > 0) {
                        $('#sidebar_menu_' + _menu.current_expand_menu_id).removeClass('expand');
                        $('#sidebar_submenu_' + _menu.current_expand_menu_id).slideUp(300);
                    }
                }

                _menu.current_expand_menu_id = id_;
            };

            _menu.init_active = function (cb_stack) {
                if (_menu.active_menu_id.length === 1) {
                    $('#sidebar_menu_' + _menu.active_menu_id[0]).addClass('active');
                    $('#sidebar_menu_' + _menu.active_menu_id[0] + ' a').addClass('active');
                } else if (_menu.active_menu_id.length === 2) {
                    $('#sidebar_menu_' + _menu.active_menu_id[0]).addClass('active expand');
                    $('#sidebar_menu_' + _menu.active_menu_id[0] + ' a').addClass('selected');
                    $('#sidebar_submenu_' + _menu.active_menu_id[0]).show();
                    $('#sidebar_menu_' + _menu.active_menu_id[0] + '_' + _menu.active_menu_id[1] + ' a').addClass('active');
                }
                _menu.current_expand_menu_id = _menu.active_menu_id[0];

                cb_stack.exec();
            };

            return _menu;
        };
    }

    $app.sidebar_menu = $app._make_sidebar_menu(menu_id);

    // 绑定侧边栏导航栏的退出按钮点击事件
    $('#btn-sidebar-menu-logout').click($tp.logout);

    $('#page-sidebar').mCustomScrollbar({
        axis: "y",
        theme: 'minimal'
    });
};

$app.has_sidebar = function () {
    return !_.isUndefined($app.sidebar_menu);
};

$app.page_id = function (default_value) {
    if (!$app.has_sidebar())
        return default_value;
    return $app.sidebar_menu.active_menu_id.join('_');
};

$app.load_role_list = function (cb_stack) {
    $tp.ajax_post_json('/user/get-role-list', {},
        function (ret) {
            if (ret.code === TPE_OK) {
                $app.role_list = ret.data;
            } else {
                console.error('无法获取角色列表：' + tp_error_msg(ret.code, ret.message));
            }
            cb_stack.exec();
        },
        function () {
            console.error('网络故障，无法获取角色列表！');
            cb_stack.exec();
        }
    );
};

$app.id2name = function(_list, _id) {
    if (_.isUndefined(_list)) {
        console.error('_list not loaded.');
        return undefined;
    }

    for (var i = 0; i < _list.length; ++i) {
        if (_list[i].id === _id)
            return _list[i].name;
    }

    return undefined;
};

$app.role_id2name = function (id) {
    if (_.isUndefined($app.role_list)) {
        console.error('role list not loaded, call load_role_list() first.');
        return undefined;
    }

    for (var i = 0; i < $app.role_list.length; ++i) {
        if ($app.role_list[i].id === id)
            return $app.role_list[i].name;
    }

    return undefined;
};

// 页面加载完成后，自动初始化核心JS功能。
$(function () {
    $tp.init();
});
