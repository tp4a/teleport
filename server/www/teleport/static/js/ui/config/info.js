"use strict";

ywl.on_init = function (cb_stack, cb_args) {
    console.log(ywl.page_options);

    var dom = {
        info: $('#info-kv')
    };

    var html = [];
    html.push(ywl._make_info('核心服务通讯', ywl.page_options.web.core_server_rpc));
    html.push(ywl._make_info('WEB服务通讯', ywl.page_options.core.web_server_rpc));
    html.push(ywl._make_protocol_info('RDP 端口', ywl.page_options.core.rdp));
    html.push(ywl._make_protocol_info('SSH 端口', ywl.page_options.core.ssh));
    html.push(ywl._make_protocol_info('TELNET 端口', ywl.page_options.core.telnet));
    html.push(ywl._make_info('录像文件路径', ywl.page_options.core.replay_path));

    dom.info.append(html.join(''));

//	$("#current-rdp-port").val(core.rdp.port);
//  $("#current-ssh-port").val(core.ssh.port);
//	$("#current-telnet-port").val(core.telnet.port);

    cb_stack.exec();
};

ywl._make_protocol_info = function (name, p) {
    if(_.isUndefined(p))
        return ywl._make_info(name, '未能检测到');
    // <tr><td class="key">RDP 端口：</td><td class="value">52089</td></tr>
    var key = name;
    if (!p.enable) {
        key += '（未启用）';
    }

    return ywl._make_info(key, p.port);
};

ywl._make_info = function (key, value) {
    if(_.isUndefined(value))
        value = '未能检测到';
    return '<tr><td class="key">' + key + '：</td><td class="value">' + value + '</td></tr>';
};
