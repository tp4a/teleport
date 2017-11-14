<%!
    page_title_ = 'SSH操作记录'
%>

<%inherit file="../page_single_base.mako"/>

<%block name="extend_js_file">
</%block>

<%block name="extend_css">
    <style type="text/css">
        #no-op-msg {
            display: none;
            padding: 20px;
            margin: 50px;
            background-color: #fffed5;
            border-radius: 5px;
            font-size: 120%;
        }

        #op-list {
            display: none;
            padding: 20px;
            margin: 20px 10px 20px 10px;
            background-color: #ffffff;
            font-size: 14px;
            border-radius: 5px;
        }

        .op-item {
            margin-bottom: 3px;
        }

        .time, .cmd {
            font-family: Consolas, Lucida Console, Monaco, Courier, 'Courier New', monospace;
            line-height: 15px;
            padding: 0 5px;
            border-radius: 3px;
        }

        .time {
            margin-right: 15px;
            background-color: #d8d8d8;
        }

        .cmd-danger {
            background-color: #ffbba6;
            font-weight: bold;
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
    <div id="no-op-msg">
        他悄悄地来，又悄悄地走，挥一挥衣袖，没有留下任何操作~~~~
    </div>
    <div id="op-list"></div>
</div>

<%block name="embed_js">
    <script type="text/javascript">

        $app.add_options(${page_param});


        var danger_cmd = ['chmod', 'chown', 'kill', 'rm', 'su', 'sudo'];
        var info_cmd = ['exit'];

        $app.on_init = function (cb_stack, cb_args) {
            console.log($app.options);
            var header = $app.options.header;
            $('#recorder-info').html(tp_format_datetime(header.start) + ': ' + header.user_name + '@' + header.client_ip + ' 访问 ' + header.account + '@' + header.conn_ip + ':' + header.conn_port);

            if ($app.options.count === 0) {
                $('#no-op-msg').show();
            } else {
                var dom_op_list = $('#op-list');
                var html = [];
                for (var i = 0; i < $app.options.count; i++) {
                    var cmd_list = $app.options.op[i].c.split(' ');

                    var cmd_class = '';
                    if (_.intersection(cmd_list, danger_cmd).length > 0) {
                        cmd_class = ' cmd-danger';
                    } else if (_.intersection(cmd_list, info_cmd).length > 0) {
                        cmd_class = ' cmd-info';
                    }

                    html.push('<div class="op-item"><span class="time">' + $app.options.op[i].t + '</span> <span class="cmd' + cmd_class + '">' + $app.options.op[i].c + '</span></div>');
                }
                dom_op_list.append(html.join(''));
                dom_op_list.show();
            }
            cb_stack.exec();
        };
    </script>
</%block>