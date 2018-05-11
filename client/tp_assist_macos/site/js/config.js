"use strict";

var g_url_base = 'http://127.0.0.1:50022';

var g_cfg = null;

var dom = {
    term_type: $('#term-type'),
    term_profile: $('#term-profile'),
    rdp_type: $('#rdp-type'),
    rdp_app: $('#rdp-app'),

    btn_save: $('#btn-save')
};


var get_config = function () {
    $.ajax({
        type: 'GET',
        timeout: 5000,
        url: g_url_base + '/api/get_config',
        jsonp: 'callback',
        dataType: 'json',
        success: function (ret) {
            if (ret.code == 0) {
                g_cfg = ret.data;
                update_dom();
            } else {
                notify_error("获取配置信息失败!");
            }
        },
        error: function (jqXhr, _error, _e) {
            console.log('state:', jqXhr.state());
            notify_error("获取配置信息失败!");
        }
    });
}

function update_dom() {
    console.log('---', g_cfg);

    dom.term_type.html('');

    if (!_.isUndefined(g_cfg.term)) {
        if (_.isUndefined(g_cfg.term.selected)) {
            g_cfg.term.selected = '';
        }

        if (!_.isUndefined(g_cfg.term.available) && g_cfg.term.available.length > 0) {
            var selected = '';
            var profile = '';

            var html = [];
            for (var i = 0; i < g_cfg.term.available.length; i++) {
                var item = g_cfg.term.available[i];

                if (selected === '' || item.name === g_cfg.term.selected) {
                    selected = item.name;
                    profile = item.profile;
                }

                html.push('<option id="term-' + item.name + '" value="' + item.name + '">' + item.display + '</option>');
            }

            dom.term_type.html(html.join(''));

            dom.term_type.val(selected);
            dom.term_profile.val(profile);
        }
    }

    if (!_.isUndefined(g_cfg.rdp)) {
        if (_.isUndefined(g_cfg.rdp.selected)) {
            g_cfg.rdp.selected = '';
        }

        if (!_.isUndefined(g_cfg.rdp.available) && g_cfg.rdp.available.length > 0) {
            var selected = '';
            var app = '';

            var html = [];
            for (var i = 0; i < g_cfg.rdp.available.length; i++) {
                var item = g_cfg.rdp.available[i];

                if (selected === '' || item.name === g_cfg.rdp.selected) {
                    selected = item.name;
                    app = item.app;
                }

                html.push('<option id="rdp-' + item.name + '" value="' + item.name + '">' + item.display + '</option>');
            }

            dom.rdp_type.html(html.join(''));

            dom.rdp_type.val(selected);
            dom.rdp_app.val(app);
        }
    }
}

function on_term_change() {
    g_cfg.term.selected = dom.term_type.val();

    for (var i = 0; i < g_cfg.term.available.length; i++) {
        var item = g_cfg.term.available[i];
        if (item.name === g_cfg.term.selected) {
            dom.term_profile.val(item.profile);
            return;
        }
    }
    notify_error('所选的终端配置项并不存在！');
}

function on_rdp_change() {
    g_cfg.rdp.selected = dom.rdp_type.val();

    for (var i = 0; i < g_cfg.rdp.available.length; i++) {
        var item = g_cfg.rdp.available[i];
        if (item.name === g_cfg.rdp.selected) {
            dom.rdp_app.val(item.app);
            return;
        }
    }
    notify_error('所选的RDP配置项并不存在！');
}

function on_save() {
    if (g_cfg === null)
        return;

    for (var i = 0; i < g_cfg.term.available.length; i++) {
        var item = g_cfg.term.available[i];
        if (item.name === g_cfg.term.selected) {
            item.profile = dom.term_profile.val();
            break;
        }
    }
    for (var i = 0; i < g_cfg.rdp.available.length; i++) {
        var item = g_cfg.rdp.available[i];
        if (item.name === g_cfg.rdp.selected) {
            item.app = dom.rdp_app.val();
            break;
        }
    }

    var args_ = encodeURIComponent(JSON.stringify(g_cfg));

    $.ajax({
        type: 'GET',
        timeout: 5000,
        url: g_url_base + '/api/set_config/' + args_,
        jsonp: 'callback',
        dataType: 'json',
        success: function (ret) {
            if (ret.code == 0) {
                notify_success('设置保存成功！');
            } else {
                notify_error('设置保存失败！' + ret.code);
            }

        },
        error: function () {
            notify_error('网络故障，设置保存失败');
        }
    });
}

function notify_error(message_, title_) {
    var _title = title_ || '';
    $.gritter.add({
        class_name: 'gritter-error',
        time: 10000,
        title: '<i class="fa fa-warning fa-fw"></i> 错误：' + _title,
        text: message_
    });
    console.error('错误', _title, message_);
};

function notify_success(message_, title_) {
    var _title = title_ || null;
    if (_title !== null)
        _title = '<i class="fa fa-check-square fa-fw"></i> ' + _title;
    $.gritter.add({
        class_name: 'gritter-success',
        time: 5000,
        title: _title,
        text: message_
    });
};


$(document).ready(function () {
    get_config();

    dom.term_type.change(function () {
        on_term_change();
    });
    dom.rdp_type.change(function () {
        on_rdp_change();
    });

    dom.btn_save.click(function () {
        on_save();
    });
});
