<%!
    page_title_ = 'SSH操作记录'
%>

<%inherit file="../page_single_base.mako"/>

<%block name="extend_js_file">
</%block>

<%block name="extend_css">
    <style type="text/css">
        #err-box, #op-box, #no-op-box {
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

        .time, .cmd {
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
                <li><i class="fa fa-server"></i> <span id="page-title">${self.attr.page_title_}</span></li>
                <li class="sub-title"><span id="recorder-info"></span></li>
            </ol>
        </div>
    </div>
</%block>

<div class="page-content">
    <div id="err-box">
        <div class="alert alert-danger">
            错误，无法读取日志文件！<br/><br/>
            错误原因：<span id="err-more-info" class="bold"></span>
        </div>
    </div>
    <div id="no-op-box">
        他悄悄地来，又悄悄地走，挥一挥衣袖，没有留下任何操作~~~~
    </div>
    <div id="op-box">
        <div id="op-list"></div>
        <div class="op-msg">
            <div class="op-item bold">图例说明：</div>
            <div class="op-item"><span class="time multi">YYYY-mm-dd HH:MM:SS</span> <span class="cmd cmd-multi">此记录可能是被复制粘贴到SSH客户端的，有可能是批量执行命令，也可能是在做文本编辑，详情见录像回放。</span></div>
            <div class="op-item"><span class="time">YYYY-mm-dd HH:MM:SS</span> <span class="cmd cmd-danger">此命令可能是危险操作。</span></div>
        </div>
    </div>
</div>

<%block name="embed_js">
    <script type="text/javascript">
        "use strict";

        $app.add_options(${page_param});


        var danger_cmd = ['chmod', 'chown', 'kill', 'rm', 'su', 'sudo'];
        var info_cmd = ['exit'];

        $app.on_init = function (cb_stack, cb_args) {
            $app.dom = {
                page_title: $('#page-title')
                , rec_info: $('#recorder-info')
                , err_box: $('#err-box')
                , err_more: $('#err-more-info')
                , no_op_box: $('#no-op-box')
                , op_box: $('#op-box')
                , op_list: $('#op-list')
            };

            console.log($app.options);

            if ($app.options.code !== TPE_OK) {
                $app.dom.page_title.text('错误');
                $app.dom.rec_info.text('读取日志文件时发生错误');
                $app.dom.err_more.text(tp_error_msg($app.options.code));
                $app.dom.err_box.show();
                cb_stack.exec();
                return;
            }

            var header = $app.options.header;
            $app.dom.rec_info.html(tp_format_datetime(header.start) + ': ' + header.user_name + '@' + header.client_ip + ' 访问 ' + header.account + '@' + header.conn_ip + ':' + header.conn_port);

            var op = $app.options.op;
            if (op.length === 0) {
                $app.dom.no_op_box.show();
                cb_stack.exec();
                return;
            }


            var html = [];
            html.push('<div class="op-item bold">命令历史记录：</div>');
            for (var i = 0; i < op.length; i++) {
                var cmd_list = op[i].c.split(' ');

                var cmd_class = 'cmd';
                var time_class = 'time';

                if (op[i].f === 1) {
                    time_class += ' multi';
                    cmd_class += ' cmd-multi';
                }

                if (_.intersection(cmd_list, danger_cmd).length > 0) {
                    cmd_class += ' cmd-danger';
                } else if (_.intersection(cmd_list, info_cmd).length > 0) {
                    cmd_class += ' cmd-info';
                }

                var t = tp_format_datetime(header.start + parseInt(op[i].t / 1000));
                html.push('<div class="op-item"><span class="' + time_class + '">' + t + '</span> <span class="' + cmd_class + '">' + op[i].c + '</span></div>');
            }
            $app.dom.op_list.append(html.join(''));
            $app.dom.op_box.show();

            cb_stack.exec();
        };
    </script>
</%block>