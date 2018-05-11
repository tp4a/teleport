<%!
    page_title_ = 'SFTP操作记录'
%>

<%inherit file="../page_single_base.mako"/>

<%block name="extend_js_file">
</%block>

<%block name="extend_css">

    <style type="text/css">
        #op-box, #no-op-box {
            display: none;
        }

        #no-op-box {
            padding: 20px;
            margin: 50px;
            background-color: #fffed5;
            border-radius: 5px;
            font-size: 120%;
        }

        #op-list, .op-msg {
            padding: 20px;
            margin: 10px;
            background-color: #ffffff;
            font-size: 13px;
            border-radius: 5px;
            box-shadow: 1px 1px 2px rgba(0, 0, 0, .2);
        }

        .op-item {
            margin: 2px 3px;
            padding: 2px 5px;
        }

        .op-item.bold {
            margin-bottom: 5px;
            margin-left: -10px;
        }

        .time, .cmd, .path {
            font-family: Consolas, Lucida Console, Monaco, Courier, 'Courier New', monospace;
            line-height: 15px;
            padding: 2px 5px;
            border-radius: 3px;
        }

        .time {
            margin-right: 15px;
            background-color: #ececec;
        }

        .time.multi, .cmd-multi {
            background-color: #fff2cb;
        }

        .path {
            margin: 0 5px 0 5px;
            background-color: #dbffff;
        }

        .cmd {
            display: inline-block;
        }

        .cmd-danger {
            background-color: #ffd2c2;
            font-weight: bold;
        }

        .cmd-danger:before {
            display: block;
            position: relative;
            width: 16px;
            float: left;
            margin-right: 3px;
            margin-top: 0;
            color: #ff533e;
            font-size: 16px;
            content: "\f06a";
            font-family: 'Font Awesome 5 Free';
            font-weight: 900;
        }

        .cmd-info {
            background-color: #b4fdb1;
        }
    </style>
</%block>

<%block name="page_header">
    <div class="container-fluid top-navbar">
        <div class="breadcrumb-container">
            <ol class="breadcrumb">
                <li><i class="fa fa-server"></i> ${self.attr.page_title_}</li>
                <li class="sub-title"><span id="recorder-info"></span></li>
            </ol>
        </div>
    </div>
</%block>

<div class="page-content">
    <div id="no-op-box">
        他悄悄地来，又悄悄地走，挥一挥衣袖，没有留下任何操作~~~~
    </div>
    <div id="op-box">
        <div id="op-list"></div>
        <div class="op-msg">
            <div class="op-item bold">图例说明：</div>
            ##             <div class="op-item"><span class="time multi">YYYY-mm-dd HH:MM:SS</span> <span class="cmd cmd-multi">此记录可能是被复制粘贴到SSH客户端的，有可能是批量执行命令，也可能是在做文本编辑，详情见录像回放。</span></div>

            <div class="op-item"><span class="time">YYYY-mm-dd HH:MM:SS</span> <span class="cmd cmd-danger">此命令可能是危险操作。</span></div>
        </div>
    </div>
</div>

<%block name="embed_js">
    <script type="text/javascript">
        "use strict";

        var SSH_FXP_OPEN = 3;
        var SSH_FXP_REMOVE = 13;
        var SSH_FXP_MKDIR = 14;
        var SSH_FXP_RMDIR = 15;
        var SSH_FXP_RENAME = 18;
        var SSH_FXP_LINK = 21;

        $app.add_options(${page_param});

        $app.on_init = function (cb_stack, cb_args) {
            $app.dom = {
                rec_info: $('#recorder-info')
                , no_op_box: $('#no-op-box')
                , op_box: $('#op-box')
                , op_list: $('#op-list')
            };

            console.log($app.options);

            var header = $app.options.header;
            $app.dom.rec_info.html(tp_format_datetime(header.start) + ': ' + header.user_name + '@' + header.client_ip + ' 访问 ' + header.account + '@' + header.conn_ip + ':' + header.conn_port);

            var op = $app.options.op;
            if (op.length === 0) {
                $app.dom.no_op_box.show();
                cb_stack.exec();
                return;
            }

            var html = [];
            html.push('<div class="op-item bold">操作历史记录：</div>');

            for (var i = 0; i < op.length; i++) {
                var t = tp_format_datetime(header.start + parseInt(op[i].t / 1000));
                html.push('<div class="op-item"><span class="time">' + t + '</span> ');

                if (op[i].c === 3) {
                    html.push('<span class="cmd">打开文件</span>');
                    html.push('<span class="path">' + op[i].p1 + '</span>');
                } else if (op[i].c === 13) {
                    html.push('<span class="cmd cmd-danger">删除文件</span>');
                    html.push('<span class="path">' + op[i].p1 + '</span>');
                } else if (op[i].c === 14) {
                    html.push('<span class="cmd">创建目录</span>');
                    html.push('<span class="path">' + op[i].p1 + '</span>');
                } else if (op[i].c === 15) {
                    html.push('<span class="cmd cmd-danger">删除目录</span>');
                    html.push('<span class="path">' + op[i].p1 + '</span>');
                } else if (op[i].c === 18) {
                    html.push('<span class="cmd cmd-info">更改名称</span>');
                    html.push('<span class="path">' + op[i].p1 + '</span>');
                    html.push(' <i class="fa fa-long-arrow-right fa-fw"></i> ');
                    html.push('<span class="path">' + op[i].p2 + '</span>');
                } else if (op[i].c === 21) {
                    html.push('<span class="cmd">创建链接</span>');
                    html.push('<span class="path">' + op[i].p2 + '</span>');
                    html.push(' <i class="fa fa-arrow-right fa-fw"></i> ');
                    html.push('<span class="path">' + op[i].p1 + '</span>');
                }

                html.push('</div>');
            }
            $app.dom.op_list.append(html.join(''));
            $app.dom.op_box.show();

            cb_stack.exec();
        };
    </script>
</%block>