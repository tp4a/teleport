"use strict";

var g_url_base = 'http://127.0.0.1:50022';

var g_cfg = null;

var dom = {
    version: $('#version'),

    ssh_type: $('#ssh-type'),
    ssh_app: $('#ssh-app'),
    ssh_cmdline: $('#ssh-cmdline'),
    ssh_desc: $('#ssh-desc'),

    sftp_type: $('#sftp-type'),
    sftp_app: $('#sftp-app'),
    sftp_cmdline: $('#sftp-cmdline'),
    sftp_desc: $('#sftp-desc'),


    telnet_type: $('#telnet-type'),
    telnet_app: $('#telnet-app'),
    telnet_cmdline: $('#telnet-cmdline'),
    telnet_desc: $('#telnet-desc'),

    rdp_type: $('#rdp-type'),
    rdp_app: $('#rdp-app'),
    rdp_cmdline: $('#rdp-cmdline'),
    rdp_desc: $('#rdp-desc'),

    btn_save: $('#btn-save')
};

function get_version() {
    $.ajax({
        type: 'GET',
        timeout: 5000,
        url: g_url_base + '/api/get_version',
        jsonp: 'callback',
        dataType: 'json',
        success: function (ret) {
            if (ret.code == 0) {
                dom.version.text('v' + ret.version);
            } else {
                alert("获取助手版本信息失败!");
            }
        },
        error: function (jqXhr, _error, _e) {
            console.log('state:', jqXhr.state());
            alert("获取助手版本信息失败!");
        }
    });
}

function get_config() {
    $.ajax({
        type: 'GET',
        timeout: 5000,
        url: g_url_base + '/api/get_config',
        jsonp: 'callback',
        dataType: 'json',
        success: function (ret) {
            if (ret.code == 0) {
                g_cfg = ret.data;
                console.log(g_cfg);
                update_dom();
            } else {
                alert("获取配置信息失败!");
            }
        },
        error: function (jqXhr, _error, _e) {
            console.log('state:', jqXhr.state());
            alert("获取配置信息失败!");
        }
    });
}

function update_dom() {
    if (_.isNull(g_cfg))
        return;

    dom.ssh_type.html('');
    if (!_.isUndefined(g_cfg.ssh)) {
        if (_.isUndefined(g_cfg.ssh.selected)) {
            g_cfg.ssh.selected = '';
        }

        if (!_.isUndefined(g_cfg.ssh.available) && g_cfg.ssh.available.length > 0) {
            var selected = '';
            var app = '';
            var cmdline = '';

            var html = [];
            for (var i = 0; i < g_cfg.ssh.available.length; i++) {
                var item = g_cfg.ssh.available[i];

                if (selected === '' || item.name === g_cfg.ssh.selected) {
                    selected = item.name;
                    app = item.app;
                    cmdline = item.cmdline;
                }

                html.push('<option value="' + item.name + '">' + item.display + '</option>');
            }

            dom.ssh_type.html(html.join(''));

            dom.ssh_type.val(selected);
            dom.ssh_app.val(app);
            dom.ssh_cmdline.val(cmdline);

            $(dom.ssh_type).trigger('change');
        }
    }

    dom.sftp_type.html('');
    if (!_.isUndefined(g_cfg.sftp)) {
        if (_.isUndefined(g_cfg.sftp.selected)) {
            g_cfg.sftp.selected = '';
        }

        if (!_.isUndefined(g_cfg.sftp.available) && g_cfg.sftp.available.length > 0) {
            var selected = '';
            var app = '';
            var cmdline = '';

            var html = [];
            for (var i = 0; i < g_cfg.sftp.available.length; i++) {
                var item = g_cfg.sftp.available[i];

                if (selected === '' || item.name === g_cfg.sftp.selected) {
                    selected = item.name;
                    app = item.app;
                    cmdline = item.cmdline;
                }

                html.push('<option value="' + item.name + '">' + item.display + '</option>');
            }

            dom.sftp_type.html(html.join(''));

            dom.sftp_type.val(selected);
            dom.sftp_app.val(app);
            dom.sftp_cmdline.val(cmdline);

            $(dom.sftp_type).trigger('change');
        }
    }


    dom.telnet_type.html('');
    if (!_.isUndefined(g_cfg.telnet)) {
        if (_.isUndefined(g_cfg.telnet.selected)) {
            g_cfg.telnet.selected = '';
        }

        if (!_.isUndefined(g_cfg.telnet.available) && g_cfg.telnet.available.length > 0) {
            var selected = '';
            var app = '';
            var cmdline = '';

            var html = [];
            for (var i = 0; i < g_cfg.telnet.available.length; i++) {
                var item = g_cfg.telnet.available[i];

                if (selected === '' || item.name === g_cfg.telnet.selected) {
                    selected = item.name;
                    app = item.app;
                    cmdline = item.cmdline;
                }

                html.push('<option value="' + item.name + '">' + item.display + '</option>');
            }

            dom.telnet_type.html(html.join(''));

            dom.telnet_type.val(selected);
            dom.telnet_app.val(app);
            dom.telnet_cmdline.val(cmdline);

            $(dom.telnet_type).trigger('change');
        }
    }


    dom.rdp_type.html('');
    if (!_.isUndefined(g_cfg.rdp)) {
        if (_.isUndefined(g_cfg.rdp.selected)) {
            g_cfg.rdp.selected = '';
        }

        if (!_.isUndefined(g_cfg.rdp.available) && g_cfg.rdp.available.length > 0) {
            var selected = '';
            var app = '';
            var cmdline = '';

            var html = [];
            for (var i = 0; i < g_cfg.rdp.available.length; i++) {
                var item = g_cfg.rdp.available[i];

                if (selected === '' || item.name === g_cfg.rdp.selected) {
                    selected = item.name;
                    app = item.app;
                    cmdline = item.cmdline;
                }

                html.push('<option value="' + item.name + '">' + item.display + '</option>');
            }

            dom.rdp_type.html(html.join(''));

            dom.rdp_type.val(selected);
            dom.rdp_app.val(app);
            dom.rdp_cmdline.val(cmdline);
            
            $(dom.rdp_type).trigger('change');
        }
    }
}

