<%!
    page_title_ = 'SFTP操作记录'
%>

<%inherit file="../page_no_sidebar_base.mako"/>
<%block name="extend_js">
</%block>

<%block name="breadcrumb">
    <ol class="breadcrumb">
        <li><i class="fa fa-file-text-o"></i> ${self.attr.page_title_}</li>
        <li><span id="recorder-info"></span></li>
    </ol>
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

        .time, .cmd, .path {
            font-family: Consolas, Lucida Console, Monaco, Courier, 'Courier New', monospace;
            font-size:13px;
            line-height: 15px;
            padding: 0 5px;
            border-radius: 3px;
        }

        .time {
            margin-right: 15px;
            background-color: #d8d8d8;
        }

        .path {
            margin:0 5px 0 5px;
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

<div class="page-content">
    <div id="no-op-msg">
        他悄悄地来，又悄悄地走，挥一挥衣袖，没有留下任何操作~~~~
    </div>
    <div id="op-list"></div>
</div>

<%block name="embed_js">
    <script type="text/javascript">

        ywl.add_page_options(${page_param});

        ywl.on_init = function (cb_stack, cb_args) {

            if (ywl.page_options.count === 0) {
                $('#no-op-msg').show();
            } else {
                var header = ywl.page_options.header;
                $('#recorder-info').html(header.account + ' 于 ' + format_datetime(header.start) + ' 访问 ' + header.user_name + '@' + header.ip + ':' + header.port);

                var dom_op_list = $('#op-list');
                var html = [];
                for (var i = 0; i < ywl.page_options.count; i++) {
                    html.push('<div class="op-item"><span class="time">' + ywl.page_options.op[i].t + '</span> ');

                    if (ywl.page_options.op[i].c === '3') {
                        html.push('<span class="cmd">打开文件</span>');
                        html.push('<span class="path">' + ywl.page_options.op[i].p1 + '</span>');
                    } else if (ywl.page_options.op[i].c === '13') {
                        html.push('<span class="cmd cmd-danger">删除文件</span>');
                        html.push('<span class="path cmd-danger">' + ywl.page_options.op[i].p1 + '</span>');
                    } else if (ywl.page_options.op[i].c === '14') {
                        html.push('<span class="cmd">创建目录</span>');
                        html.push('<span class="path">' + ywl.page_options.op[i].p1 + '</span>');
                    } else if (ywl.page_options.op[i].c === '15') {
                        html.push('<span class="cmd cmd-danger">删除目录</span>');
                        html.push('<span class="path cmd-danger">' + ywl.page_options.op[i].p1 + '</span>');
                    } else if (ywl.page_options.op[i].c === '18') {
                        html.push('<span class="cmd cmd-info">更改名称</span>');
                        html.push('<span class="path cmd-info">' + ywl.page_options.op[i].p1 + '</span>');
                        html.push('<i class="fa fa-arrow-circle-right"></i>');
                        html.push('<span class="path cmd-info">' + ywl.page_options.op[i].p2 + '</span>');
                    } else if (ywl.page_options.op[i].c === '21') {
                        html.push('<span class="cmd">创建链接</span>');
                        html.push('<span class="path">' + ywl.page_options.op[i].p2 + '</span>');
                        html.push('<i class="fa fa-arrow-right"></i>');
                        html.push('<span class="path">' + ywl.page_options.op[i].p1 + '</span>');
                    }

                    html.push('</div>');
                }
                dom_op_list.append(html.join(''));
                dom_op_list.show();
            }
            cb_stack.exec();
        };
    </script>
</%block>