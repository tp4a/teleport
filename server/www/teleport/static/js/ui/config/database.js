"use strict";

ywl.on_init = function (cb_stack, cb_args) {
    console.log(ywl.page_options);

    var dom = {
        info: $('#info-kv')
    };

    var html = [];

    // 版本号
    var db = ywl.page_options.db;
    if (db.type === 1) {
        html.push(ywl._make_info('数据库类型', 'SQLite'));
        html.push(ywl._make_info('数据库文件', db.file));
    } else if(db.type === 2) {
        html.push(ywl._make_info('数据库类型', 'MySQL'));
    } else {
        html.push(ywl._make_info('数据库类型', '未知类型（' + db.type + '）'));
    }

    dom.info.append(html.join(''));

//	$("#current-rdp-port").val(core.rdp.port);
//  $("#current-ssh-port").val(core.ssh.port);
//	$("#current-telnet-port").val(core.telnet.port);

    cb_stack.exec();
};

ywl._make_info = function (key, value) {
    if (_.isUndefined(value))
        value = '<span class="error">未能检测到</span>';
    return '<tr><td class="key">' + key + '：</td><td class="value">' + value + '</td></tr>';
};