function on_save() {
    if (g_cfg === null)
        return;

    var i = 0;
    for (i = 0; i < g_cfg.ssh.available.length; i++) {
        var item = g_cfg.ssh.available[i];
        if (item.name === g_cfg.ssh.selected) {
            item.app = dom.ssh_app.val();
            item.cmdline = dom.ssh_cmdline.val();
            break;
        }
    }
    for (i = 0; i < g_cfg.sftp.available.length; i++) {
        var item = g_cfg.sftp.available[i];
        if (item.name === g_cfg.sftp.selected) {
            item.app = dom.sftp_app.val();
            item.cmdline = dom.sftp_cmdline.val();
            break;
        }
    }
//    for (i = 0; i < g_cfg.telnet.available.length; i++) {
//        var item = g_cfg.telnet.available[i];
//        if (item.name === g_cfg.telnet.selected) {
//            item.app = dom.telnet_app.val();
//            item.cmdline = dom.telnet_cmdline.val();
//            break;
//        }
//    }
    for (i = 0; i < g_cfg.rdp.available.length; i++) {
        var item = g_cfg.rdp.available[i];
        if (item.name === g_cfg.rdp.selected) {
            item.app = dom.rdp_app.val();
            item.cmdline = dom.rdp_cmdline.val();
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

var select_local_file = function (callback) {
    var data = {
        action: 1
    };
    var args_ = encodeURIComponent(JSON.stringify(data));

    $.ajax({
        type: 'GET',
        timeout: -1,
        url: g_url_base + '/api/file_action/' + args_,
        jsonp: 'callback',
        dataType: 'json',
        success: function (ret) {
            if(ret.code === 0)
                callback(0, ret.path);
        },
        error: function (jqXhr, _error, _e) {
            console.log('state:', jqXhr.state());
            callback(-1, "");
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
    get_version();

    dom.ssh_type.change(function () {
        g_cfg.ssh.selected = dom.ssh_type.val();
        for (var i = 0; i < g_cfg.ssh.available.length; i++) {
            var item = g_cfg.ssh.available[i];
            if (item.name === g_cfg.ssh.selected) {
                dom.ssh_app.val(item.app);
                dom.ssh_cmdline.val(item.cmdline);

                var html = [];
                for(var j = 0; j < item.desc.length; j++) {
                    html.push('<div class="desc"><i class="fa fa-info-circle"></i> ' + item.desc[j] + '</div>');
                }
                dom.ssh_desc.html(html.join(''));
                return;
            }
        }
        notify_error('所选的配置项不存在！');
    });

                  
    dom.sftp_type.change(function () {
        g_cfg.sftp.selected = dom.sftp_type.val();
        for (var i = 0; i < g_cfg.sftp.available.length; i++) {
            var item = g_cfg.sftp.available[i];
            if (item.name === g_cfg.sftp.selected) {
                dom.sftp_app.val(item.app);
                dom.sftp_cmdline.val(item.cmdline);

                var html = [];
                for(var j = 0; j < item.desc.length; j++) {
                    html.push('<div class="desc"><i class="fa fa-info-circle"></i> ' + item.desc[j] + '</div>');
                }
                dom.sftp_desc.html(html.join(''));
                return;
            }
        }
        notify_error('所选的配置项不存在！');
    });


    dom.telnet_type.change(function () {
        g_cfg.telnet.selected = dom.telnet_type.val();
        for (var i = 0; i < g_cfg.telnet.available.length; i++) {
            var item = g_cfg.telnet.available[i];
            if (item.name === g_cfg.telnet.selected) {
                dom.telnet_app.val(item.app);
                dom.telnet_cmdline.val(item.cmdline);

               var html = [];
               for(var j = 0; j < item.desc.length; j++) {
                    html.push('<div class="desc"><i class="fa fa-info-circle"></i> ' + item.desc[j] + '</div>');
               }
               dom.telnet_desc.html(html.join(''));
                return;
            }
        }
        notify_error('所选的配置项不存在！');
    });


    dom.rdp_type.change(function () {
        g_cfg.rdp.selected = dom.rdp_type.val();
        for (var i = 0; i < g_cfg.rdp.available.length; i++) {
            var item = g_cfg.rdp.available[i];
            if (item.name === g_cfg.rdp.selected) {
                dom.rdp_app.val(item.app);
                dom.rdp_cmdline.val(item.cmdline);

                var html = [];
                for(var j = 0; j < item.desc.length; j++) {
                    html.push('<div class="desc"><i class="fa fa-info-circle"></i> ' + item.desc[j] + '</div>');
                }
                dom.rdp_desc.html(html.join(''));
                return;
            }
        }
        notify_error('所选的配置项不存在！');
    });


    get_config();


    dom.btn_save.click(function () {
        on_save();
    });
});
