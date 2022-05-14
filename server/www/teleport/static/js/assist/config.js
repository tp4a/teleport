"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        version: $('#version'),

        ssh_type: $('#ssh-type'),
        ssh_app: $('#ssh-app'),
        ssh_cmdline: $('#ssh-cmdline'),
        ssh_desc: $('#ssh-desc'),
        ssh_select_app: $('#ssh-select-app'),

        sftp_type: $('#sftp-type'),
        sftp_app: $('#sftp-app'),
        sftp_cmdline: $('#sftp-cmdline'),
        sftp_desc: $('#sftp-desc'),
        sftp_select_app: $('#sftp-select-app'),


        telnet_type: $('#telnet-type'),
        telnet_app: $('#telnet-app'),
        telnet_cmdline: $('#telnet-cmdline'),
        telnet_desc: $('#telnet-desc'),
        telnet_select_app: $('#telnet-select-app'),

        rdp_type: $('#rdp-type'),
        rdp_app: $('#rdp-app'),
        rdp_cmdline: $('#rdp-cmdline'),
        rdp_desc: $('#rdp-desc'),
        rdp_select_app: $('#rdp-select-app'),

        btn_save: $('#btn-save')
    };

    $app.cfg = null;

    $assist.register_response_handler('get_config', $app.on_assist_config_loaded);
    $assist.register_response_handler('set_config', $app.on_assist_config_saved);
    $assist.register_response_handler('select_file', $app.on_local_file_selected);

    $assist.add_next_command({
        type: ASSIST_WS_COMMAND_TYPE_REQUEST,
        method: 'get_config',
        param: {
            username: $app.options.username
        }
    });

    cb_stack
        .add($app.init_dom_event)
        .exec();
};

$app.notify_error = function (message_, title_) {
    let _title = title_ || '';
    $tp.notify_error(message_, _title);
    console.error('错误=[', _title, '] ', message_);
};

$app._on_type_change = function (cfg, dom_type, dom_app, dom_cmdline, dom_desc) {
    cfg.selected = dom_type.val();
    for (let i = 0; i < cfg.available.length; i++) {
        let item = cfg.available[i];
        if (item.name === cfg.selected) {
            dom_app.val(item.app);
            dom_cmdline.val(item.cmdline);

            let html = [];
            for (let j = 0; j < item.desc.length; j++) {
                html.push('<div class="desc"><i class="fa fa-info-circle"></i> ' + item.desc[j] + '</div>');
            }
            dom_desc.html(html.join(''));
            return;
        }
    }
    $app.notify_error('所选的配置项不存在！');
};

$app.init_dom_event = function (cb_stack) {
    $app.dom.ssh_type.change(function () {
        $app._on_type_change($app.cfg.ssh, $app.dom.ssh_type, $app.dom.ssh_app, $app.dom.ssh_cmdline, $app.dom.ssh_desc);
    });
    $app.dom.sftp_type.change(function () {
        $app._on_type_change($app.cfg.sftp, $app.dom.sftp_type, $app.dom.sftp_app, $app.dom.sftp_cmdline, $app.dom.sftp_desc);
    });
    $app.dom.telnet_type.change(function () {
        $app._on_type_change($app.cfg.telnet, $app.dom.telnet_type, $app.dom.telnet_app, $app.dom.telnet_cmdline, $app.dom.telnet_desc);
    });
    $app.dom.rdp_type.change(function () {
        $app._on_type_change($app.cfg.rdp, $app.dom.rdp_type, $app.dom.rdp_app, $app.dom.rdp_cmdline, $app.dom.rdp_desc);
    });
    $app.dom.ssh_select_app.click(function () {
        $assist.select_local_file('ssh');
    });
    $app.dom.sftp_select_app.click(function () {
        $assist.select_local_file('sftp');
    });
    $app.dom.telnet_select_app.click(function () {
        $assist.select_local_file('telnet');
    });
    $app.dom.rdp_select_app.click(function () {
        $assist.select_local_file('rdp');
    });

    $app.dom.btn_save.click(function () {
        $app.on_save();
    });

    cb_stack.exec();
};

$app._fill_config_dom = function (cfg, dom_type, dom_app, dom_cmdline) {
    dom_type.html('');
    if (!_.isUndefined(cfg)) {
        if (_.isUndefined(cfg.selected)) {
            cfg.selected = '';
        }

        if (!_.isUndefined(cfg.available) && cfg.available.length > 0) {
            let selected = '';
            let app = '';
            let cmdline = '';

            let html = [];
            for (let i = 0; i < cfg.available.length; i++) {
                let item = cfg.available[i];

                if (selected === '' || item.name === cfg.selected) {
                    selected = item.name;
                    app = item.app;
                    cmdline = item.cmdline;
                }

                html.push('<option value="' + item.name + '">' + item.display + '</option>');
            }

            dom_type.html(html.join(''));

            dom_type.val(selected);
            dom_app.val(app);
            dom_cmdline.val(cmdline);

            $(dom_type).trigger('change');
        }
    }

};

$app.on_assist_config_loaded = function (code, message, ret) {
    console.log('on_assist_config_loaded(), ', code, message, ret);
    $app.cfg = ret;

    $app._fill_config_dom($app.cfg.ssh, $app.dom.ssh_type, $app.dom.ssh_app, $app.dom.ssh_cmdline);
    $app._fill_config_dom($app.cfg.sftp, $app.dom.sftp_type, $app.dom.sftp_app, $app.dom.sftp_cmdline);
    $app._fill_config_dom($app.cfg.telnet, $app.dom.telnet_type, $app.dom.telnet_app, $app.dom.telnet_cmdline);
    $app._fill_config_dom($app.cfg.rdp, $app.dom.rdp_type, $app.dom.rdp_app, $app.dom.rdp_cmdline);
};

$app.on_assist_config_saved = function (code, message, ret) {
    console.log('on_assist_config_saved(), ', code, message, ret);
    if (code !== TPE_OK)
        $tp.notify_error(tp_error_msg(code, message));
    else
        $tp.notify_success('助手配置保存成功!');
};

$app.on_local_file_selected = function (code, message, ret) {
    console.log('on_local_file_selected(), ', code, message, ret);
    if (code !== TPE_OK) {
        $tp.notify_error(tp_error_msg(code, message));
        return;
    }

    let app_type = ret.app_type;
    $('#' + app_type + '-app').val(ret.app_path);
};

$app._read_dom_value = function (cfg, dom_app, dom_cmdline) {
    let i = 0;
    for (i = 0; i < cfg.available.length; i++) {
        let item = cfg.available[i];
        if (item.name === cfg.selected) {
            item.app = dom_app.val();
            item.cmdline = dom_cmdline.val();
            break;
        }
    }
};

$app.on_save = function () {
    if ($app.cfg === null)
        return;

    $app._read_dom_value($app.cfg.ssh, $app.dom.ssh_app, $app.dom.ssh_cmdline);
    $app._read_dom_value($app.cfg.sftp, $app.dom.sftp_app, $app.dom.sftp_cmdline);
    $app._read_dom_value($app.cfg.telnet, $app.dom.telnet_app, $app.dom.telnet_cmdline);
    $app._read_dom_value($app.cfg.rdp, $app.dom.rdp_app, $app.dom.rdp_cmdline);

    console.log('save: ', $app.cfg);

    let cmd = {
        type: ASSIST_WS_COMMAND_TYPE_REQUEST,
        method: 'set_config',
        param: $app.cfg
    }

    $assist.ws.send(JSON.stringify(cmd));

}
